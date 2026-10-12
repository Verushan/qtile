from libqtile.lazy import lazy
from libqtile.config import Key

mod = "mod4"

# Run commands for common programs
terminal = "ghostty"
browser = "brave"
file_explorer = "dolphin"

keys = [
    Key(key[0], key[1], *key[2:])
    for key in [
        # ------------ Window Configs ------------
        # Switch between windows in current stack pane
        ([mod], "j", lazy.layout.down()),
        ([mod], "k", lazy.layout.up()),
        ([mod], "h", lazy.layout.left()),
        ([mod], "l", lazy.layout.right()),
        # BSP window grow
        ([mod, "control"], "j", lazy.layout.grow_down()),
        ([mod, "control"], "k", lazy.layout.grow_up()),
        ([mod, "control"], "h", lazy.layout.grow_left()),
        ([mod, "control"], "l", lazy.layout.grow_right()),
        # Toggle floating
        ([mod, "shift"], "f", lazy.window.toggle_floating()),
        # Toggle fullscreen
        ([mod, "shift"], "m", lazy.window.toggle_fullscreen()),
        # Move windows up or down in current stack
        ([mod, "shift"], "j", lazy.layout.shuffle_down()),
        ([mod, "shift"], "k", lazy.layout.shuffle_up()),
        ([mod, "shift"], "h", lazy.layout.shuffle_left()),
        ([mod, "shift"], "l", lazy.layout.shuffle_right()),
        # Toggle between different layouts as defined below
        ([mod], "Tab", lazy.next_layout()),
        ([mod, "shift"], "Tab", lazy.prev_layout()),
        # Kill window
        ([mod, "shift"], "q", lazy.window.kill()),
        # Switch focus of monitors
        ([mod], "period", lazy.next_screen()),
        ([mod], "comma", lazy.prev_screen()),
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
