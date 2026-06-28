"""Square crop + pan/zoom preview for wolf proxy avatars."""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageDraw, ImageOps

OUTPUT_SIZE = 256
PREVIEW_SIZE = 384
MAX_BYTES = 256 * 1024
ALLOWED_CONTENT_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"}
)

ALLOWED_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})

PAN_STEP = 24
ZOOM_STEP = 0.12
MIN_ZOOM = 1.0
MAX_ZOOM = 4.0


@dataclass
class CropState:
    offset_x: float = 0.0
    offset_y: float = 0.0
    zoom: float = 1.0

    def reset(self) -> None:
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.zoom = 1.0

def _open_image(data: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(data))
    if getattr(img, "is_animated", False):
        img.seek(0)
    return ImageOps.exif_transpose(img.convert("rgba"))


def _base_scale(img: Image.Image, crop_size: int) -> float:
    return max(crop_size / img.width, crop_size / img.height)


def _scaled_crop_box(img: Image.Image, state: CropState, crop_size: int) -> tuple[int, int, int, int]:
    scale = _base_scale(img, crop_size) * state.zoom
    sw = img.width * scale
    sh = img.height * scale
    left = (sw - crop_size) / 2 + state.offset_x
    top = (sh - crop_size) / 2 + state.offset_y
    # Clamp so the crop window stays inside the scaled image.
    left = max(0.0, min(left, sw - crop_size))
    top = max(0.0, min(top, sh - crop_size))
    # Map back to original image coordinates.
    x0 = int(left / scale)
    y0 = int(top / scale)
    x1 = int((left + crop_size) / scale)
    y1 = int((top + crop_size) / scale)
    return x0, y0, x1, y1


def render_cropped_png(data: bytes, state: CropState, *, preview: bool = False) -> bytes:
    img = _open_image(data)
    crop_size = PREVIEW_SIZE if preview else OUTPUT_SIZE
    box = _scaled_crop_box(img, state, crop_size)
    cropped = img.crop(box).resize((crop_size, crop_size), Image.Resampling.LANCZOS)
    if preview:
        # Show the circular mask Discord uses on webhook avatars.
        mask = Image.new("L", (crop_size, crop_size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, crop_size - 1, crop_size - 1), fill=255)
        bg = Image.new("RGBA", (crop_size, crop_size), (32, 32, 40, 255))
        bg.paste(cropped, (0, 0), mask)
        cropped = bg
    out = io.BytesIO()
    cropped.save(out, format="PNG", optimize=True)
    return out.getvalue()


def validate_avatar_upload(
    data: bytes, *, content_type: str | None = None, filename: str | None = None
) -> str | None:
    if len(data) > 8 * 1024 * 1024:
        return "image must be 8 mb or smaller."
    if content_type and content_type.split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        if not (filename and any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS)):
            return "use a png, jpg, webp, or gif image."
    try:
        img = _open_image(data)
        if img.width < 32 or img.height < 32:
            return "image is too small; use at least 32×32 pixels."
    except Exception:
        return "could not read that image file."
    return None
