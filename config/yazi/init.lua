-- The desktop installer deploys the aliases together with the matching fonts.
local loaded, aliases = pcall(require, "kael-yazi-icons")
if not loaded then
  aliases = {}
end

local entity_style = Entity.style
function Entity:style()
  local style = entity_style(self)
  if style:raw().fg == "Blue" then
    return style:fg(th.mode.normal_main:bg())
  end
  return style
end

function Entity:icon()
  local hovered = self._file.is_hovered
  local icon = th.icon:match(self._file, { hovered = hovered })
  if not icon or icon.text == "" then
    return ""
  end

  local glyph = ui.Span(aliases[icon.text] or icon.text)
  if not hovered then
    glyph = glyph:style(icon.style)
  end
  if self._file.cha.is_dir then
    glyph = glyph:fg(th.mode.normal_main:bg())
  end

  return ui.Line { glyph, "  " }
end
