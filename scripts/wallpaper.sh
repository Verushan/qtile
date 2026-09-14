#!/usr/bin/env bash
# Set a random wallpaper, pulling the bright ones down first so a photo of a
# sunlit sky does not shout over the windows sitting on top of it.
set -u

wallpapers=${1:-$HOME/Pictures/Victus}
cache=${XDG_CACHE_HOME:-$HOME/.cache}/qtile/wallpapers

# The mean luminance a wallpaper is allowed to keep, 0-1. Anything brighter is
# scaled down to it - so the brighter the picture, the more it gives up, and
# anything already below the line is left exactly as it was shot.
ceiling=0.42

# How far that scaling is allowed to go, as a percentage of the original, and
# what a dulled picture keeps of its colour. Dimming alone leaves a washed-out
# grey, so the saturation comes down with it.
floor=55
saturation=85

# Some of these PNGs carry an alpha channel, and a picture that is dark
# where you can see it reads as bright while its transparent parts still hold
# white underneath. Flatten onto the black the desktop shows through anyway,
# then both the reading and the result describe what actually gets hung.
flattened=(-background black -alpha remove -alpha off)

luminance() { # image
	magick "$1" "${flattened[@]}" -colorspace Gray -format '%[fx:mean]' info: 2>/dev/null
}

dulled() { # image -> the path to actually hang on the desktop
	local source=$1 target=$cache/${1##*/} mean adjust

	mean=$(luminance "$source")
	[ -n "$mean" ] || { printf '%s' "$source"; return; }

	adjust=$(awk -v mean="$mean" -v ceiling="$ceiling" -v floor="$floor" \
		'BEGIN { print (mean > ceiling) ? int(ceiling / mean * 100) : 0 }')

	if [ "$adjust" -eq 0 ]; then
		printf '%s' "$source"
		return
	fi

	[ "$adjust" -lt "$floor" ] && adjust=$floor

	# Redo the work only when the picture is new or has changed underneath us.
	if [ ! -f "$target" ] || [ "$source" -nt "$target" ]; then
		mkdir -p "$cache"
		magick "$source" "${flattened[@]}" -modulate "$adjust,$saturation" "$target" 2>/dev/null ||
			{ printf '%s' "$source"; return; }
	fi

	printf '%s' "$target"
}

chosen=$(find "$wallpapers" -maxdepth 1 -type f -print0 | shuf -z -n1 | tr -d '\0')
[ -n "$chosen" ] || exit 1

feh --no-fehbg --bg-fill "$(dulled "$chosen")"
