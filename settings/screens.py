# Antonio Sarosi
# https://youtube.com/c/antoniosarosi
# https://github.com/antoniosarosi/dotfiles

# Multimonitor support

import subprocess

from libqtile.config import Screen
from libqtile import bar
from libqtile.bar import Gap
from libqtile.log_utils import logger

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

xrandr = "xrandr | grep -w 'connected' | cut -d ' ' -f 2 | wc -l"

command = subprocess.run(
    xrandr,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

if command.returncode != 0:
    error = command.stderr.decode("UTF-8")
    logger.error(f"Failed counting monitors using {xrandr}:\n{error}")
    connected_monitors = 1
else:
    connected_monitors = int(command.stdout.decode("UTF-8"))

# Each extra monitor gets its own bar. Counted when the config loads, so a
# monitor plugged in later needs a qtile restart to get one.
for _ in range(1, connected_monitors):
    screens.append(
        Screen(
            top=status_bar(secondary_widgets()),
            left=Gap(size=GAP),
            right=Gap(size=GAP),
            bottom=Gap(size=GAP),
        )
    )
