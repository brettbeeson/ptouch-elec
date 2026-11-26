"""labels PRESET [flags] — then type/pipe labels, one per line."""

import argparse
import sys
from pathlib import Path

from .core import OVERRIDES, LabelError, get_preset, preset_names, print_labels, render

PREVIEW = Path("preview")


def main() -> int:
    ap = argparse.ArgumentParser(prog="labels", description=__doc__)
    ap.add_argument("preset", choices=preset_names())
    ap.add_argument("--preview", action="store_true", help=f"save PNGs to {PREVIEW}/ instead of printing")
    for name, typ in OVERRIDES.items():
        ap.add_argument(f"--{name.replace('_', '-')}", dest=name, type=typ)
    args = ap.parse_args()

    try:
        p = get_preset(args.preset, **{k: getattr(args, k) for k in OVERRIDES})
    except LabelError as e:
        sys.exit(f"error: {e}")

    if args.preview:
        PREVIEW.mkdir(exist_ok=True)
        for old in PREVIEW.glob("*.png"):
            old.unlink()

    ok = True
    for n, line in enumerate(sys.stdin, 1):
        if not (text := line.strip()):
            continue
        try:
            if args.preview:
                render(p, text).save(PREVIEW / f"{p.name}-{n}.png")
            else:
                print_labels(p, text)
            print(f"ok: {text}", file=sys.stderr)
        except (LabelError, OSError) as e:
            ok = False
            print(f"error: {text}: {e}", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
