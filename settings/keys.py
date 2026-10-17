from libqtile.lazy import lazy
from libqtile.config import Key

from . import navigation

mod = "mod4"

# Run commands for common programs
terminal = "ghostty"
browser = "brave"
file_explorer = "dolphin"

keys = [
    Key(key[0], key[1], *key[2:])
    for key in [
        # ------------ Window Configs ------------
        # Switch between windows, carrying on to the next monitor at the edge
        ([mod], "j", lazy.layout.down()),
        ([mod], "k", lazy.layout.up()),
        ([mod], "h", navigation.focus("left")),
        ([mod], "l", navigation.focus("right")),
        # BSP window grow
        ([mod, "control"], "j", lazy.layout.grow_down()),
        ([mod, "control"], "k", lazy.layout.grow_up()),
        ([mod, "control"], "h", lazy.layout.grow_left()),
        ([mod, "control"], "l", lazy.layout.grow_right()),
        # Toggle floating
        ([mod, "shift"], "f", lazy.window.toggle_floating()),
        # Toggle fullscreen
        ([mod, "shift"], "m", lazy.window.toggle_fullscreen()),
        # Move windows around, pushing them onto the next monitor at the edge
        ([mod, "shift"], "j", lazy.layout.shuffle_down()),
        ([mod, "shift"], "k", lazy.layout.shuffle_up()),
        ([mod, "shift"], "h", navigation.shuffle("left")),
        ([mod, "shift"], "l", navigation.shuffle("right")),
        # Toggle between different layouts as defined below
        ([mod], "Tab", lazy.next_layout()),
        ([mod, "shift"], "Tab", lazy.prev_layout()),
        # Kill window
        ([mod, "shift"], "q", lazy.window.kill()),
        # Focus the monitor to the left/right, or send the window there
        ([mod], "comma", navigation.focus_screen("left")),
        ([mod], "period", navigation.focus_screen("right")),
        ([mod, "shift"], "comma", navigation.send_to_screen("left")),
        ([mod, "shift"], "period", navigation.send_to_screen("right")),
        # Restart Qtile
        ([mod, "control"], "r", lazy.reload_config()),
        ([mod, "control"], "q", lazy.shutdown()),
        # ------------ App Configs ------------
        # Menu
        ([mod], "p", lazy.spawn("rofi -show drun")),
        # Screenshots
        ([mod, "shift"], "s", lazy.spawn("flameshot gui")),
        # Window Nav
        ([mod, "shift"], "p", lazy.spawn("rofi -show")),
        # File Explorer
        ([mod], "e", lazy.spawn(file_explorer)),
        # Terminal
        ([mod], "Return", lazy.spawn(terminal)),
        ([mod], "b", lazy.spawn(browser)),
        # ------------ Hardware Configs ------------
        # Volume
        ([mod], "Down", lazy.spawn("amixer sset Master 5%-")),
        ([mod], "Up", lazy.spawn("amixer sset Master 5%+")),
        ([mod], "m", lazy.spawn("pactl set-sink-mute @DEFAULT_SINK@ toggle")),
        # Brightness
        ([mod], "Left", lazy.spawn("brightnessctl set 10%-")),
        ([mod], "Right", lazy.spawn("brightnessctl set +10%")),
    ]
]
