#!/usr/bin/env bash
# Shared rofi front-end helpers for the bar's click menus.
#
# Each menu is a list of labels and a parallel list of opaque actions; rofi is
# asked for the *index* of the choice (-format i) so a network or device name
# is never parsed back out of its own decorated label.

rofi_pick() { # prompt, lines... -> index on stdout, 1 if cancelled
	local prompt=$1
	shift
	printf '%s\n' "$@" |
		rofi -dmenu -i -format i -p "$prompt" \
			-theme-str 'window { width: 22em; } listview { lines: 9; }'
}

rofi_password() { # prompt -> secret on stdout, 1 if cancelled
	rofi -dmenu -password -p "$1" -lines 0 \
		-theme-str 'window { width: 22em; } listview { enabled: false; }' </dev/null
}

report() { # title, body
	notify-send -a "$MENU_APP" "$1" "$2"
}

# Run a command, reporting only when it fails - the bar widget is the success
# message.
attempt() { # failure title, command...
	local title=$1 output
	shift

	if ! output=$("$@" 2>&1); then
		report "$title" "${output:-$*}"
		return 1
	fi
}
