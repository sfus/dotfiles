""" Vim Settings

set nocompatible            " be improved

""
"" Basic Settings
""
set fenc=utf-8              " Encoding
set nobackup                " No backup when overwrite
set noswapfile              " No swap file on editting
set autoread                " Auto reload when the file is modified
set hidden                  " Enable to open another file when the buffer is not saved
set showcmd                 " Show command input on status bar
set whichwrap=b,s,h,l,<,>,[,],~ " Enable cursor move over line end (need `nocompatible' setting)

""
"" Visual Settings
""
set number                  " Show line numbers
set cursorline              " Highlight current row
" set cursorcolumn          " Highlight current column
set virtualedit=onemore     " Enable cursor to move the last column + 1
set smartindent             " Use smart indent (indent on carriage return)
set visualbell              " Use visual bell
set showmatch               " Show matched paren
set laststatus=2            " Always show status line
set wildmode=list:longest   " Complecation on command line with Tab key
set statusline=%<%f\ %m%r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=%l,%c%V%8P
syntax enable               " Enable syntax highlight


""
"" Tab Settings
""
set list listchars=tab:\▸\  " Enable visualize white space characters (tab to `▸ ')
set expandtab               " Expand tab to spaces
set tabstop=4               " Tab stop
set shiftwidth=4            " Tab width on line head


""
"" Search Settings
""
set ignorecase              " Ignore case sensitive search
set smartcase               " Enable case sensitive search when capital character is included
set incsearch               " Enable incremental search
set wrapscan                " Loop the first candidate when
set hlsearch                " Highlight the search word

" Exit highlight by <Esc><Esc>
nmap <Esc><Esc> :nohlsearch<CR><Esc>


""
"" Terminal Settings
""
set term=xterm-256color     " Enable 256 color
set t_Co=256                " Enable 256 color (duplicated)
set vb t_vb=                " Suppress beep sound
set noerrorbells            " Suppress beep sound on error
set ambiwidth=double        " Set ambiguous wide characters as double width


""
"" OS Settings
""
set clipboard=unnamed,unnamedplus   " Enable yank/put from OS clipboard without specifying register


""
"" Key Settings
""

" Swap colon and semi-colon
nnoremap ; :
nnoremap : ;

" Enable visual line move when the line is wrapped
nnoremap j gj
nnoremap k gk
nnoremap gj j
nnoremap gk k

""
"" VimDiff Settings
""
highlight DiffAdd    cterm=bold ctermfg=10 ctermbg=22
highlight DiffDelete cterm=bold ctermfg=10 ctermbg=52
highlight DiffChange cterm=bold ctermfg=10 ctermbg=17
highlight DiffText   cterm=bold ctermfg=10 ctermbg=21


""
"" Other Settings
""
autocmd FileType * setlocal formatoptions-=ro   " Disable auto comment out on carriage return in comment block


""
"" Vundle Settings
""

" https://github.com/VundleVim/Vundle.vim
" $ git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
" :PluginInstall or $ vim +PluginInstall +qall

"set nocompatible              " be iMproved, required
filetype off                  " required

" set the runtime path to include Vundle and initialize
set rtp+=~/.vim/bundle/Vundle.vim/
call vundle#begin()

" let Vundle manage Vundle, required
Plugin 'VundleVim/Vundle.vim'

" Keep Plugin commands between vundle#begin/end.
Plugin 'vifm/vifm.vim'

" All of your Plugins must be added before the following line
call vundle#end()            " required
filetype plugin indent on    " required


""
"" References
""

" https://qiita.com/morikooooo/items/9fd41bcd8d1ce9170301
" https://qiita.com/iwaseasahi/items/0b2da68269397906c14c
" http://vimblog.hatenablog.com/entry/vimrc_set_recommended_options
