#!/bin/sh
wallpaper_interval_in_min=5

# Call script to set wallpaper and perodically change the wallpaper
feh --bg-fill "/home/elementrix/Pictures/Victus/Victus Eye.jpg"

# Compositor
picom -b --config ~/.config/picom/picom.conf

# Disable screen off
xset s off