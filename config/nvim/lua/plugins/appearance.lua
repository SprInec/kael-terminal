return {
  {
    "catppuccin/nvim",
    opts = {
      flavour = "mocha",
      -- Match the status line and active pane colors in ~/.config/tmux/status.conf.
      color_overrides = {
        mocha = {
          rosewater = "#e4cbb8",
          flamingo = "#e1b8ac",
          pink = "#d5b1c4",
          mauve = "#c1b0cc",
          red = "#e6a091",
          maroon = "#d39388",
          peach = "#dfb17e",
          yellow = "#d7c183",
          green = "#a5bb8b",
          teal = "#9cba9f",
          sky = "#a9c7b5",
          sapphire = "#86ab98",
          blue = "#b1e969",
          lavender = "#c1d88a",
          text = "#dce5d3",
          subtext1 = "#c2cdb8",
          subtext0 = "#aebba3",
          overlay2 = "#a0ad95",
          overlay1 = "#929e85",
          overlay0 = "#7f8d72",
          surface2 = "#48533e",
          surface1 = "#3b452c",
          surface0 = "#293322",
          base = "#171717",
          mantle = "#141913",
          crust = "#10140f",
        },
      },
      custom_highlights = function(colors)
        return {
          Normal = { bg = colors.base },
          NormalNC = { bg = colors.base },
          WinSeparator = { fg = colors.surface2 },
          StatusLine = { fg = colors.text, bg = colors.base },
          StatusLineNC = { fg = colors.overlay1, bg = colors.base },
        }
      end,
      integrations = {
        lualine = {
          mocha = function(colors)
            return {
              normal = {
                a = { fg = "#17210f" },
                c = { bg = colors.base },
              },
            }
          end,
        },
      },
    },
  },
  { "sphamba/smear-cursor.nvim", event = "VeryLazy", opts = {} },
}
