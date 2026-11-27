vim.g.autoformat = true
vim.opt.cmdheight = 0

-- Reuse language tools installed by the existing Neovim profile.
local nvim_mason_bin = vim.fn.stdpath("data") .. "/mason/bin"
if vim.fn.isdirectory(nvim_mason_bin) == 1 then
  vim.env.PATH = vim.env.PATH .. ":" .. nvim_mason_bin
end
