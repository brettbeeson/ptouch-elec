"""Render sample labels for every preset in config.toml into demo/."""

from pathlib import Path

from PIL import Image

from labels import LabelError, get_preset, render
from labels.core import preset_names

OUT = Path("demo")
SAMPLES = ["P-101", "SITE A", "LV", "SOLAR-1 DC+", "INV-12 AC L1", "PL-1088-AB", "MDB-3", "WWWWWWWWWWWWWWWW"]


def texts_for(p) -> list[str]:
    """Sample texts sized to the preset: single words, multi-line combos, and a max-length one."""
    fits = [s for s in SAMPLES if len(s) <= p.max_chars]
    texts = list(fits)
    if p.max_lines > 1:
        texts += ["|".join(fits[i : i + p.max_lines]) for i in range(0, len(fits), p.max_lines)]
    texts.append("8" * p.max_chars)  # longest allowed
    return texts


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.png"):
        old.unlink()
    for name in preset_names():
        p = get_preset(name)
        images = []
        for i, text in enumerate(texts_for(p), 1):
            try:
                img = render(p, text)
            except LabelError as e:
                print(f"{name}: skip {text!r}: {e}")
                continue
            img.save(OUT / f"{name}-{i}.png")
            images.append(img)
        # one sheet per preset for a quick look
        w = max(im.width for im in images) + 20
        sheet = Image.new("RGB", (w, sum(im.height + 10 for im in images) + 10), "#bbb")
        y = 10
        for im in images:
            sheet.paste(im, (10, y))
            y += im.height + 10
        sheet.save(OUT / f"{name}-sheet.png")
        print(f"{name}: {len(images)} labels -> {OUT}/{name}-*.png")


if __name__ == "__main__":
    main()
