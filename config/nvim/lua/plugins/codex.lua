return {
  {
    "folke/sidekick.nvim",
    cmd = "Sidekick",
    opts = {
      nes = { enabled = false },
      cli = {
        mux = { backend = "tmux", enabled = vim.fn.executable("tmux") == 1 },
      },
    },
    keys = {
      {
        "<leader>aa",
        function()
          require("sidekick.cli").toggle({ name = "codex" })
        end,
        desc = "Toggle Codex",
      },
      {
        "<leader>af",
        function()
          require("sidekick.cli").send({ name = "codex", msg = "{file}" })
        end,
        desc = "Send File to Codex",
      },
      {
        "<leader>av",
        function()
          require("sidekick.cli").send({ name = "codex", msg = "{selection}" })
        end,
        mode = "x",
        desc = "Send Selection to Codex",
      },
    },
  },
}
