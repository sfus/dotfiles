# Print used disk space on the specified filesystem

TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM_DEFAULT="/"

generate_segmentrc() {
	read -d '' rccontents  << EORC
# Filesystem to retrieve disk space information. Any from the filesystems available (run "df | awk '{print $1}'" to check them).
export TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM="${TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM_DEFAULT}"
EORC
	echo "$rccontents"
}

run_segment() {
	__process_settings
    percentage=$(df -h ${TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM} | awk '{print $4"/"$2 " " $5}' | tail -n1)
    echo "${TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM} ${percentage}"
	return 0
}

__process_settings() {
	if [ -z "$TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM" ]; then
        export TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM="${TMUX_POWERLINE_SEG_DISK_USAGE_FILESYSTEM_DEFAULT}"
    fi
    return 0
}
