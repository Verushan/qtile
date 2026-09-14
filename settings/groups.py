from libqtile.config import Key, Group, ScratchPad, DropDown
from libqtile.lazy import lazy
from .keys import mod, keys


def scratchpad_base(opacity=0.9):
    return {"width": 0.8, "height": 0.8, "x": 0.1, "y": 0.1, "opacity": opacity}


workspace_symbol = " ● "

groups = [
    Group(name=str(index), label=icon)
    for index, icon in enumerate(workspace_symbol for _ in range(9))
]

for i, group in enumerate(groups):
    keybind = str(i + 1)

    keys.extend(
        [
            # Switch to workspace N
            Key([mod], keybind, lazy.group[group.name].toscreen()),
            # Send window to workspace N
            Key([mod, "shift"], keybind, lazy.window.togroup(group.name)),
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
