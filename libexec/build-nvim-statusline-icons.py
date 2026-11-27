#!/usr/bin/env python3
"""Build the LazyVim glyphs in the bundled Kael fonts."""

import argparse
import json
import math
import os
from pathlib import Path
import subprocess

from fontTools.colorLib.builder import LayerListBuilder, buildClipBox
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables.otTables import BaseGlyphPaintRecord, PaintFormat


ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = ROOT / "fonts/StarshipPromptIcons"
NERD_FONT_DIR = ROOT / "fonts/SauceCodeProNF"
MANIFEST = ROOT / "config/nvim/lua/kael/statusline-icons.json"
COMPACT_SCALE = 0.90
COMPACT_CENTER = (600, 356)

# Neovim filetypes whose names differ from the existing artwork sources.
FILETYPE_ALIASES = {
    "cmakecache": "cmake",
    "cpp": "cplusplus",
    "dockerfile": "docker",
    "nix": "nixos",
    "terraform-vars": "terraform",
    "v": "vlang",
}
# Root, read-only, diagnostics, file defaults and overrides, and clock.
STATUSLINE_GLYPHS = "󱉭󰌾󰊢"
# Trouble symbols that use different outlines than mini.icons' LSP category.
TROUBLE_GLYPHS = "󰨙󰏿󰊕󰦮󰎠"
# Snacks picker symbols outside mini.icons' inventory.
SNACKS_GLYPHS = "󰝰󱄽󰓅"
# Default LazyVim dashboard menu symbols.
DASHBOARD_GLYPHS = "󰒲"
# Which-key's profiler icon uses a Unicode character outside the PUA.
UNICODE_GLYPH_ALIASES = {0x26A1: 0xF8800}
ICON_INVENTORY = """
vim.opt.rtp:prepend(vim.env.KAEL_MINI_ICONS)
local icons = require("mini.icons")
icons.setup()
local result = { filetypes = icons.list("filetype"), glyphs = {} }
for _, category in ipairs({ "default", "directory", "file", "extension", "filetype", "lsp" }) do
  for _, name in ipairs(icons.list(category)) do
    result.glyphs[icons.get(category, name)] = true
  end
end
local which_key = vim.env.KAEL_WHICH_KEY
if vim.uv.fs_stat(which_key .. "/lua/which-key/icons.lua") then
  vim.opt.rtp:prepend(which_key)
  for _, rule in ipairs(require("which-key.icons").rules) do
    if rule.icon then
      result.glyphs[vim.trim(rule.icon)] = true
    end
  end
  for _, icon in pairs(require("which-key.config").icons.keys) do
    result.glyphs[vim.trim(icon)] = true
  end
end
io.write(vim.json.encode(result))
vim.cmd("qa!")
"""


def icon_inventory(mini_icons, which_key):
    result = subprocess.run(
        ["nvim", "--headless", "-u", "NONE", "-i", "NONE", "-c", "lua " + ICON_INVENTORY],
        env={**os.environ, "KAEL_MINI_ICONS": str(mini_icons), "KAEL_WHICH_KEY": str(which_key)},
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def add_outline(font, nerd, codepoint, alias):
    cmap = font.getBestCmap()
    if codepoint in cmap:
        source, name = font, cmap[codepoint]
    else:
        source, name = nerd, nerd.getBestCmap()[codepoint]
    table = source["glyf"]
    original = table[name]

    width = original.xMax - original.xMin
    height = original.yMax - original.yMin
    # Use the same two-cell artwork box as the Starship package and Python glyphs.
    scale = min(1100 / width, 989 / height)
    left = 600 - scale * (original.xMin + original.xMax) / 2
    bottom = 355.5 - scale * (original.yMin + original.yMax) / 2
    pen = TTGlyphPen(font["glyf"])
    original.draw(TransformPen(pen, (scale, 0, 0, scale, left, bottom)), table)
    set_outline(font, alias, pen.glyph())


def set_outline(font, alias, glyph):
    glyph.recalcBounds(font["glyf"])
    cmap = font.getBestCmap()
    name = cmap.get(alias, f"u{alias:05X}")
    if alias not in cmap:
        font["glyf"].glyphOrder.append(name)
        for subtable in font["cmap"].tables:
            if subtable.isUnicode() and subtable.format in (12, 13):
                subtable.cmap[alias] = name
    font["glyf"][name] = glyph
    font["hmtx"][name] = (600, glyph.xMin)
    return name


def add_compact_glyphs(font, codepoints):
    cmap = font.getBestCmap()
    colr = font["COLR"].table
    base_list = colr.BaseGlyphList
    records = {record.BaseGlyph: record for record in base_list.BaseGlyphPaintRecord}
    paint_builder = LayerListBuilder()
    center_x, center_y = COMPACT_CENTER
    scale = COMPACT_SCALE
    dx = center_x * (1 - scale)
    dy = center_y * (1 - scale)
    variants = {}

    for codepoint in sorted(codepoints):
        # Plane 16 holds compact versions of the existing PUA glyphs.
        offset = 0x8000 if codepoint >= 0xF8000 else 0xFA000
        alias = codepoint + offset
        source = cmap[codepoint]
        pen = TTGlyphPen(font["glyf"])
        pen.addComponent(source, (scale, 0, 0, scale, dx, dy))
        name = set_outline(font, alias, pen.glyph())
        variants[str(codepoint)] = alias

        if source in records:
            record = BaseGlyphPaintRecord()
            record.BaseGlyph = name
            record.Paint = paint_builder.buildPaint({
                "Format": PaintFormat.PaintScaleUniformAroundCenter,
                "Paint": {"Format": PaintFormat.PaintColrGlyph, "Glyph": source},
                "scale": scale,
                "centerX": center_x,
                "centerY": center_y,
            })
            records[name] = record

            if colr.ClipList and (clip := colr.ClipList.clips.get(source)):
                colr.ClipList.clips[name] = buildClipBox((
                    math.floor(scale * clip.xMin + dx),
                    math.floor(scale * clip.yMin + dy),
                    math.ceil(scale * clip.xMax + dx),
                    math.ceil(scale * clip.yMax + dy),
                ))

    glyph_ids = font.getReverseGlyphMap(rebuild=True)
    base_list.BaseGlyphPaintRecord = sorted(records.values(), key=lambda record: glyph_ids[record.BaseGlyph])
    base_list.BaseGlyphCount = len(records)
    return variants


def color_codepoints(font):
    colr = font["COLR"].table
    names = set()
    if colr.BaseGlyphList:
        names.update(record.BaseGlyph for record in colr.BaseGlyphList.BaseGlyphPaintRecord)
    if colr.BaseGlyphRecordArray:
        names.update(record.BaseGlyph for record in colr.BaseGlyphRecordArray.BaseGlyphRecord)
    return {codepoint for codepoint, name in font.getBestCmap().items() if name in names}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    xdg_data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    parser.add_argument("--mini-icons", type=Path, default=xdg_data / "nvim/lazy/mini.icons")
    parser.add_argument("--which-key", type=Path, help="Which-key checkout, next to mini.icons by default")
    args = parser.parse_args()
    which_key = args.which_key or args.mini_icons.with_name("which-key.nvim")
    inventory = icon_inventory(args.mini_icons, which_key)
    glyphs = set(inventory["glyphs"]) | set(STATUSLINE_GLYPHS + TROUBLE_GLYPHS + SNACKS_GLYPHS + DASHBOARD_GLYPHS)
    sources = json.loads((ROOT / "config/starship/icon-sources.json").read_text())["sources"]
    brand_codepoints = {key: int(value["codepoint"], 16) for key, value in sources.items() if key != "git"}
    brand_codepoints["python"] = 0xE606

    manifest = None
    for style in ("Regular", "Bold"):
        path = FONT_DIR / f"StarshipPromptIcons-{style}.ttf"
        nerd_path = NERD_FONT_DIR / f"SauceCodeProNerdFontMono-{style}.ttf"
        with TTFont(path, recalcTimestamp=False) as font, TTFont(nerd_path) as nerd:
            colors = color_codepoints(font)
            filetypes = {}
            for filetype in sorted(inventory["filetypes"]):
                codepoint = brand_codepoints.get(FILETYPE_ALIASES.get(filetype, filetype))
                if codepoint in colors:
                    filetypes[filetype] = codepoint

            available = font.getBestCmap().keys() | nerd.getBestCmap().keys()
            outlines = {}
            for char in sorted(glyphs):
                if len(char) != 1:
                    continue
                codepoint = ord(char)
                if codepoint in colors:
                    continue
                # The private-use aliases preserve the original glyphs elsewhere.
                alias = UNICODE_GLYPH_ALIASES.get(codepoint)
                if 0xE000 <= codepoint <= 0xF8FF:
                    alias = codepoint + 0xEF000
                elif 0xF0000 <= codepoint <= 0xF1FFF:
                    alias = codepoint + 0x9000
                if alias is None:
                    continue
                if codepoint not in available:
                    raise ValueError(f"{style} font is missing U+{codepoint:04X}")
                add_outline(font, nerd, codepoint, alias)
                outlines[str(codepoint)] = alias

            compact = add_compact_glyphs(font, set(outlines.values()).union(filetypes.values()))
            data = {"filetypes": filetypes, "glyphs": outlines, "compact": compact}
            if manifest is not None and manifest != data:
                raise ValueError("Regular and Bold statusline coverage differs")
            manifest = data
            font.save(path)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
