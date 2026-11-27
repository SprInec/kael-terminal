#!/usr/bin/env python3
"""Match Starship's monochrome glyphs to its existing package/Python icon size."""

import os
from pathlib import Path
import tempfile
import tomllib

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/starship/starship.toml"
FONT_DIR = ROOT / "fonts/StarshipPromptIcons"
FONT_FAMILY = "Kael Starship Prompt Icons"

# The bundled package and Python glyphs are centered here and are 970/989 units
# tall. The two-cell artwork is at most 1100 units wide.
BOX_HEIGHT = 989
BOX_WIDTH = 1100
CENTER_X = 600
CENTER_Y = 355.5
PACKAGE = ord("")
GIT_BRANCH = ord("")
GIT_HOST_ICONS = {ord(""), ord("")}


def icon_codepoints():
    config = tomllib.loads(CONFIG.read_text())
    symbols = []
    for section, options in config.items():
        if not isinstance(options, dict):
            continue
        for key, value in options.items():
            if section == "os" and key == "symbols":
                symbols.extend(value.values())
            elif key.endswith("symbol") or key.endswith("_symbol") or (section, key) == ("directory", "read_only"):
                if isinstance(value, str):
                    symbols.append(value)
    return {ord(char) for symbol in symbols for char in symbol if ord(char) >= 0xE000} | GIT_HOST_ICONS


def color_glyphs(font):
    if "COLR" not in font:
        return set()
    table = font["COLR"].table
    legacy = table.BaseGlyphRecordArray
    modern = table.BaseGlyphList
    return ({record.BaseGlyph for record in legacy.BaseGlyphRecord} if legacy else set()) | (
        {record.BaseGlyph for record in modern.BaseGlyphPaintRecord} if modern else set()
    )


def normalize(font, codepoints):
    cmap = font.getBestCmap()
    colored = color_glyphs(font)
    changed = []
    verified_color = []
    for codepoint in sorted(codepoints - {PACKAGE, GIT_BRANCH}):
        name = cmap.get(codepoint)
        if name is None:
            continue
        glyph = font["glyf"][name]
        if not hasattr(glyph, "xMin"):
            continue
        width, height = glyph.xMax - glyph.xMin, glyph.yMax - glyph.yMin
        scale = min(BOX_WIDTH / width, BOX_HEIGHT / height)
        center_x = (glyph.xMin + glyph.xMax) / 2
        center_y = (glyph.yMin + glyph.yMax) / 2
        if name in colored:
            # Ubuntu, GitLab, and the other COLR artwork already use the same
            # box. Check them without changing their layers or gradients.
            if abs(scale - 1) > 0.02 or abs(center_x - CENTER_X) > 5 or abs(center_y - CENTER_Y) > 5:
                raise ValueError(f"colored Starship icon U+{codepoint:04X} is outside the reference box")
            verified_color.append(codepoint)
            continue
        if abs(scale - 1) <= 0.003 and abs(center_x - CENTER_X) <= 1 and abs(center_y - CENTER_Y) <= 1:
            continue
        pen = TTGlyphPen(font["glyf"])
        transform = TransformPen(
            pen,
            (scale, 0, 0, scale, CENTER_X - scale * center_x, CENTER_Y - scale * center_y),
        )
        glyph.draw(transform, font["glyf"])
        resized = pen.glyph()
        resized.recalcBounds(font["glyf"])
        font["glyf"][name] = resized
        advance, _ = font["hmtx"][name]
        font["hmtx"][name] = (advance, resized.xMin)
        changed.append(codepoint)
    return changed, verified_color


def set_unique_family(font, style):
    changed = False
    replacements = {
        1: FONT_FAMILY,
        3: f"KaelStarshipPromptIcons-{style}-20261125",
        4: f"{FONT_FAMILY} {style}",
        6: f"KaelStarshipPromptIcons-{style}",
        16: FONT_FAMILY,
    }
    for record in font["name"].names:
        replacement = replacements.get(record.nameID)
        if replacement is not None and record.toUnicode() != replacement:
            record.string = replacement.encode("utf_16_be" if record.platformID == 3 else "mac_roman")
            changed = True
    return changed


def main():
    codepoints = icon_codepoints()
    for style in ("Regular", "Bold"):
        path = FONT_DIR / f"StarshipPromptIcons-{style}.ttf"
        with TTFont(path, recalcTimestamp=False) as font:
            changed, verified_color = normalize(font, codepoints)
            renamed = set_unique_family(font, style)
            if changed or renamed:
                fd, temporary = tempfile.mkstemp(dir=path.parent, suffix=".ttf")
                os.close(fd)
                try:
                    font.save(temporary)
                    os.replace(temporary, path)
                finally:
                    if os.path.exists(temporary):
                        os.unlink(temporary)
        print(f"{style}: resized {len(changed)} monochrome glyphs; verified {len(verified_color)} colored glyphs; family {FONT_FAMILY}")


if __name__ == "__main__":
    main()
