#!/bin/sh
# Turn on every external monitor at its native resolution and the fastest
# refresh rate it offers there, each one to the left of the last, starting
# from the laptop's screen. X finds a monitor on the NVIDIA card's HDMI port
# but gives it no mode, and left to `--auto` it settles for the 60Hz the
# monitor calls preferred.
set -u

primary=$(xrandr | awk '$2 == "connected" && $3 == "primary" { print $1 }')

# For each external output print "output resolution rate". xrandr lists an
# output's native resolution first, its rates after it, marked with * for
# the current one and + for the preferred one.
xrandr | awk '
	$2 == "connected" { output = ($3 == "primary") ? "" : $1; next }
	/^[^ ]/ { output = ""; next }
	output != "" && $1 ~ /^[0-9]+x[0-9]+$/ {
		fastest = 0
		for (i = 2; i <= NF; i++) {
			rate = $i
			gsub(/[*+]/, "", rate)
			if (rate + 0 > fastest + 0) fastest = rate
		}
		print output, $1, fastest
		output = ""
	}
' | {
	previous=$primary
	while read -r output resolution rate; do
		if [ -n "$previous" ]; then
			xrandr --output "$output" --mode "$resolution" --rate "$rate" --left-of "$previous"
		else
			xrandr --output "$output" --mode "$resolution" --rate "$rate"
		fi
		previous=$output
	done
}
