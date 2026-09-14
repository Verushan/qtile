#!/usr/bin/env bash
# Wi-Fi applet for the qtile bar: pick a network, toggle the radio, rescan.
set -u

MENU_APP="Wi-Fi"
. "$(dirname "$(readlink -f "$0")")/menu.sh"

# nmcli --terse escapes ':' and '\' inside values; SSID is asked for last so
# everything after the third colon is the name, escapes and all.
unescape() { sed -e 's/\\\(.\)/\1/g'; }

signal_icon() { # strength, 0-100
	if [ "$1" -ge 75 ]; then echo "󰤨"
	elif [ "$1" -ge 50 ]; then echo "󰤥"
	elif [ "$1" -ge 25 ]; then echo "󰤢"
	else echo "󰤟"
	fi
}

known() { # ssid - does a saved connection profile already exist?
	nmcli -t -f NAME connection show | unescape | grep -Fxq "$1"
}

connect() { # ssid, security ("" when open)
	local ssid=$1 security=$2 password

	if known "$ssid"; then
		attempt "$ssid" nmcli connection up id "$ssid" && return
		# A saved profile can hold a stale password, so fall through and re-ask
		# rather than leaving the failure as the last word.
	fi

	if [ -z "$security" ]; then
		attempt "$ssid" nmcli device wifi connect "$ssid"
		return
	fi

	password=$(rofi_password "Password for $ssid") || return
	[ -n "$password" ] || return
	attempt "$ssid" nmcli device wifi connect "$ssid" password "$password"
}

# Each entry is a label the user sees and an action of tab-separated fields,
# so a name containing spaces survives the round trip.
add() { # label, action fields...
	local label=$1
	shift
	labels+=("$label")
	actions+=("$(printf '%s\t' "$@")")
}

build_menu() {
	local radio line rest in_use signal security ssid
	local -a seen=()

	labels=()
	actions=()
	radio=$(nmcli radio wifi)

	if [ "$radio" = enabled ]; then
		add "󰖪  Turn Wi-Fi off" radio off
		add "󰑓  Rescan" rescan
	else
		add "󰖩  Turn Wi-Fi on" radio on
	fi

	add "󰒓  Network settings" settings

	[ "$radio" = enabled ] || return

	while IFS= read -r line; do
		in_use=${line%%:*}
		rest=${line#*:}
		signal=${rest%%:*}
		rest=${rest#*:}
		security=${rest%%:*}
		ssid=$(printf '%s' "${rest#*:}" | unescape)

		# Hidden networks report a blank SSID, and one network can answer from
		# several access points; nmcli sorts by signal, so keep the first row
		# of each name and drop the weaker duplicates.
		[ -n "$ssid" ] || continue
		[[ " ${seen[*]-} " == *" $ssid "* ]] && continue
		seen+=("$ssid")

		if [ "$in_use" = "*" ]; then
			add "$(signal_icon "$signal")  $ssid   󰅖 disconnect" down "$ssid"
		else
			add "$(signal_icon "$signal")  $ssid${security:+  󰌾}" up "$ssid" "$security"
		fi
	done < <(nmcli -t -f IN-USE,SIGNAL,SECURITY,SSID device wifi list --rescan no)
}

# The menu reopens after each action so it behaves like an applet panel:
# toggling the radio or rescanning leaves you looking at the new list.
while true; do
	build_menu
	choice=$(rofi_pick "Wi-Fi" "${labels[@]}") || exit 0
	[ "$choice" -ge 0 ] 2>/dev/null || exit 0

	IFS=$'\t' read -r -a action <<<"${actions[$choice]}"
	case ${action[0]} in
	radio) nmcli radio wifi "${action[1]}" ;;
	rescan) nmcli device wifi rescan >/dev/null 2>&1 ;;
	settings)
		nm-connection-editor &
		exit 0
		;;
	down) attempt "Wi-Fi" nmcli connection down id "${action[1]}" ;;
	up) connect "${action[1]}" "${action[2]-}" ;;
	esac
done
