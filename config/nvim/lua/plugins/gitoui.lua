local function open_gitoui(cwd)
  local gitoui = vim.fn.exepath("gitoui")
  if gitoui == "" then
    vim.notify("Gitoui is not on PATH", vim.log.levels.WARN)
    return
  end

  local socket = (vim.env.TMUX or ""):match("^(.+),%d+,%d+$")
  local pane = vim.env.TMUX_PANE
  if socket and pane and pane:match("^%%%d+$") then
    local data = vim.env.XDG_DATA_HOME or vim.fn.expand("~/.local/share")
    local tmux = vim.env.KAEL_TMUX_BIN or (data .. "/kael-terminal/bin/tmux")
    if vim.fn.executable(tmux) ~= 1 then
      tmux = vim.fn.exepath("tmux")
    end
    if tmux ~= "" then
      local report = vim.system({
        tmux, "-S", socket, "display-message", "-p", "-t", pane,
        "#{sixel_support} #{session_id}:#{window_id} #{client_termfeatures}",
      }, { text = true, timeout = 1000 }):wait()
      local target, features = (report.stdout or ""):match("^1 (%$%d+:@%d+) ([^\n]+)")
      if report.code == 0 and target and vim.tbl_contains(vim.split(features, ","), "sixel") then
        -- A tmux window lets the outer terminal draw Gitoui's Sixel images.
        local launched = vim.system({
          tmux, "-S", socket, "new-window", "-a", "-t", target,
          "-n", "Gitoui", "-c", cwd, "--", gitoui, "--graph-renderer=sixel",
        }, { text = true, timeout = 1000 }):wait()
        if launched.code == 0 then
          return
        end
      end
    end
  end

  Snacks.terminal({ gitoui, "--graph-renderer=ascii" }, { cwd = cwd })
end

return {
  {
    "folke/snacks.nvim",
    keys = function(_, keys)
      if vim.fn.executable("gitoui") ~= 1 then
        return
      end
      return vim.list_extend(keys, {
        {
          "<leader>gg",
          function()
            open_gitoui(LazyVim.root.git())
          end,
          desc = "Gitoui (Root Dir)",
        },
        {
          "<leader>gG",
          function()
            open_gitoui(vim.fn.getcwd(0))
          end,
          desc = "Gitoui (cwd)",
        },
      })
    end,
  },
}
