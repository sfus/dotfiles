-- https://zenn.dev/vim_jp/articles/1b4344e41b9d5b
-- https://qiita.com/Tsuyopon-1067/items/54bdfb5a24e62d1627ea

-- Open nvim-tree by default, but keep focus on the file when a filename was given.
local function open_nvim_tree_on_start(data)
  local api = require("nvim-tree.api")

  -- Detect cases
  local is_dir   = vim.fn.isdirectory(data.file) == 1
  local no_name  = (data.file == "" and vim.bo[data.buf].buftype == "")

  if is_dir then
    -- Started with a directory: cd into it and open the tree (focus stays in tree)
    vim.cmd.cd(data.file)
    api.tree.open()
    return
  end

  if no_name then
    -- Started without a file (empty buffer): just open the tree
    api.tree.open()
    return
  end

  -- Started with a filename: open the tree but keep focus on the file window
  local file_win = vim.api.nvim_get_current_win()   -- remember current (file) window
  api.tree.open()                                   -- open tree on the side
  pcall(vim.cmd, "NvimTreeFindFile")                -- reveal the file in the tree (ignore errors)
  if vim.api.nvim_win_is_valid(file_win) then       -- restore focus to the file window
    vim.api.nvim_set_current_win(file_win)
  end
end

vim.api.nvim_create_autocmd("VimEnter", {
  callback = open_nvim_tree_on_start,
})

-- l key to opendir/closedir/preview
-- h key to closedir/updir
local function my_on_attach(bufnr)
  local api = require("nvim-tree.api")
  local function opts(desc)
    return { desc = "nvim-tree: " .. desc, buffer = bufnr, noremap = true, silent = true, nowait = true }
  end

  -- 1) Load default mappings first (<CR> will open the file)
  api.config.mappings.default_on_attach(bufnr)

  -- 2) Keep <CR> behavior explicit (open/edit)
  vim.keymap.set("n", "<CR>", api.node.open.edit, opts("Open"))

  -- 3) `l`: open directory; if file, preview (keep focus in the tree)
  vim.keymap.set("n", "l", function()
    local node = api.tree.get_node_under_cursor()
    if not node then return end
    if node.type == "directory" or node.nodes ~= nil then
      api.node.open.edit()      -- expand/open directory
    else
      api.node.open.preview()   -- preview file (focus stays in tree)
    end
  end, opts("Open dir / Preview file"))

  -- 4) `h`: go to parent; at root, change root to its parent (go up one level)
  vim.keymap.set("n", "h", function()
    local node = api.tree.get_node_under_cursor()
    if node and node.parent ~= nil then
      api.node.navigate.parent_close()  -- move to parent and collapse
    else
      api.tree.change_root_to_parent()  -- at root: go up directory
    end
  end, opts("Up (parent) / Change root up"))
end

-- PageDown/PageUp to next/previous buffer
vim.api.nvim_create_autocmd("FileType", {
  pattern = "NvimTree",
  callback = function(ev)
    local function safe_return_to(winid)
      if winid and vim.api.nvim_win_is_valid(winid) then
        vim.api.nvim_set_current_win(winid)
      end
    end

    -- PageDown: go to right window, :bnext, then return to NvimTree
    vim.keymap.set("n", "<PageDown>", function()
      -- remember current (NvimTree) window at press-time
      local tree_win = vim.api.nvim_get_current_win()

      -- go right; if there's no right window, do nothing
      vim.cmd("wincmd l")
      local cur = vim.api.nvim_get_current_win()
      if cur == tree_win then
        -- no right window; just return (nothing to do)
        return
      end

      -- try :bnext; if it fails (no other buffers), ignore
      pcall(vim.cmd, "bnext")

      -- return to NvimTree safely
      safe_return_to(tree_win)
    end, { buffer = ev.buf, silent = true, desc = "NvimTree: bnext in right win then return" })

    -- PageUp: go to right window, :bprev, then return to NvimTree
    vim.keymap.set("n", "<PageUp>", function()
      local tree_win = vim.api.nvim_get_current_win()

      vim.cmd("wincmd l")
      local cur = vim.api.nvim_get_current_win()
      if cur == tree_win then
        return
      end

      pcall(vim.cmd, "bprev")

      safe_return_to(tree_win)
    end, { buffer = ev.buf, silent = true, desc = "NvimTree: bprev in right win then return" })
  end,
})

return {
  "nvim-tree/nvim-tree.lua",
  version = "*",
  lazy = false,
  dependencies = {
    "nvim-tree/nvim-web-devicons",
  },
  keys = {
    {mode = "n", "<C-n>", "<cmd>NvimTreeToggle<CR>", desc = "NvimTreeをトグルする"},
    {mode = "n", "<C-m>", "<cmd>NvimTreeFocus<CR>", desc = "NvimTreeにフォーカス"},
  },
  config = function()
    require("nvim-tree").setup {
      on_attach = my_on_attach,
      git = {
        enable = true,
        ignore = true,
      }
    }
  end,
}
