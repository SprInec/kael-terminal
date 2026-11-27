return {
  { "LazyVim/LazyVim", opts = { colorscheme = "catppuccin-mocha" } },
  {
    "neovim/nvim-lspconfig",
    opts = function(_, opts)
      local executables = {
        clangd = "clangd",
        pyright = "pyright-langserver",
        lua_ls = "lua-language-server",
        ruff = "ruff",
      }
      for server, executable in pairs(executables) do
        if vim.fn.executable(executable) == 1 then
          opts.servers[server].mason = false
        end
      end
    end,
  },
  {
    "mason-org/mason.nvim",
    opts = function(_, opts)
      opts.ensure_installed = vim.tbl_filter(function(tool)
        return vim.fn.executable(tool) == 0
      end, opts.ensure_installed or {})
      if vim.fn.executable("clang-format") == 0 then
        table.insert(opts.ensure_installed, "clang-format")
      end
    end,
  },
  {
    "stevearc/conform.nvim",
    opts = {
      formatters_by_ft = {
        c = { "clang_format" },
        cpp = { "clang_format" },
        lua = { "stylua" },
        python = { "ruff_format" },
      },
    },
  },
}
