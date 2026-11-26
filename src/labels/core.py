"""Render and print preset labels on a Brother P-touch via ptouch."""

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
import ptouch
from ptouch import ConnectionNetwork, Label, Tape6mm, Tape9mm, Tape12mm, Tape18mm, Tape24mm

PRESETS_FILE = Path(__file__).resolve().parents[2] / "config.toml"  # brother/config.toml
TAPES = {6: Tape6mm, 9: Tape9mm, 12: Tape12mm, 18: Tape18mm, 24: Tape24mm}
LINE_SPACING = 1.15
LEFT_PAD_MM = 2  # extra inset for align = "left", on top of the feed margin


class LabelError(ValueError):
    pass


@dataclass(frozen=True)
class Preset:
    name: str
    font_size: float            # mm
    max_chars: int
    max_lines: int = 1
    repeat: int = 1             # print the line N times stacked
    align: str = "centre"       # "left" or "centre" (horizontal, along each line)
    slots: int = 0              # lay out as if N lines, filling from the top (0 = centre actual lines)
    orientation: str = "long"   # long: along the tape; short: across the tape
    label_length: float = 0     # mm incl. margins; 0 = fit text
    label_width: float = 12     # tape width, mm
    font: str = "DejaVuSansMono-Bold.ttf"
    printer: str = "P750W"
    margin: float = 2
    chain: bool = False         # don't feed+cut after a job: no ~25mm leader on the next one
    description: str = ""
    ip: str = ""

    @property
    def printer_class(self) -> type[ptouch.LabelPrinter]:
        return getattr(ptouch, f"PT{self.printer}")

    @property
    def tape(self) -> type[ptouch.Tape]:
        return TAPES[int(self.label_width)]


# Overridable from env (PTOUCH_<NAME>) and CLI flags (--<name>)
OVERRIDES = {"ip": str, "font": str, "font_size": float, "label_width": float, "label_length": float}


def get_preset(name: str, **overrides) -> Preset:
    """Load a preset from config.toml; then env vars, then `overrides`, win."""
    data = tomllib.loads(PRESETS_FILE.read_text())
    presets = data.pop("presets")
    if name not in presets:
        raise LabelError(f"unknown preset {name!r}; choose from {', '.join(presets)}")
    p = Preset(name=name, **data, **presets[name])
    env = {k: t(os.environ[f"PTOUCH_{k.upper()}"]) for k, t in OVERRIDES.items()
           if os.environ.get(f"PTOUCH_{k.upper()}")}
    return replace(p, **(env | {k: v for k, v in overrides.items() if v is not None}))


def preset_names() -> list[str]:
    return list(tomllib.loads(PRESETS_FILE.read_text())["presets"])


def render(p: Preset, text: str) -> Image.Image:
    """Render text (lines separated by '|') to an image ready for ptouch."""
    lines = [ln.strip() for ln in text.split("|")]  # empty segment = blank line
    if not text.strip():
        raise LabelError("empty label")
    if len(lines) > p.max_lines:
        raise LabelError(f"{len(lines)} lines, max {p.max_lines}")
    if too_long := [ln for ln in lines if len(ln) > p.max_chars]:
        raise LabelError(f"{too_long[0]!r} longer than {p.max_chars} chars")
    lines *= p.repeat
    lines += [""] * (p.slots - len(lines))  # pad so line 1 sits at a fixed position

    px = lambda mm: round(mm * p.printer_class.RESOLUTION_DPI / 25.4)  # noqa: E731
    pins = p.printer_class.PIN_CONFIGS[p.tape].print_pins
    font = ImageFont.truetype(p.font, px(p.font_size))
    pitch = px(p.font_size) * LINE_SPACING
    text_w = max(font.getlength(ln) for ln in lines)
    text_h = (len(lines) - 1) * pitch + sum(font.getmetrics())
    length = px(p.label_length - 2 * p.margin) if p.label_length else None

    rotate = p.orientation == "short"
    # Lines run along x, stack along y. Rotated labels are drawn sideways then turned.
    w, h = (pins, length or int(text_h) + 8) if rotate else (length or int(text_w) + 8, pins)
    if text_w + (px(LEFT_PAD_MM) if p.align == "left" else 0) > w or text_h > h:
        raise LabelError(f"{text!r} doesn't fit at {p.font_size}mm; shorten or reduce font size")

    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)
    y0 = h / 2 - (len(lines) - 1) * pitch / 2
    for i, ln in enumerate(lines):
        x, anchor = (px(LEFT_PAD_MM), "lm") if p.align == "left" else (w / 2, "mm")
        draw.text((x, y0 + i * pitch), ln, font=font, fill="black", anchor=anchor)
    return img.transpose(Image.Transpose.ROTATE_90) if rotate else img


def print_labels(p: Preset, texts: list[str] | str) -> None:
    """Print one or more labels as a single job."""
    texts = [texts] if isinstance(texts, str) else texts
    if not p.ip:
        raise LabelError("no printer IP: set PTOUCH_IP")
    labels = [Label(render(p, t), p.tape) for t in texts]
    conn = ConnectionNetwork(p.ip)
    try:
        printer = p.printer_class(conn)
        if p.chain:  # ptouch hardcodes chain_printing=False; force it on (ESC i K bit 3 clear)
            adv = printer._cmd_advanced_mode_settings
            printer._cmd_advanced_mode_settings = lambda half_cut=False, chain_printing=False, \
                high_resolution=False: adv(half_cut, True, high_resolution)
        printer.print_multi(labels, margin_mm=p.margin)
    finally:
        conn.close()
