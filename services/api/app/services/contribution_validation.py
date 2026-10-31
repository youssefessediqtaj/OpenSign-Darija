from __future__ import annotations

import hashlib
import json
import os
import resource
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.contributions import VideoMetadata

WEBM_SIGNATURE = b"\x1a\x45\xdf\xa3"


@dataclass(frozen=True)
class ProbedVideo:
    duration_seconds: float
    width: int
    height: int
    frame_rate: float | None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bounded_child() -> None:
    limits = (
        (resource.RLIMIT_CPU, 10),
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_NOFILE, 32),
        (resource.RLIMIT_NPROC, 16),
    )
    for resource_kind, requested_soft in limits:
        try:
            current_soft, current_hard = resource.getrlimit(resource_kind)
            target_soft = (
                requested_soft
                if current_soft == resource.RLIM_INFINITY
                else min(current_soft, requested_soft)
            )
            resource.setrlimit(resource_kind, (target_soft, current_hard))
        except (OSError, ValueError):
            # Timeout and fixed-process arguments remain enforced on platforms
            # where an individual POSIX resource limit cannot be lowered.
            continue


def _run_media_command(
    command: list[str], timeout_seconds: float
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            shell=False,
            preexec_fn=_bounded_child if os.name == "posix" else None,
        )
    except (OSError, subprocess.SubprocessError, subprocess.TimeoutExpired) as error:
        raise ApiError(
            "VIDEO_VALIDATION_UNAVAILABLE",
            "La validation de la vidéo est momentanément indisponible.",
            503,
        ) from error


def _parse_frame_rate(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        parsed = float(Fraction(value))
    except (ValueError, ZeroDivisionError):
        return None
    return parsed if parsed > 0 else None


def probe_and_decode_video(path: Path, settings: Settings) -> ProbedVideo:
    probe = _run_media_command(
        [
            settings.contribution_ffprobe_path,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,duration:format=duration,format_name",
            "-of",
            "json",
            str(path),
        ],
        settings.contribution_probe_timeout_seconds,
    )
    if probe.returncode != 0:
        raise ApiError("INVALID_VIDEO", "La vidéo est illisible ou mal formée.", 422)
    try:
        payload: dict[str, Any] = json.loads(probe.stdout)
        streams = payload.get("streams", [])
        stream = streams[0]
        format_data = payload.get("format", {})
        format_name = str(format_data.get("format_name", "")).lower()
        duration = float(stream.get("duration") or format_data.get("duration"))
        width = int(stream["width"])
        height = int(stream["height"])
    except (IndexError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ApiError("INVALID_VIDEO", "La vidéo ne contient pas de piste valide.", 422) from error
    if "webm" not in format_name and "matroska" not in format_name:
        raise ApiError("UNSUPPORTED_VIDEO_CONTAINER", "Le conteneur vidéo n’est pas accepté.", 415)

    decode = _run_media_command(
        [
            settings.contribution_ffmpeg_path,
            "-v",
            "error",
            "-xerror",
            "-i",
            str(path),
            "-map",
            "0:v:0",
            "-f",
            "null",
            "-",
        ],
        settings.contribution_probe_timeout_seconds,
    )
    if decode.returncode != 0:
        raise ApiError("INVALID_VIDEO", "La vidéo ne peut pas être décodée en sécurité.", 422)
    return ProbedVideo(
        duration_seconds=duration,
        width=width,
        height=height,
        frame_rate=_parse_frame_rate(stream.get("r_frame_rate")),
    )


def validate_staged_video(
    path: Path,
    *,
    declared_mime_type: str,
    settings: Settings,
    expected_min_duration_seconds: float,
    expected_max_duration_seconds: float,
) -> VideoMetadata:
    normalized_mime = declared_mime_type.strip().lower()
    if normalized_mime not in settings.contribution_allowed_mime_types:
        raise ApiError("UNSUPPORTED_VIDEO_TYPE", "Le format vidéo n’est pas accepté.", 415)
    size = path.stat().st_size
    if size < settings.contribution_min_video_bytes:
        raise ApiError("VIDEO_TOO_SMALL", "La vidéo envoyée est vide ou trop petite.", 422)
    if size > settings.contribution_max_video_bytes:
        raise ApiError(
            "VIDEO_TOO_LARGE",
            "La vidéo dépasse la taille maximale autorisée.",
            413,
            {"max_bytes": settings.contribution_max_video_bytes},
        )
    with path.open("rb") as stream:
        signature = stream.read(len(WEBM_SIGNATURE))
    if signature != WEBM_SIGNATURE:
        raise ApiError(
            "INVALID_VIDEO_SIGNATURE", "Le contenu ne correspond pas à une vidéo WebM.", 415
        )

    probed = probe_and_decode_video(path, settings)
    minimum = max(settings.contribution_min_duration_seconds, expected_min_duration_seconds)
    maximum = min(settings.contribution_max_duration_seconds, expected_max_duration_seconds)
    if probed.duration_seconds < minimum:
        raise ApiError(
            "VIDEO_TOO_SHORT",
            "La vidéo est trop courte.",
            422,
            {"minimum_seconds": minimum},
        )
    if probed.duration_seconds > maximum:
        raise ApiError(
            "VIDEO_TOO_LONG",
            "La vidéo est trop longue.",
            422,
            {"maximum_seconds": maximum},
        )
    if probed.width <= 0 or probed.height <= 0 or probed.width > 4096 or probed.height > 4096:
        raise ApiError("INVALID_VIDEO_DIMENSIONS", "Les dimensions vidéo sont invalides.", 422)
    if probed.frame_rate is not None and (probed.frame_rate < 1 or probed.frame_rate > 120):
        raise ApiError("INVALID_VIDEO_FRAME_RATE", "La fréquence vidéo est invalide.", 422)
    return VideoMetadata(
        sha256=sha256_file(path),
        mime_type=normalized_mime,
        file_size_bytes=size,
        duration_seconds=probed.duration_seconds,
        width=probed.width,
        height=probed.height,
        frame_rate=probed.frame_rate,
    )
