from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import torch
from torch import nn


INPUT_FRAMES = 60
INPUT_LANDMARKS = 75
INPUT_COORDINATES = 3
FLAT_FEATURES = INPUT_LANDMARKS * INPUT_COORDINATES


@dataclass(frozen=True)
class ModelSpec:
    name: str
    class_count: int
    hidden_size: int = 64
    dropout: float = 0.15


def _validate_landmarks(landmarks: torch.Tensor) -> None:
    if landmarks.ndim != 4 or tuple(landmarks.shape[1:]) != (
        INPUT_FRAMES,
        INPUT_LANDMARKS,
        INPUT_COORDINATES,
    ):
        raise ValueError("landmarks must have shape [batch, 60, 75, 3]")


def _frame_mask(landmarks: torch.Tensor) -> torch.Tensor:
    return landmarks.abs().sum(dim=(2, 3)) > 0


def _masked_mean(encoded: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    weights = mask.to(encoded.dtype).unsqueeze(-1)
    return (encoded * weights).sum(dim=1) / weights.sum(dim=1).clamp_min(1.0)


class BidirectionalGruClassifier(nn.Module):
    def __init__(self, class_count: int, hidden_size: int = 64, dropout: float = 0.15) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(FLAT_FEATURES, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.encoder = nn.GRU(
            hidden_size,
            hidden_size,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, class_count),
        )

    def forward(self, landmarks: torch.Tensor) -> torch.Tensor:
        _validate_landmarks(landmarks)
        mask = _frame_mask(landmarks)
        projected = self.projection(landmarks.flatten(start_dim=2))
        encoded, _ = self.encoder(projected)
        return self.classifier(_masked_mean(encoded, mask))


class TemporalConvGruClassifier(nn.Module):
    def __init__(self, class_count: int, hidden_size: int = 64, dropout: float = 0.15) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(FLAT_FEATURES, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )
        self.temporal = nn.Sequential(
            nn.Conv1d(hidden_size, hidden_size, kernel_size=5, padding=2),
            nn.BatchNorm1d(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Conv1d(
                hidden_size,
                hidden_size,
                kernel_size=3,
                padding=2,
                dilation=2,
                groups=hidden_size,
            ),
            nn.Conv1d(hidden_size, hidden_size, kernel_size=1),
            nn.GELU(),
        )
        self.encoder = nn.GRU(
            hidden_size,
            hidden_size,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
        )
        self.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size * 2, class_count),
        )

    def forward(self, landmarks: torch.Tensor) -> torch.Tensor:
        _validate_landmarks(landmarks)
        mask = _frame_mask(landmarks)
        projected = self.projection(landmarks.flatten(start_dim=2))
        convolved = self.temporal(projected.transpose(1, 2)).transpose(1, 2)
        encoded, _ = self.encoder(convolved)
        return self.classifier(_masked_mean(encoded, mask))


class LightweightTransformerClassifier(nn.Module):
    def __init__(self, class_count: int, hidden_size: int = 64, dropout: float = 0.15) -> None:
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(FLAT_FEATURES, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
        )
        self.position = nn.Parameter(torch.zeros(1, INPUT_FRAMES, hidden_size))
        nn.init.trunc_normal_(self.position, std=0.02)
        layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=4,
            dim_feedforward=hidden_size * 2,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=False,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=2)
        self.classifier = nn.Sequential(
            nn.LayerNorm(hidden_size),
            nn.Dropout(dropout),
            nn.Linear(hidden_size, class_count),
        )

    def forward(self, landmarks: torch.Tensor) -> torch.Tensor:
        _validate_landmarks(landmarks)
        mask = _frame_mask(landmarks)
        first_frame = (
            torch.arange(INPUT_FRAMES, device=mask.device).eq(0).unsqueeze(0)
        )
        safe_mask = mask | ((~mask.any(dim=1, keepdim=True)) & first_frame)
        projected = self.projection(landmarks.flatten(start_dim=2)) + self.position
        encoded = self.encoder(projected, src_key_padding_mask=~safe_mask)
        return self.classifier(_masked_mean(encoded, safe_mask))


def build_model(spec: ModelSpec) -> nn.Module:
    constructors: dict[str, Any] = {
        "bidirectional_gru": BidirectionalGruClassifier,
        "temporal_conv_gru": TemporalConvGruClassifier,
        "lightweight_transformer": LightweightTransformerClassifier,
    }
    try:
        constructor = constructors[spec.name]
    except KeyError as exc:
        raise ValueError(f"unknown model architecture: {spec.name}") from exc
    return constructor(spec.class_count, spec.hidden_size, spec.dropout)


def parameter_count(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())
