-- Managed by kael-terminal.
if vim.fn.has("nvim-0.12") == 1 then
  require("config.lazy")
else
  vim.cmd("source " .. vim.fn.fnameescape(vim.fn.expand("~/.vimrc")))
end
