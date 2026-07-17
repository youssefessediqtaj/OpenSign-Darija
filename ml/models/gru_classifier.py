from __future__ import annotations


def require_torch() -> object:
    try:
        import torch
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "PyTorch is required for GRU training. Install ML dependencies before training."
        ) from exc
    return torch


def build_gru_classifier(feature_count: int, class_count: int, hidden_size: int = 128) -> object:
    torch = require_torch()
    nn = torch.nn

    class GRUClassifier(nn.Module):  # type: ignore[name-defined]
        def __init__(self) -> None:
            super().__init__()
            self.projection = nn.Linear(feature_count, hidden_size)
            self.gru = nn.GRU(
                hidden_size,
                hidden_size,
                num_layers=2,
                batch_first=True,
                bidirectional=True,
                dropout=0.3,
            )
            self.dropout = nn.Dropout(0.3)
            self.classifier = nn.Linear(hidden_size * 2, class_count)

        def forward(self, features: object, presence_mask: object) -> object:
            projected = torch.relu(self.projection(features))
            encoded, _ = self.gru(projected)
            frame_mask = (presence_mask.sum(dim=-1) > 0).float().unsqueeze(-1)
            pooled = (encoded * frame_mask).sum(dim=1) / frame_mask.sum(dim=1).clamp_min(1.0)
            return self.classifier(self.dropout(pooled))

    return GRUClassifier()
