#!/bin/sh
wallpaper_interval_in_min=5
wallpapers="$HOME/Pictures/Victus"

# Set a wallpaper now and swap to another one every few minutes. The script
# picks one and hangs it; qtile waits for this file before it finishes
# starting up, so the rotation goes into the background. It ends when the
# script does - once the X session is gone there is nothing left to set a
# wallpaper on, and the loop should not outlive it.
while "$HOME/.config/qtile/scripts/wallpaper.sh" "$wallpapers"; do
	sleep $((wallpaper_interval_in_min * 60))
done &

# Compositor
picom -b --config ~/.config/picom/picom.conf

# Disable screen off
xset s off
