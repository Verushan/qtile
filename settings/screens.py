# Antonio Sarosi
# https://youtube.com/c/antoniosarosi
# https://github.com/antoniosarosi/dotfiles

# Multimonitor support

from libqtile.config import Screen
from libqtile import bar
from libqtile.bar import Gap

from . import desktops
from .widgets import primary_widgets, secondary_widgets
from .config import config

GAP = config.read_config("gap") // 2


def status_bar(widgets):
    return bar.Bar(widgets, 32, opacity=1, margin=[GAP, GAP, GAP, GAP])


screens = [
    Screen(
        top=status_bar(primary_widgets),
        left=Gap(size=GAP),
        right=Gap(size=GAP),
        bottom=Gap(size=GAP),
    )
]

# A bar for every monitor qtile may meet, not just the ones plugged in now.
# qtile only builds the bars of monitors that are there, and picks the next
# one up when a monitor is plugged in.
for monitor in range(1, desktops.MONITORS):
    screens.append(
        Screen(
            top=status_bar(secondary_widgets(monitor)),
            left=Gap(size=GAP),
            right=Gap(size=GAP),
            bottom=Gap(size=GAP),
        )
    )
