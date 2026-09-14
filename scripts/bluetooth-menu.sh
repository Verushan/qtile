#!/usr/bin/env bash
# Bluetooth applet for the qtile bar: connect a paired device, pair a new one,
# toggle the adapter.
set -u

MENU_APP="Bluetooth"
. "$(dirname "$(readlink -f "$0")")/menu.sh"

scan_seconds=8

field() { # info output, field name
	printf '%s\n' "$1" | sed -n "s/^[[:space:]]*$2: //p" | head -1
}

device_icon() { # the device's "Icon" field
	case $1 in
	audio-headset | audio-headphones) echo "󰋋" ;;
	audio-card) echo "󰓃" ;;
	input-mouse) echo "󰍽" ;;
	input-keyboard) echo "󰌌" ;;
	input-gaming) echo "󰊴" ;;
	phone) echo "󰏲" ;;
	computer) echo "󰟀" ;;
	*) echo "󰂯" ;;
	esac
}

pair() { # mac, name
	local mac=$1 name=$2

	attempt "$name" bluetoothctl pair "$mac" || return
	bluetoothctl trust "$mac" >/dev/null
	attempt "$name" bluetoothctl connect "$mac"
}

# Each entry is a label the user sees and an action of tab-separated fields,
# so a device name containing spaces survives the round trip.
add() { # label, action fields...
	local label=$1
	shift
	labels+=("$label")
	actions+=("$(printf '%s\t' "$@")")
}

# bluetoothctl prints "Device <mac> <name>" per line.
add_devices() { # filter ("Paired"/"" for everything known), skip-paired flag
	local line mac name info connected
	local -a paired=()

	[ "$2" = skip ] && mapfile -t paired < <(bluetoothctl devices Paired | cut -d' ' -f2)

	while read -r _ mac name; do
		[ -n "$mac" ] || continue
		[[ "$2" == skip && " ${paired[*]-} " == *" $mac "* ]] && continue

		info=$(bluetoothctl info "$mac")
		connected=$(field "$info" Connected)

		if [ "$connected" = yes ]; then
			add "$(device_icon "$(field "$info" Icon)")  $name   󰅖 disconnect" \
				disconnect "$mac" "$name"
		elif [ "$2" = skip ]; then
			add "󰂲  $name   󰌷 pair" pair "$mac" "$name"
		else
			add "$(device_icon "$(field "$info" Icon)")  $name" connect "$mac" "$name"
		fi
	done < <(bluetoothctl devices ${1:+"$1"})
}

build_menu() {
	local powered

	labels=()
	actions=()
	powered=$(field "$(bluetoothctl show)" Powered)

	if [ "$powered" = yes ]; then
		add "󰂲  Turn Bluetooth off" power off
		add "󰑓  Scan for devices" scan
	else
		add "󰂯  Turn Bluetooth on" power on
		return
	fi

	# Paired devices first - they are the ones you actually reconnect to -
	# then whatever else the last scan turned up.
	add_devices Paired keep
	add_devices "" skip
}

# The menu reopens after each action so it behaves like an applet panel:
# scanning or toggling the adapter leaves you looking at the new list.
while true; do
	build_menu
	choice=$(rofi_pick "Bluetooth" "${labels[@]}") || exit 0
	[ "$choice" -ge 0 ] 2>/dev/null || exit 0

	IFS=$'\t' read -r -a action <<<"${actions[$choice]}"
	case ${action[0]} in
	power) bluetoothctl power "${action[1]}" >/dev/null ;;
	scan) bluetoothctl --timeout "$scan_seconds" scan on >/dev/null ;;
	connect) attempt "${action[2]}" bluetoothctl connect "${action[1]}" ;;
	disconnect) attempt "${action[2]}" bluetoothctl disconnect "${action[1]}" ;;
	pair) pair "${action[1]}" "${action[2]}" ;;
	esac
done
