from __future__ import annotations

from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def discover_images(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS)


def inspect_image(path: Path) -> dict[str, object]:
    try:
        from PIL import Image

        with Image.open(path) as image:
            return {"width": image.width, "height": image.height, "format": image.format or path.suffix[1:].upper(), "valid": True}
    except Exception as exc:
        return {"width": None, "height": None, "format": path.suffix[1:].upper(), "valid": False, "error": exc.__class__.__name__}
