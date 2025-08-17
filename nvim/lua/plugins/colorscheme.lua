return {
  "catppuccin/nvim",
  name = "catppuccin",
  priority = 1000,
  -- enabled = false,
  config = function()
    require("catppuccin").setup({
      flavour = "frappe",
      integrations = {
       gitsigns = true,
       nvimtree = true,
      }
    })
    vim.cmd.colorscheme("catppuccin")
  end
}
