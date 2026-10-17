from libqtile.config import Key, ScratchPad, DropDown
from libqtile.lazy import lazy
from .keys import mod, keys
from . import desktops, navigation


def scratchpad_base(opacity=0.9):
    return {"width": 0.8, "height": 0.8, "x": 0.1, "y": 0.1, "opacity": opacity}


groups = desktops.groups()

for desktop in range(1, desktops.DESKTOPS + 1):
    keybind = str(desktop)

    keys.extend(
        [
            # Switch every monitor to desktop N
            Key([mod], keybind, navigation.go_to_desktop(desktop)),
            # Send window to desktop N, on the monitor it is on
            Key([mod, "shift"], keybind, navigation.send_to_desktop(desktop)),
        ]
    )

my_scratch_pad = ScratchPad(
    "scratchpad",
    [
        DropDown("terminal", "ghostty --class=scratch", **scratchpad_base()),
        DropDown("volume", "ghostty -e alsamixer", **scratchpad_base()),
        DropDown("files", "dolphin", **scratchpad_base()),
    ],
)

groups.append(my_scratch_pad)

keys.extend(
    [
        Key(
            [mod, "shift"],
            "Return",
            lazy.group["scratchpad"].dropdown_toggle("terminal"),
        ),
        Key([mod, "shift"], "v", lazy.group["scratchpad"].dropdown_toggle("volume")),
        Key([mod, "shift"], "e", lazy.group["scratchpad"].dropdown_toggle("files")),
    ]
)
