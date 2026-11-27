local manifest = vim.api.nvim_get_runtime_file("lua/kael/statusline-icons.json", false)[1]
if not manifest then
  return {}
end
local icons = vim.json.decode(table.concat(vim.fn.readfile(manifest), "\n"))
-- Reserve the glyph's second cell and leave one visible space before text.
local icon_spacing = "  "

local function glyph(icon, glyphs)
  icon = vim.trim(icon)
  if vim.fn.strchars(icon) ~= 1 then
    return icon
  end
  local codepoint = (glyphs or icons.glyphs)[tostring(vim.fn.char2nr(icon))]
  return codepoint and vim.fn.nr2char(codepoint) or icon
end

local function compact_glyph(icon)
  return glyph(glyph(icon), icons.compact)
end

local function compact_menu_icon(icon)
  local replacement = compact_glyph(icon)
  -- The menu's column gap supplies the visible space after the second glyph cell.
  return replacement ~= vim.trim(icon) and replacement .. " " or icon
end

local function colored_icon(filetype)
  local codepoint = icons.filetypes[filetype]
  return codepoint and vim.fn.nr2char(codepoint)
end

local function filetype_icon(component)
  local filetype = vim.bo.filetype
  local colored = colored_icon(filetype)
  if colored then
    return colored .. icon_spacing
  end

  local devicons = require("nvim-web-devicons")
  local icon, highlight = devicons.get_icon(vim.fn.expand("%:t"))
  if not icon then
    icon, highlight = devicons.get_icon_by_filetype(filetype)
  end
  icon = icon or ""
  if not filetype:match("^git") then
    icon = glyph(icon)
  end
  return LazyVim.lualine.format(component, icon .. icon_spacing, highlight or "DevIconDefault")
end

return {
  {
    "folke/snacks.nvim",
    opts = function(_, opts)
      local dashboard = opts.dashboard
      if type(dashboard) == "table" then
        local keys = vim.tbl_get(dashboard, "preset", "keys")
        if type(keys) == "table" then
          for _, item in ipairs(keys) do
            if type(item.icon) == "string" then
              item.icon = compact_menu_icon(item.icon)
            end
          end
        end
        dashboard.sections = dashboard.sections or {
          { section = "header" },
          { section = "keys", gap = 1, padding = 1 },
          { section = "startup", icon = compact_glyph("⚡") .. icon_spacing },
        }
      end

      opts.picker = vim.tbl_deep_extend("keep", opts.picker or {}, {
        formatters = { file = { icon_width = 3 } },
        icons = {},
      })
      local defaults = require("snacks.picker.config.defaults").defaults.icons
      for _, category in ipairs({ "diagnostics", "kinds", "keymaps" }) do
        local configured = opts.picker.icons[category] or {}
        opts.picker.icons[category] = vim.tbl_map(compact_menu_icon, vim.tbl_extend("force", defaults[category], configured))
      end

      -- All Snacks sources that show paths share this formatter.
      local format = require("snacks.picker.format")
      local filename = format.filename
      format.filename = function(item, picker)
        local segments = filename(item, picker)
        local icon = segments[1]
        if item.file and picker.opts.icons.files.enabled ~= false and icon and icon.virtual then
          local filetype = not item.dir and vim.filetype.match({ filename = item.file })
          local colored = filetype and colored_icon(filetype)
          if colored then
            icon[1], icon[2] = compact_glyph(colored), nil
          elseif not filetype or not filetype:match("^git") then
            icon[1] = compact_glyph(icon[1])
          end
          local width = math.max(3, picker.opts.formatters.file.icon_width or 3)
          icon[1] = Snacks.picker.util.align(icon[1], width)
        end
        return segments
      end
    end,
  },
  {
    "saghen/blink.cmp",
    optional = true,
    opts = function(_, opts)
      local draw = opts.completion.menu.draw
      draw.components = draw.components or {}
      local kind_icon = draw.components.kind_icon or {}
      local defaults = require("blink.cmp.config.completion.menu").default.draw.components
      local text = kind_icon.text or defaults.kind_icon.text
      kind_icon.text = function(ctx)
        local icon = text(ctx)
        return vim.fn.getcmdtype() == ":" and compact_menu_icon(icon) or icon
      end
      draw.components.kind_icon = kind_icon
    end,
  },
  {
    "folke/which-key.nvim",
    opts = function()
      -- Which-key trims ASCII padding before adding its own column gap.
      local glyph_cell = " "
      local module = require("which-key.icons")
      local get_icon = module.get_icon
      module.get_icon = function(spec)
        local icon, highlight = get_icon(spec)
        local filetype = type(spec) == "string" and spec or spec.cat == "filetype" and not spec.icon and spec.name
        if filetype and filetype:match("^git") then
          return icon, highlight
        end
        local colored = filetype and colored_icon(filetype)
        if colored then
          return compact_glyph(colored) .. glyph_cell, highlight
        end
        if icon then
          local replacement = compact_glyph(icon)
          if replacement ~= vim.trim(icon) then
            return replacement .. glyph_cell, highlight
          end
        end
        return icon, highlight
      end

      local view = require("which-key.view")
      local format = view.format
      view.format = function(lhs)
        return (format(lhs):gsub("[\194-\244][\128-\191]+", function(char)
          local replacement = compact_glyph(char)
          if replacement ~= char then
            return replacement .. glyph_cell
          end
        end))
      end
    end,
  },
  {
    "akinsho/bufferline.nvim",
    opts = function(_, opts)
      local options = opts.options
      local get_element_icon = options.get_element_icon
      options.get_element_icon = function(element)
        local icon, highlight
        if get_element_icon then
          icon, highlight = get_element_icon(element)
        end
        if options.show_buffer_icons == false or icon == "" then
          return icon, highlight
        end
        local filetype = element.filetype
        if filetype == "" and element.path ~= "" and not element.directory then
          filetype = vim.filetype.match({ filename = element.path }) or ""
        end
        if filetype:match("^git") then
          return icon, highlight
        end

        -- Bufferline adds the visible space before the filename.
        local colored = colored_icon(filetype)
        if colored then
          return compact_glyph(colored) .. " "
        end
        if not icon then
          if element.directory then
            icon, highlight = "󰉋", "Directory"
          else
            local ok, devicons = pcall(require, "nvim-web-devicons")
            if ok then
              local name = vim.fn.fnamemodify(element.path, ":t")
              icon, highlight = devicons.get_icon(name, nil, { default = true })
            end
          end
        end
        if not icon then
          return
        end
        local replacement = compact_glyph(icon)
        return replacement ~= vim.trim(icon) and replacement .. " " or icon, highlight
      end

      local diagnostics_indicator = options.diagnostics_indicator
      if diagnostics_indicator then
        options.diagnostics_indicator = function(...)
          local indicator = diagnostics_indicator(...)
          return (indicator:gsub("(%S+) +(%d+)", function(icon, count)
            local replacement = compact_glyph(icon)
            if replacement ~= icon then
              return replacement .. icon_spacing .. count
            end
          end))
        end
      end
    end,
  },
  {
    "nvim-lualine/lualine.nvim",
    opts = function(_, opts)
      local left = opts.sections.lualine_c
      -- LazyVim supplies the second space after the root icon.
      left[1] = LazyVim.lualine.root_dir({ icon = glyph("󱉭") .. " " })

      for severity, icon in pairs(left[2].symbols) do
        left[2].symbols[severity] = glyph(icon) .. icon_spacing
      end

      if opts.options.icons_enabled ~= false then
        left[3] = { filetype_icon, separator = "", padding = { left = 1, right = 0 } }
        left[4].padding = { left = 0, right = 1 }
      end
      -- The path component's right padding supplies the second space.
      left[4][1] = LazyVim.lualine.pretty_path({ readonly_icon = " " .. glyph("󰌾") .. " " })

      if left[5] and vim.g.trouble_lualine and LazyVim.has("trouble.nvim") then
        left[5].fmt = function(status)
          -- Trouble wraps each breadcrumb icon in its own highlight.
          return status:gsub("(%%#TroubleStatusline%d+#)(.-)(%%%*)", function(open, text, close)
            local icon = glyph(text)
            if icon ~= vim.trim(text) then
              return open .. icon .. icon_spacing .. close
            end
          end)
        end
      end

      local clock = glyph("")
      opts.sections.lualine_z[1] = function()
        return clock .. icon_spacing .. os.date("%R")
      end
    end,
  },
}
