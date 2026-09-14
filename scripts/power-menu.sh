#!/usr/bin/env bash
# Session applet for the bar's distro mark: lock, log out, suspend, restart,
# shut down.
set -u

MENU_APP="Session"
. "$(dirname "$(readlink -f "$0")")/menu.sh"

locker() {
	# In preference order; nothing is printed if none of them is installed,
	# and the menu leaves the row out rather than offering a dead action.
	for candidate in betterlockscreen i3lock xsecurelock slock; do
		if command -v "$candidate" >/dev/null; then
			printf '%s' "$candidate"
			return
		fi
	done
}

lock() { # locker
	case $1 in
	betterlockscreen) betterlockscreen -l ;;
	i3lock) i3lock -c 1d1c19 ;;
	*) "$1" ;;
	esac
}

confirmed() { # what is about to happen
	local choice
	choice=$(rofi_pick "$1?" "󰅖  No" "󰄬  Yes") || return 1
	[ "$choice" = 1 ]
}

labels=()
actions=()

add() { # label, action
	labels+=("$1")
	actions+=("$2")
}

screen_locker=$(locker)
[ -n "$screen_locker" ] && add "󰌾  Lock" lock

add "󰤄  Suspend" suspend
add "󰍃  Log out" logout
add "󰜉  Restart" reboot
add "󰐥  Shut down" poweroff

choice=$(rofi_pick "Session" "${labels[@]}") || exit 0
[ "$choice" -ge 0 ] 2>/dev/null || exit 0

# Only the ones that throw work away ask twice; locking and suspending are a
# keystroke from undone.
case ${actions[$choice]} in
lock) lock "$screen_locker" ;;
suspend) systemctl suspend ;;
logout) confirmed "Log out" && qtile cmd-obj -o cmd -f shutdown ;;
reboot) confirmed "Restart" && systemctl reboot ;;
poweroff) confirmed "Shut down" && systemctl poweroff ;;
esac
