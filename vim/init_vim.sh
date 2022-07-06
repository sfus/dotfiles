#!/bin/sh

VUNDLE_DIR=~/.vim/bundle/Vundle.vim

if [ ! -e $VUNDLE_DIR ]; then
  git clone https://github.com/VundleVim/Vundle.vim.git "$VUNDLE_DIR"
  vim +PluginInstall +qall
fi
