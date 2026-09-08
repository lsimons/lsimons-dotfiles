#!/usr/bin/env python3
"""Generate desktop backgrounds from an Omarchy theme's colors.toml.

Shipping backgrounds as committed image files would fork the palette: a
change to colors/lsd-colors.json would leave the wallpapers behind. These
are drawn from the theme's own colours instead, so the two cannot drift.

The output is a vertical gradient, which is one solid colour per row —
that costs a few kilobytes as PNG and needs no image library, so the
installer stays dependency-free.
"""

import struct
import sys
import zlib
from pathlib import Path

import tomllib

# 16:9 at a size that still looks clean on a HiDPI panel. A gradient
# rescales without artefacts, so one size covers every monitor.
WIDTH = 2560
HEIGHT = 1440


def _rgb(value):
    """Parse ``#rrggbb`` into an (r, g, b) tuple."""
    text = value.lstrip("#")
    return tuple(int(text[i : i + 2], 16) for i in (0, 2, 4))


def _chunk(tag, payload):
    body = tag + payload
    return struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))


def gradient_png(top, bottom, width=WIDTH, height=HEIGHT):
    """Return PNG bytes for a vertical `top`→`bottom` gradient."""
    top_rgb = _rgb(top)
    bottom_rgb = _rgb(bottom)

    raw = bytearray()
    last = max(height - 1, 1)
    for y in range(height):
        ratio = y / last
        pixel = bytes(
            round(a + (b - a) * ratio) for a, b in zip(top_rgb, bottom_rgb)
        )
        raw.append(0)  # PNG per-scanline filter: none
        raw += pixel * width

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + _chunk(b"IEND", b"")
    )


def theme_background(colors_toml):
    """Return PNG bytes for the background belonging to one theme.

    The gradient runs between the theme's two most recessive surfaces, so
    it reads as depth behind the windows rather than as a second accent.
    """
    colors = tomllib.loads(Path(colors_toml).read_text())
    if colors.get("mode") == "light":
        top, bottom = colors["background"], colors["darker_background"]
    else:
        top, bottom = colors["darker_background"], colors["background"]
    return gradient_png(top, bottom)


if __name__ == "__main__":
    # Handy for eyeballing a palette change:
    #   python3 omarchy/backgrounds.py themes/lsd-warm-dark/colors.toml out.png
    source, destination = sys.argv[1], sys.argv[2]
    Path(destination).write_bytes(theme_background(source))
    print(f"Wrote {destination}")
