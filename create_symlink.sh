#!/bin/sh

# get script located dir
DIR=$(cd $(dirname $0);pwd)

set -e
set -x

# zsh
install -d ~/.zsh
ln -sf $DIR/shell/.zshrc ~/.zshrc
ln -sf $DIR/shell/.zshrc-peco ~/.zshrc-peco
ln -sf $DIR/shell/.zshrc-fzf ~/.zshrc-fzf
ln -shf $DIR/shell/functions ~/.zsh/

install -d ~/.oh-my-zsh/themes
ln -sf $DIR/shell/zsh-theme/my-dpoggi.zsh-theme ~/.oh-my-zsh/themes/

# git
ln -sf $DIR/git/.gitconfig ~/.gitconfig
ln -sf $DIR/git/.gitconfig_commit_template ~/.gitconfig_commit_template
ln -sf $DIR/git/.gitignore_global ~/.gitignore_global

install -d ~/.git_templates/hooks
ln -sf $DIR/git/.git_templates/hooks/post-checkout ~/.git_templates/hooks/post-checkout

# peco
install -d ~/.peco
ln -sf $DIR/terminal/peco/config.json ~/.peco/config.json

# tig
ln -sf $DIR/terminal/tig/.tigrc ~/.tigrc

# tmux
install -d ~/.tmux-powerline/themes
ln -sf $DIR/terminal/tmux/.tmux.conf ~/.tmux.conf
ln -sf $DIR/terminal/tmux/.tmux-powerlinerc ~/.tmux-powerlinerc
ln -sf $DIR/terminal/tmux/mytheme.sh ~/.tmux-powerline/themes/mytheme.sh

# vifm
install -d ~/.vifm
ln -sf $DIR/terminal/vifm/vifmrc ~/.vifm/vifmrc

# lesskey
ln -sf $DIR/terminal/less/.lesskey ~/.lesskey

# aspell
ln -sf $DIR/tool/aspell/.aspell.conf ~/.aspell.conf

# GNU global
ln -sf $DIR/tool/global/.globalrc ~/.globalrc

# Gradle
install -d ~/.gradle
ln -sf $DIR/tool/gradle/gradle.properties ~/.gradle/gradle.properties

# vim
ln -sf $DIR/vim/.vimrc ~/.vimrc

# script
install -d ~/bin
# https://developer.atlassian.com/blog/2015/03/emacs-intellij/
ln -sf $DIR/script/openinemacs ~/bin/openinemacs
# https://www.iterm2.com/documentation-images.html
ln -sf $DIR/script/imgls ~/bin/imgls
# https://qiita.com/kiritex/items/786dbed4b7a2a22cbb89
ln -sf $DIR/script/imgcat_tmux ~/bin/imgcat
# convert snake_case to UpperCamelCase or lowerCamelCase
ln -sf $DIR/script/_2U ~/bin/_2U
ln -sf $DIR/script/_2l ~/bin/_2l
ln -sf $DIR/script/c2_ ~/bin/c2_
