#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
PS1='[\u@\h \W]\$ '

function aud()
{
	youtube-dl --extract-audio --audio-format mp3 $(xclip -o)
}

function vid()
{
	youtube-dl $(xclip -o)
}
