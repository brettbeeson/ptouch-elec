# labels

Preset-driven label printing for a Brother P-touch (default: PT-P750W over the network), built on [ptouch](https://pypi.org/project/ptouch/). It's aimed at electrical work like pole tags and cable wraps. Each preset in `config.toml` sets the font size, orientation, length and limits. You then type or pipe in the label text.

## Setup

Requires Python ≥ 3.15 and [uv](https://docs.astral.sh/uv/). [just](https://github.com/casey/just) and [direnv](https://direnv.net/) are optional.

```sh
uv sync
echo 'PTOUCH_IP=192.168.1.50' > .env   # your printer's IP
```

The default font is `DejaVuSansMono-Bold.ttf`, which must be findable by Pillow (it is installed on most Linux systems). To use another font, set `font` to a font name or path.

## Usage

```sh
labels PRESET [--preview] [--ip IP] [--font FONT] [--font-size MM] [--label-width MM] [--label-length MM]
```

Labels are read from stdin, one per line. Use `|` to separate lines within a single label.

```sh
# Print interactively (Ctrl-D to finish)
just run pole

# Print from a file
just run pole-short < poles.txt

# Multi-line label
echo 'SITE A|P-101|LV' | uv run labels pole-short

# Preview to preview/*.png instead of printing
uv run labels cable --preview < cables.txt
```

Each label prints as its own job. The CLI reports `ok:` or `error:` for each line on stderr. It skips text that is too long, has too many lines or doesn't fit, and exits non-zero if any label failed.

### Chain printing

`chain = true` (the default in `config.toml`) suppresses the feed and cut after each job, which avoids a ~25 mm blank leader on the next label. As a result, **the last label stays in the printer. Press the feed/cut button to eject it.**

## Presets

| Preset | Description |
| --- | --- |
| `pole` | One large line along the tape, left-justified (40 mm, ≤12 chars) |
| `pole-centred` | Same as `pole`, centred |
| `pole-short` | Up to 3 smaller lines across the tape, top-aligned (25 mm, ≤6 chars/line) |
| `pole-short-centred` | Same as `pole-short`, centred vertically |
| `cable` | Cable wrap: the text repeated 3× stacked, small (≤16 chars) |

### Configuration

All lengths in `config.toml` are in mm. Top-level keys are defaults for every preset, and each `[presets.NAME]` table overrides them. The available keys are:

| Key | Meaning |
| --- | --- |
| `printer` | ptouch printer class suffix, e.g. `P750W` → `PTP750W` |
| `label_width` | Tape width: 6, 9, 12, 18 or 24 |
| `label_length` | Total length including margins; `0` = fit to text |
| `margin` | Feed margin at each end |
| `orientation` | `long` (text along the tape) or `short` (across it) |
| `font`, `font_size` | Font file and font size in mm |
| `max_chars`, `max_lines` | Limits per line / per label |
| `align` | `left` or `centre` |
| `repeat` | Print the text N times stacked |
| `slots` | Lay out as if N lines so line 1 is always at the same position |
| `chain` | Skip feed+cut between jobs |

Settings are resolved in this order, with later sources winning: `config.toml`, then the env vars `PTOUCH_IP`, `PTOUCH_FONT`, `PTOUCH_FONT_SIZE`, `PTOUCH_LABEL_WIDTH` and `PTOUCH_LABEL_LENGTH`, then CLI flags.

To add a preset, add a `[presets.NAME]` table. It then appears automatically in the CLI choices.

## Demo

```sh
just demo
```

This renders sample labels for every preset into `demo/`, plus one `NAME-sheet.png` contact sheet per preset, without needing a printer.

## Python API

```python
from labels import get_preset, print_labels, render

print_labels(get_preset("pole"), ["P-101", "P-102"])           # one job
print_labels(get_preset("pole-short", font_size=3), "SITE A|P-101|LV")
render(get_preset("cable"), "INV-12 AC L1").save("cable.png")  # image only
```

Bad input raises `LabelError`.

## License

MIT
