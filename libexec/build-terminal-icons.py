#!/usr/bin/env python3
"""Build scalable prompt and status glyphs for the terminal icon font."""

import argparse
from pathlib import Path

from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fonts/StarshipPromptIcons"
NERD_FONT = ROOT / "fonts/SauceCodeProNF"
WARNING = 0x26A0
LIGHTNING = 0xF0E7
GPU = 0xF08AE
WARNING_SCALE = 1.12
CENTER_X = 300
CENTER_Y = 320
TARGETS = {
    LIGHTNING: (700, 860),
    GPU: (720, 480),
}


def draw_warning_outline(font, name):
    # Exact mirrored geometry keeps the triangle, stem, and dot upright at
    # terminal sizes. The base also stays inside the font's line box.
    pen = TTGlyphPen(None)
    pen.moveTo((245, 760))
    pen.qCurveTo((300, 860), (355, 760))
    pen.lineTo((705, 120))
    pen.qCurveTo((762, 15), (680, 15))
    pen.lineTo((-80, 15))
    pen.qCurveTo((-162, 15), (-105, 120))
    pen.lineTo((245, 760))
    pen.closePath()

    pen.moveTo((260, 650))
    pen.lineTo((-25, 120))
    pen.qCurveTo((-60, 60), (0, 60))
    pen.lineTo((600, 60))
    pen.qCurveTo((660, 60), (625, 120))
    pen.lineTo((340, 650))
    pen.qCurveTo((300, 735), (260, 650))
    pen.closePath()

    pen.moveTo((260, 570))
    pen.qCurveTo((260, 610), (300, 610))
    pen.qCurveTo((340, 610), (340, 570))
    pen.lineTo((328, 280))
    pen.qCurveTo((326, 250), (300, 250))
    pen.qCurveTo((274, 250), (272, 280))
    pen.closePath()

    pen.moveTo((300, 205))
    pen.qCurveTo((332, 205), (345, 180))
    pen.qCurveTo((360, 155), (345, 130))
    pen.qCurveTo((332, 105), (300, 105))
    pen.qCurveTo((268, 105), (255, 130))
    pen.qCurveTo((240, 155), (255, 180))
    pen.qCurveTo((268, 205), (300, 205))
    pen.closePath()
    glyph = pen.glyph()
    # Grow around the center of the base to keep its baseline and cell width.
    base_y = 15
    glyph.coordinates.translate((-CENTER_X, -base_y))
    glyph.coordinates.scale((1.035 * WARNING_SCALE, WARNING_SCALE))
    glyph.coordinates.translate((CENTER_X, base_y))
    glyph.recalcBounds(font["glyf"])
    font["glyf"][name] = glyph
    font["hmtx"][name] = (600, glyph.xMin)


def fit_outline(source_font, source_name, target_font, target_name, width, height):
    source_table = source_font["glyf"]
    source = source_table[source_name]
    scale_x = width / (source.xMax - source.xMin)
    scale_y = height / (source.yMax - source.yMin)
    translate_x = CENTER_X - scale_x * (source.xMin + source.xMax) / 2
    translate_y = CENTER_Y - scale_y * (source.yMin + source.yMax) / 2
    pen = TTGlyphPen(None)
    source.draw(TransformPen(pen, (scale_x, 0, 0, scale_y, translate_x, translate_y)), source_table)
    glyph = pen.glyph()
    glyph.recalcBounds(target_font["glyf"])
    target_font["glyf"][target_name] = glyph
    target_font["hmtx"][target_name] = (600, glyph.xMin)


def build(source, output, style):
    nerd_path = NERD_FONT / f"SauceCodeProNerdFontMono-{style}.ttf"
    with TTFont(source, recalcTimestamp=False) as font, TTFont(nerd_path) as nerd:
        cmap = font.getBestCmap()
        warning = cmap[WARNING]
        draw_warning_outline(font, warning)
        nerd_cmap = nerd.getBestCmap()
        for codepoint, size in TARGETS.items():
            name = cmap.get(codepoint)
            if name is None:
                name = f"uni{codepoint:04X}" if codepoint <= 0xFFFF else f"u{codepoint:05X}"
                font.setGlyphOrder([*font.getGlyphOrder(), name])
                for table in font["cmap"].tables:
                    if table.isUnicode() and (table.format == 12 or (table.format == 4 and codepoint <= 0xFFFF)):
                        table.cmap[codepoint] = name
            fit_outline(nerd, nerd_cmap[codepoint], font, name, *size)

        # A fixed-size sbix strike makes the entire font render poorly at normal
        # terminal sizes. Both symbols now use tintable outlines instead.
        if "sbix" in font:
            del font["sbix"]
        for record in font["name"].names:
            if record.nameID == 0:
                text = record.toUnicode()
                record.string = text.replace("\nTerminal artwork by Icons8 (https://icons8.com).", "")
        font.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_directory", type=Path)
    output = parser.parse_args().output_directory
    if output.resolve() == SOURCE:
        parser.error("choose an output directory outside the bundled font directory")
    output.mkdir(parents=True, exist_ok=True)
    for style in ("Regular", "Bold"):
        name = f"StarshipPromptIcons-{style}.ttf"
        build(SOURCE / name, output / name, style)


if __name__ == "__main__":
    main()
