return {
  'akinsho/bufferline.nvim',
  version = "*",
  dependencies = 'nvim-tree/nvim-web-devicons',
  config = function ()
    vim.opt.termguicolors = true
    require("bufferline").setup{}
  end,
  -- Only set these mappings when bufferline is active
  vim.keymap.set("n", "<PageUp>", "<cmd>bprev<CR>", { desc = "Previous buffer (bufferline)" }),
  vim.keymap.set("n", "<PageDown>", "<cmd>bnext<CR>", { desc = "Next buffer (bufferline)" }),
}
