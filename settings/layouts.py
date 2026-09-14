from libqtile import layout
from libqtile.config import Match
from .theme import colors
from .config import config


# Layouts and layout rules
border_conf = {
    "border_focus": colors["active"][0],
    "border_width": config.read_config("border-width"),
    "margin": config.read_config("gap") // 2,
}

layout_conf = {**border_conf, "border_on_single": True}

layouts = [
    layout.Bsp(**layout_conf),
    # Max shows one window at a time, so "border_on_single" - Bsp's way of
    # keeping the border once the split is gone - has nothing to say here.
    layout.Max(**border_conf),
    # layout.Columns(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]


floating_layout = layout.Floating(
    float_rules=[*layout.Floating.default_float_rules], border_focus=colors["color2"][0]
)
