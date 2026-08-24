from libqtile import layout
from libqtile.config import Match
from .theme import colors
from .config import config


# Layouts and layout rules
layout_conf = {
    "border_focus": colors["active"][0],
    "border_width": config.read_config("border-width"),
    "margin": config.read_config("gap") // 2,
    "border_on_single": True,
}

layouts = [
    layout.Bsp(**layout_conf),
    # layout.Columns(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]


floating_layout = layout.Floating(
    float_rules=[*layout.Floating.default_float_rules], border_focus=colors["color2"][0]
)
