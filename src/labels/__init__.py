"""Preset label printing on a Brother P-touch (via ptouch).

    from labels import get_preset, print_labels
    print_labels(get_preset("pole"), ["P-101", "P-102"])
    print_labels(get_preset("pole-short", font_size=3), "SITE A|P-101|LV")
"""

from .core import LabelError, Preset, get_preset, print_labels, render

__all__ = ["LabelError", "Preset", "get_preset", "print_labels", "render"]
