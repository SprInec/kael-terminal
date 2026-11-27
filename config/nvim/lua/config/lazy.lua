local plugin_dir = vim.fn.stdpath("data") .. "/lazy"
local lazypath = plugin_dir .. "/lazy.nvim"
local entrypoint = lazypath .. "/lua/lazy/init.lua"

if not vim.uv.fs_stat(entrypoint) then
  vim.fn.mkdir(plugin_dir, "p")
  local staging = assert(vim.uv.fs_mkdtemp(plugin_dir .. "/.lazy.nvim-XXXXXX"))
  local result = vim.system({
    "git",
    "clone",
    "--filter=blob:none",
    "--branch=stable",
    "https://github.com/folke/lazy.nvim.git",
    staging,
  }, { text = true }):wait()

  local installed, rename_error
  if result.code == 0 then
    installed, rename_error = vim.uv.fs_rename(staging, lazypath)
  end
  if not installed then
    vim.fn.delete(staging, "rf")
    if not vim.uv.fs_stat(entrypoint) then
      local detail = rename_error or vim.trim(result.stderr or "")
      vim.api.nvim_err_writeln("Could not install lazy.nvim\n" .. detail)
      vim.cmd.cquit()
      return
    end
  end
end

vim.opt.rtp:prepend(lazypath)
require("lazy").setup({
  spec = {
    { "LazyVim/LazyVim", import = "lazyvim.plugins" },
    { import = "lazyvim.plugins.extras.coding.mini-surround" },
    { import = "lazyvim.plugins.extras.lang.clangd" },
    { import = "lazyvim.plugins.extras.lang.python" },
    { import = "plugins" },
  },
  install = { colorscheme = { "tokyonight", "habamax" } },
  checker = { enabled = true, notify = false },
})
