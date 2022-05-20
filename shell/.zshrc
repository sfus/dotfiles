bindkey -e

## how to install zplug
# -> https://github.com/zplug/zplug
# curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh

# zplug
source ~/.zplug/init.zsh
zplug 'zplug/zplug', hook-build:'zplug --self-manage'

# Async
zplug "mafredri/zsh-async"

# # Theme
# # -> https://github.com/sindresorhus/pure
# zplug "sindresorhus/pure"
# zstyle :prompt:pure:path color '#00ff00'
# zstyle :prompt:pure:git:branch color '#999999'
# zstyle :prompt:pure:prompt:success color '#00afd7'
# PURE_PROMPT_SYMBOL="%D{%H:%M} %F{#cccccc}❯%f"

# # -> https://github.com/Powerlevel9k/powerlevel9k
# # $ brew install font-noto-mono-for-powerline
# zplug "bhilburn/powerlevel9k", use:powerlevel9k.zsh-theme, as:theme
# #POWERLEVEL9K_VCS_GIT_HOOKS=(vcs-detect-changes git-untracked git-aheadbehind git-stash git-remotebranch git-tagname)
# POWERLEVEL9K_VCS_GIT_HOOKS=(vcs-detect-changes git-untracked git-aheadbehind git-remotebranch git-tagname)
# POWERLEVEL9K_SHORTEN_STRATEGY=truncate_middle
# POWERLEVEL9K_SHORTEN_DIR_LENGTH=3

# -> https://github.com/zsh-users/zsh-syntax-highlighting
# zsh-syntax-highlighting must be loaded
# after executing compinit command and sourcing other plugins
# (If the defer tag is given 2 or above, run after compinit command)
zplug "zsh-users/zsh-syntax-highlighting", defer:2

# -> https://github.com/zsh-users/zsh-history-substring-search
zplug "zsh-users/zsh-history-substring-search"
bindkey -M emacs '^P' history-substring-search-up
bindkey -M emacs '^N' history-substring-search-down

zplug "zsh-users/zsh-autosuggestions"

# -> https://github.com/zsh-users/zsh-completions
# -> https://qiita.com/sei40kr/items/bce00d4b875a7119fff8
zplug "zsh-users/zsh-completions", use:'src/_*', lazy:true
zstyle ':completion:*' insert-tab false

# -> https://github.com/chitoku-k/fzf-zsh-completions
zplug "chitoku-k/fzf-zsh-completions"

# oh-my-zsh plugins
# -> https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins
# zplug "plugins/git", from:oh-my-zsh
# zplug "plugins/docker", from:oh-my-zsh
# zplug "plugins/kubectl", from:oh-my-zsh
# zplug "plugins/gcloud", from:oh-my-zsh

# Others
zplug "chrissicool/zsh-256color"
# zplug "mrowa44/emojify", as:command

# Install plugins if there are plugins that have not been installed
if ! zplug check --verbose; then
  printf "Install? [y/N]: "
  if read -q; then
    echo; zplug install
  fi
fi

# source plugins and add commands to $PATH
zplug load
#zplug load --verbose


# fpath
fpath=(~/.zsh-completions /usr/local/share/zsh/site-functions $fpath)

# enable completion
autoload -Uz compinit
compinit -u

# # kubectl completion (after compinit)
# [[ $commands[kubectl] ]] && source <(kubectl completion zsh)


## PATH
PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
# diff-highlight
PATH="$PATH:/usr/local/share/git-core/contrib/diff-highlight"
# android-sdk
PATH="$PATH:/Applications/android-sdk-macosx/platform-tools"
# ~/bin
PATH="$HOME/bin:$PATH"
# cargo
PATH="$HOME/.cargo/bin:$PATH"
# icu4c
PATH="/usr/local/opt/icu4c/bin:$PATH"
PATH="/usr/local/opt/icu4c/sbin:$PATH"
# gnu-time
PATH="/usr/local/opt/gnu-time/libexec/gnubin:$PATH"
# td-agent
PATH="/opt/td-agent/embedded/bin:$PATH"

# for makepkg
PATH="/usr/local/opt/libarchive/bin:$PATH"
# For compilers to find this software you may need to set:
#     LDFLAGS:  -L/usr/local/opt/libarchive/lib
#     CPPFLAGS: -I/usr/local/opt/libarchive/include
# For pkg-config to find this software you may need to set:
#     PKG_CONFIG_PATH: /usr/local/opt/libarchive/lib/pkgconfig

export PATH

# Add local build *.so files after system ld library path
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH:$HOME/.local/lib"

# export MANPATH="/usr/local/man:$MANPATH"

# golang
GOPATH="$HOME/.go"
if [ -d $GOPATH ]; then
    export GOPATH
    export PATH="$GOPATH/bin:$PATH"
fi
GOROOT="/usr/local/opt/go/libexec"
if [ -e $GOROOT ]; then
    export GOROOT
    export PATH="$GOROOT/bin:$PATH"
fi

# # plenv
# PLENV_ROOT="$HOME/.plenv"
# if [ -d $PLENV_ROOT ]; then
#    export PLENV_ROOT
#    export PATH=$PLENV_ROOT/bin:$PATH
#    eval "$(plenv init -)"
# fi

# pyenv
# https://qiita.com/Kodaira_/items/feadfef9add468e3a85b
PYENV_ROOT="$HOME/.pyenv"
if [ -d $PYENV_ROOT ]; then
    export PYENV_ROOT
    export PATH=$PYENV_ROOT/bin:$PATH
    export PATH=$PYENV_ROOT/libexec:$PATH
    eval "$(pyenv init -)"
    # if [ -d "$PYENV_ROOT/plugins/pyenv-virtualenv" ]; then
    #     eval "$(pyenv virtualenv-init -)"
    # fi
fi

# for `brew doctor`
# https://qiita.com/takc923/items/45386905f70fde9af0e7
alias brew="env PATH=${PATH/$HOME\/\.pyenv\/shims:/} brew"

# # rbenv
# RBENV_ROOT="$HOME/.rbenv"
# if [ -d $RBENV_ROOT ]; then
#     export RBENV_ROOT
#     export PATH=$RBENV_ROOT/bin:$PATH
#     eval "$(rbenv init -)"
# fi

# # ndenv
# # https://github.com/riywo/ndenv
# NDENV_ROOT="$HOME/.ndenv"
# if [ -d $NDENV_ROOT ]; then
#     export NDENV_ROOT
#     export PATH=$NDENV_ROOT/bin:$PATH
#     eval "$(ndenv init -)"
# fi

# nodenv
# https://github.com/nodenv/nodenv
NODENV_ROOT="$HOME/.nodenv"
if [ -d $NODENV_ROOT ]; then
    export NODENV_ROOT
    export PATH=$NODENV_ROOT/bin:$PATH
    eval "$(nodenv init -)"
fi

# ## nodebrew
# NODEBREW_ROOT="$HOME/.nodebrew"
# if [ -d $NODEBREW_ROOT ]; then
#     export PATH=$NODEBREW_ROOT/current/bin:$PATH
# fi

export GRADLE_HOME=/usr/local/opt/gradle/libexec
export GRADLE_OPTS=-Dorg.gradle.daemon=false

# ## sdkman
SDKMAN_DIR="$HOME/.sdkman"
if [ -e "$SDKMAN_DIR/bin/sdkman-init.sh" ]; then
    export SDKMAN_DIR
    source "$SDKMAN_DIR/bin/sdkman-init.sh"
fi

## homebrew java
# #JAVA_VERSION=1.8
# JAVA_VERSION=11
# if [ -x /usr/libexec/java_home ]; then
#    export JAVA_HOME=`/usr/libexec/java_home -v $JAVA_VERSION`
# fi
# alias java-home-8='export JAVA_HOME=`/usr/libexec/java_home -v 1.8`'

# You may need to manually set your language environment
# export LANG=en_US.UTF-8
#export LC_ALL=C
export LANG=ja_JP.UTF-8

# gtags with pygments
# -> https://qiita.com/yoshizow/items/9cc0236ac0249e0638ff
# $ brew install global --with-ctags --with-pygments
# $ cat /usr/local/etc/gtags/gtags.conf
#export GTAGSLABEL=pygments


# enable zmv
# -> https://mollifier.hatenablog.com/entry/20101227/p1
# $ zmv *.txt file-*.txt
autoload -Uz zmv
alias zmv='noglob zmv -W'

# # ignore EOF (Ctrl+D)
# setopt IGNOREEOF

# word delimiter for Ctrl-w
#export WORDCHARS='*?_-.[]~=/&;!#$%^(){}<>'
export WORDCHARS='*?_.-[]~=&;!#$%^(){}<>'

# history size on memory
HISTSIZE=10000

# history size on save
SAVEHIST=100000

# share history in processes
setopt share_history

# append to history (not overwrite) for using multiple zsh simultaneously
setopt append_history

# delete dupulicated old history
setopt hist_ignore_all_dups

# ignore command history if command starts space
setopt hist_ignore_space

# enable to edit on history selection
setopt hist_verify

# reduce unnecessary spaces
setopt hist_reduce_blanks

# ignore duplicated command history
setopt hist_save_no_dups

# not store history command itself
setopt hist_no_store

# # expand history on completion
# setopt hist_expand

# append history incrementally
setopt inc_append_history

# enable auto-cd (`..' to parent dir, etc)
setopt auto_cd

# # incremental search
# bindkey "^R" history-incremental-search-backward
# bindkey "^S" history-incremental-search-forward

# cdr setting
# http://blog.n-z.jp/blog/2013-11-12-zsh-cdr.html
if [ ! -e "$HOME/.cache/shell" ]; then
  mkdir -p "$HOME/.cache/shell"
fi
if [[ -n $(echo ${^fpath}/chpwd_recent_dirs(N)) && -n $(echo ${^fpath}/cdr(N)) ]]; then
  autoload -Uz chpwd_recent_dirs cdr add-zsh-hook
  add-zsh-hook chpwd chpwd_recent_dirs
  zstyle ':completion:*:*:cdr:*:*' menu selection
  zstyle ':completion:*' recent-dirs-insert both
  zstyle ':chpwd:*' recent-dirs-max 500
  zstyle ':chpwd:*' recent-dirs-default true
  zstyle ':chpwd:*' recent-dirs-file "${XDG_CACHE_HOME:-$HOME/.cache}/shell/chpwd-recent-dirs"
  zstyle ':chpwd:*' recent-dirs-pushd true
fi

unset SSH_ASKPASS

# disable !{number} expansion
unsetopt hist_expand

# export MAVEN_OPTS=-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005

export PERL5_DEBUG_ROLE='server'
export PERL5_DEBUG_HOST=localhost
export PERL5_DEBUG_PORT=5004

export LESSCHARSET=utf-8

# https://qiita.com/phenan/items/1c60a1123612a55e76d5
# brew install less
# lesskey -o ~/.lesskey lesskey.conf
if [ -e "$HOME/.lesskey" ]; then
   export LESSKEY=~/.lesskey
fi

# send to clipboard for each platform
if which pbcopy >/dev/null 2>&1 ; then
    alias -g C='| pbcopy'
elif which xsel >/dev/null 2>&1 ; then
    # Linux
    alias -g C='| xsel --input --clipboard'
fi

alias ls='ls -G'
alias ll='ls -lG'
alias lla='ls -laG'
alias rm='rm -i'
alias cp='cp -i'

alias e='emacsclient -nw -a ""'
alias em='emacsclient -nw -a ""'
alias ekill='emacsclient -e "(kill-emacs)"'

# # Use emacsclient onclick `v' on less (or others)
# if [ -x '/usr/local/bin/emacsclient' ]; then
#    export VISUAL='emacsclient -nw -a ""'
# else
#    export VISUAL="vim"
# fi
export VISUAL="vim"

# alias pd=perldoc
alias pd=cpandoc -i
alias ce=carton exec

alias swagger-js='/usr/local/lib/node_modules/swagger/bin/swagger.js'
alias makerule='make -p -f /dev/null'

alias ht='htop'

alias d='docker'
alias doco='docker-compose'
alias lad='lazydocker'
alias k='kubectl'
alias kk='k9s'
alias kr='k9s --readonly'
alias kx='kubectx'
# for kustomize 3.9~
alias kus='kustomize --enable_kyaml=false'

alias g='git'
alias gi='git'
alias gst='git status'
alias gs='git status -s'
alias gss='git status -s'
alias gl='git --no-pager ll -20'
alias gll='git --no-pager ll -20'
alias gla='git --no-pager lla -20'
alias glla='git --no-pager lla -20'
alias ginit='git init && git commit --allow-empty -m "Initial revision"'
alias gsubi='git submodule update -i'
alias gr='git remote -v'
alias gw='git worktree'

alias t='tig'
alias ti='tig'
alias ta='tig --all'
alias td='tig develop master'
alias ref='git reflog --pretty=raw | tig --pretty=raw'

alias tm='tmux'
alias tma='tmux attach'
alias tml='tmux ls'
alias tmk='tmux kill-session -t'
alias tmz='tmux set-option -g prefix C-z'

alias slog='svn log'
alias sll='svn log -v -l 5'
alias sdi='svn diff'
alias srev='svn revert'
alias sst='svn status'
alias sup='svn update'

alias lc='leetcode'
alias lcgen='leetcode show -g -x'


# requires GNU sed, `brew install gsed` to install
alias c2s="gsed -r 's/([A-Z])/_\L\1/g'"
alias s2C="gsed -r 's/(^|_)([a-z])/\U\2/g'"
alias s2c="gsed -r 's/(^|_)([a-z])/\U\2/g' | gsed -r 's/^(.)/\l\1/g'"

alias base=base64

function bd () {
  echo -n $1 | base64 -D
}

function tmm () {
  if [ "$#" -eq 0 ]; then
    tmux split-window -v -p 30 -c "#{pane_current_path}"
    tmux select-pane -t 0
  else
    case $1 in
      .)
        tmux split-window -v -p 30 -c "#{pane_current_path}"
        tmux split-window -h -c "#{pane_current_path}"
        tmux select-pane -t 0
        ;;
      /)
        tmux split-window -h -c "#{pane_current_path}"
        tmux split-window -v -c "#{pane_current_path}"
        tmux select-pane -t 0
        ;;
      *)
        echo [ERROR] "$1": undefined argument
        ;;
    esac
  fi
}

function svn-commit-id-pair () {
    if [ $# -lt 1 ]; then return 1; fi
    NUM=$1
    NEXT=$(( $NUM + 1 ))
    svn log -l ${NEXT} | awk '/^r[0-9]+/ { print $1 }' | sed -n ${NUM},${NEXT}p | xargs
}

function sdiff () {
    if [ $# -lt 1 ]; then
        echo $(basename `pwd`)
        echo "$ svn diff"
        echo '```diff'
        svn diff
        RESULT=$?
        echo '```'
        return $RESULT
    fi
    svn-commit-id-pair $* | awk 'system("echo svn diff -r "$2":"$1" && svn diff -r "$2":"$1)'
}

function srevert () {
    if [ $# -lt 2 ]; then
        echo "USAGE: srevert NUMBER TARGET"
        return 1
    fi
    TARGET=" $2"
    svn-commit-id-pair $* | awk -v target=$TARGET 'system("echo svn merge -r "$1":"$2 target" && svn merge -r "$1":"$2 target)'
}

alias aplay='ansible-playbook'
alias ainit='ansible-galaxy init --init-path="roles"'

# tmux-xpanes(xpanes)
# http://qiita.com/greymd/items/8744d1c4b0b2b3004147
# $ brew tap greymd/tools
# $ brew install tmux-xpanes
# $ xpanes -c 'command {}' {1..5}
alias xp='tmux-xpanes'

alias conv8='convert -strip -verbose -quality 96 -resize 800x'
alias mog8='mogrify -strip -verbose -quality 96 -resize 800x'

# http://qiita.com/itkrt2y/items/0671d1f48e66f21241e2
#alias g='cd $(ghq root)/$(ghq list | peco)'
alias gh='hub browse $(ghq list | peco | cut -d "/" -f 2,3)'

# echo Ctrl-V Esc c (echo ^[c) ≒ reset
# http://orangeclover.hatenablog.com/entry/20110201/1296511181
alias clear2="echo -e '\026\033c'"

# tree
# https://qiita.com/yone098@github/items/bba8a42de6b06e40983b
alias tree="pwd;find . | sort | sed '1d;s/^\.//;s/\/\([^/]*\)$/|--\1/;s/\/[^/|]*/| /g'"

function dosh() {
    if [ $# -lt 1 ]; then
        echo "USAGE: dosh DOCKER-NAME"
        echo ""
        docker ps -a
        return
    fi
    docker exec -it $1 /bin/bash
}

function my-help-maven() {
  if [ $# -lt 2 ]; then
    mvn help:describe -Dplugin=$1 -Dfull=true
  else
    mvn help:describe -Dplugin=$1 -Dmojo=$2 -Dfull=true
  fi
}
alias mhelp=my-help-maven

# open pull-request from commit id
# http://techlife.cookpad.com/entry/2015/11/17/151426
function open-pull-request () {
    target_branch=develop
    merge_commit=$(ruby -e 'print (File.readlines(ARGV[0]) & File.readlines(ARGV[1])).last' <(git rev-list --ancestry-path $1..$target_branch) <(git rev-list --first-parent $1..$target_branch))
    if git show $merge_commit | grep -q 'pull request'
    then
        pull_request_number=$(git log -1 --format=%B $merge_commit | sed -e 's/^.*#\([0-9]*\).*$/\1/' | head -1)
        url="`hub browse -u`/pull/${pull_request_number}"
    fi
    open $url
}

# check conflicted commit by git rebase
# http://labs.timedia.co.jp/2015/05/show-what-commit-is-conflicted-while-git-rebase.html
function show-conflict() {
    f="$(git rev-parse --git-dir)/rebase-apply/patch"
    if [ -f "$f" ]
    then
        git show $(head -n1 "$f")
    else
        echo "No conflict."
    fi
}
alias conflict=show-conflict

# replace git history completely (** NEED TO CHANGE THE FOLLOWING <> **)
# http://qiita.com/muran001/items/dea2bbbaea1260098051
function my-git-change-history() {
    git filter-branch --commit-filter '
        if [ "$GIT_COMMITTER_NAME" = "<Old Name>" ];
        then
                GIT_COMMITTER_NAME="<New Name>";
                GIT_AUTHOR_NAME="<New Name>";
                GIT_COMMITTER_EMAIL="<New Email>";
                GIT_AUTHOR_EMAIL="<New Email>";
                git commit-tree "$@";
        else
                git commit-tree "$@";
        fi' HEAD
}

function gco-remote() {
    if [ $# -lt 1 ]; then
        echo "USAGE: gco-remote USER:BRANCH"
        return 1
    fi
    ARG=$1
    USER=$(echo $ARG | cut -d: -f1)
    BRANCH=$(echo $ARG | cut -d: -f2)
    REMOTE=$(git remote -v | grep origin | grep fetch | awk -F'[ \t:/]' '{ print $2":'$USER'/"$4 }')
    echo git remote add $USER $REMOTE
    git remote add $USER $REMOTE
    echo git fetch $USER $BRANCH
    git fetch $USER $BRANCH

    if [ $# -gt 1 ]; then
        echo git checkout $USER/$BRANCH -b ${USER}__${BRANCH}
        git checkout $USER/$BRANCH -b ${USER}__${BRANCH}
    fi
}

# optimize repository after git filter-branch
# http://qiita.com/go_astrayer/items/6e39d3ab16ae8094496c
alias my-git-gc-prune='git gc --aggressive --prune=now'

# when called "Delete refs/original"
alias my-git-delete-update-ref='git update-ref -d refs/original/refs/heads/master'

# force push under public/ by git subtree
# http://stackoverflow.com/questions/13756055/git-subtree-subtree-up-to-date-but-cant-push
alias push-gh-pages='git push gh-pages `git subtree split --prefix public master`:master --force'

# ignore stop screen (Ctrl-S)
stty stop undef

# # replace git to hub command
# function git(){hub "$@"}

# brew install source-highlight
if [ -x /usr/local/bin/src-hilite-lesspipe.sh ]; then
   export LESS='-R'
   export LESSOPEN='| /usr/local/bin/src-hilite-lesspipe.sh %s'
fi

# Keep current directory on leaving vifm
# https://wiki.vifm.info/index.php?title=How_to_set_shell_working_directory_after_leaving_Vifm
function vicd() {
    local dst="$(command vifm $1 $2 --choose-dir -)"
    if [ -z "$dst" ]; then
        echo 'Directory picking cancelled/failed'
        return 1
    fi
    cd "$dst"
}

# find usable zsh keybind -> http://mollifier.hatenablog.com/entry/20081213/1229148947
# % bindkey -d    # restore default binding
# % bindkey -e    # use emacs mode
# % bindkey       # show all key binding

# Esc j -> vifm from current directory
bindkey -s '\ej' '^a vicd . \n'

# v -> vicd()
alias v=vicd

# Esc e -> emacsclient
bindkey -s '\ee' '^a emacsclient -nw -a "" \n'

# Esc i -> tig
bindkey -s '\ei' '^a tig \n'

# Esc \ -> exit
bindkey -s '\e\\' '^a exit \n'

# -> https://unix.stackexchange.com/questions/14230/zsh-tab-completion-on-empty-line
# # expand-or-complete-or-list-files
# function expand-or-complete-or-list-files() {
#     if [[ $#BUFFER == 0 ]]; then
#         BUFFER="ls "
#         CURSOR=3
#         zle list-choices
#         zle backward-kill-word
#     else
#         zle expand-or-complete
#     fi
# }
# zle -N expand-or-complete-or-list-files
# # bind to tab
# bindkey '^I' expand-or-complete-or-list-files


# ## peco
# if [ -f ~/.zshrc-peco ]; then
#    . ~/.zshrc-peco
# fi

## fzf
if [ -f ~/.zshrc-fzf ]; then
   . ~/.zshrc-fzf
fi

# load .zprofile
if [ -f ~/.zprofile ]; then
  . ~/.zprofile
fi

## .zprofile sample
# export DEFAULT_USER=XXXXXX
# export EMAIL=xxx@xxxxx.com
# export MY_PROJ=XXXXXXXX


# wget https://raw.githubusercontent.com/gnachman/iTerm2/master/tests/imgcat
# wget https://raw.githubusercontent.com/gnachman/iTerm2/master/tests/imgls
# https://www.reddit.com/r/tmux/comments/4l5cpi/tmux_imgcat_iterm2/
# https://qiita.com/kiritex/items/786dbed4b7a2a22cbb89
# https://gist.githubusercontent.com/krtx/533d33d6cc49ecbbb8fab0ae871059ec/raw/b109cf4ce521a3ced0cce0da22f6d0365bc1b822/imgcat

# tmux-powerline prompt
# -> https://matsu.teraren.com/blog/2013/02/10/moteru-tmux-powerline/
PS1="$PS1"'$([ -n "$TMUX" ] && tmux setenv TMUXPWD_$(tmux display -p "#D" | tr -d %) "$PWD")'

KUBEPS1=/usr/local/opt/kube-ps1/share/kube-ps1.sh
if [ -e "$KUBEPS1" ]; then
  source "$KUBEPS1"
  # to toggle: kubeon / kubeoff
  PS1='$(kube_ps1)'$PS1
  kubeoff
fi
