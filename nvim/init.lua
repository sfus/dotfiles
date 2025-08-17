-- https://tech.aptpod.co.jp/entry/2024/12/24/110000
-- https://zenn.dev/vim_jp/articles/1b4344e41b9d5b
-- https://zenn.dev/forcia_tech/articles/202411_deguchi_neovim

vim.g.mapleader = " "
vim.opt.number = true
vim.opt.clipboard = "unnamedplus"

vim.keymap.set("n", "<leader>Q", "<cmd>qa!<CR>", { silent = true, desc = "Quit ALL (force)" })
vim.keymap.set("i", "jk", "<Esc>")
vim.keymap.set('n', ';', ':', {silent=true})

-- Move Tab
vim.keymap.set("n", "<PageUp>", "<cmd>bprev<CR>")
vim.keymap.set("n", "<PageDown>", "<cmd>bnext<CR>")

-- Move Window
vim.keymap.set('n', '<C-l>', '<C-w>l')
vim.keymap.set('n', '<C-h>', '<C-w>h')
vim.keymap.set('n', '<C-j>', '<C-w>j')
vim.keymap.set('n', '<C-k>', '<C-w>k')

-- Open a bottom terminal while keeping nvim-tree on the left
vim.keymap.set("n", "<leader>te", function()
  -- If you're in NvimTree, move to the right window first
  if vim.bo.filetype == "NvimTree" then
    vim.cmd("wincmd l")
  end
  -- Open a 15-line terminal at the bottom
  vim.cmd("botright 15split | terminal")
  -- Make the terminal nicer
  vim.opt_local.number = false
  vim.opt_local.relativenumber = false
  vim.cmd("startinsert")  -- jump straight into the shell
end, { desc = "Open bottom terminal" })

-- Terminal-mode: go to the window ABOVE
vim.keymap.set('t', '<C-k>', [[<C-\><C-n><C-w>k]], { silent = true, desc = 'Terminal: focus window above' })
vim.keymap.set('t', '<C-h>', [[<C-\><C-n><C-w>h]], { silent = true, desc = 'Terminal: focus left window' })
vim.keymap.set('t', '<C-j>', [[<C-\><C-n><C-w>j]], { silent = true, desc = 'Terminal: focus below window' })
vim.keymap.set('t', '<C-l>', [[<C-\><C-n><C-w>l]], { silent = true, desc = 'Terminal: focus right window' })

-- Only in terminal *insert/job* mode: make <C-h> work as Backspace.
vim.api.nvim_create_autocmd("TermOpen", {
  pattern = "term://*",
  callback = function(ev)
    -- Clean up any prior terminal-local mappings for <C-h>
    pcall(vim.keymap.del, "t", "<C-h>", { buffer = ev.buf })
    pcall(vim.keymap.del, "n", "<C-h>", { buffer = ev.buf }) -- ensure no local normal override

    -- t-mode (terminal job mode) only
    vim.keymap.set("t", "<C-h>", "<BS>", {
      buffer = ev.buf,
      noremap = true,
      silent = true,
      desc = "Terminal(t): Backspace",
    })
  end,
})

-- Exit terminal-insert quickly with <Esc>
vim.keymap.set('t', '<Esc>', [[<C-\><C-n>]], { silent = true, desc = 'Terminal: enter Normal mode' })

require("config.lazy")