if [ $UID -eq 0 ]; then NCOLOR="red"; else NCOLOR="green"; fi
local return_code="%(?..%{$fg[red]%}->%? %{$reset_color%})"

PREFIX='%{$reset_color%}'
if [ "$DEFAULT_USER" != `whoami` ]; then
  PREFIX='%{$fg[$NCOLOR]%}%n%{$reset_color%}@%{$fg[magenta]%}%m%{$reset_color%}:'
fi

PROMPT=$PREFIX'\
%{$fg[cyan]%}%~\
$(git_prompt_info) \
${return_code}\
%{$fg[$NCOLOR]%}%(!.#.»)%{$reset_color%} '
PROMPT2='%{$fg[red]%}\ %{$reset_color%}'

ZSH_THEME_GIT_PROMPT_PREFIX=" %{$fg[yellow]%}("
ZSH_THEME_GIT_PROMPT_CLEAN=" %{$fg[green]%}o%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY=" %{$fg[red]%}*%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$fg[yellow]%})%{$reset_color%}"
