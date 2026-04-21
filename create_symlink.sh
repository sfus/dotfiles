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

install -d ~/.oh-my-zsh/themes
ln -sf $DIR/shell/zsh-theme/my-dpoggi.zsh-theme ~/.oh-my-zsh/themes/

# git
ln -sf $DIR/git/.gitconfig ~/.gitconfig
ln -sf $DIR/git/.gitconfig_commit_template ~/.gitconfig_commit_template
ln -sf $DIR/git/.gitignore_global ~/.gitignore_global

install -d ~/.git_templates/hooks
ln -sf $DIR/git/.git_templates/hooks/post-checkout ~/.git_templates/hooks/post-checkout
ln -sf $DIR/git/.git_templates/hooks/commit-msg ~/.git_templates/hooks/commit-msg

# peco
install -d ~/.peco
ln -sf $DIR/terminal/peco/config.json ~/.peco/config.json

# tig
ln -sf $DIR/terminal/tig/.tigrc ~/.tigrc

# tmux
install -d ~/.config/tmux-powerline/themes
ln -sf $DIR/terminal/tmux/.tmux.conf ~/.tmux.conf
ln -sf $DIR/terminal/tmux/.tmux-powerlinerc ~/.config/tmux-powerline/config.sh
ln -sf $DIR/terminal/tmux/mytheme.sh ~/.config/tmux-powerline/themes/mytheme.sh

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

# k9s
# ($ k9s info)
install -d ~/Library/Application\ Support/k9s
ln -sf $DIR/terminal/k9s/hotkeys.yaml ~/Library/Application\ Support/k9s/hotkeys.yaml


# script
install -d ~/.local/bin
# https://developer.atlassian.com/blog/2015/03/emacs-intellij/
ln -sf $DIR/script/openinemacs ~/.local/bin/openinemacs
# https://www.iterm2.com/documentation-images.html
ln -sf $DIR/script/imgls ~/.local/bin/imgls
# https://qiita.com/kiritex/items/786dbed4b7a2a22cbb89
ln -sf $DIR/script/imgcat_tmux ~/.local/bin/imgcat
# convert snake_case to UpperCamelCase or lowerCamelCase
ln -sf $DIR/script/_2U ~/.local/bin/_2U
ln -sf $DIR/script/_2l ~/.local/bin/_2l
ln -sf $DIR/script/c2_ ~/.local/bin/c2_
ln -sf $DIR/script/c2_ ~/.local/bin/c2_

ln -sf $DIR/script/claude_usage.py ~/.local/bin/claude-usage
ln -sf $DIR/script/cursor_usage.py ~/.local/bin/cursor-usage
