autocmd!

syntax on
set ignorecase
set notitle
set showmatch
set noautoindent
set nobackup
filetype on
filetype indent on
filetype plugin on

set visualbell
set vb t_vb=

set tabstop=8
set expandtab

set laststatus=2
set statusline=%<%f\ %m%r%h%w%{'['.(&fenc!=''?&fenc:&enc).']['.&ff.']'}%=%l,%c%V%8P

syntax on
set term=xterm-256color
set t_Co=256

autocmd FileType * setlocal formatoptions-=ro

set ambiwidth=double

" https://github.com/VundleVim/Vundle.vim
set nocompatible              " be iMproved, required
filetype off                  " required

set rtp+=~/.vim/bundle/Vundle.vim/
call vundle#begin()

Plugin 'VundleVim/Vundle.vim'
Plugin 'vifm/vifm.vim'

call vundle#end()            " required
filetype plugin indent on    " required
