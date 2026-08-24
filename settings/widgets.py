import html
import subprocess

from libqtile import widget
from .theme import colors


def base(fg="text", bg="dark"):
    return {"foreground": colors[fg], "background": colors[bg]}


# The Bluetooth SIG brand blue, plus two shades of it mixed towards the bar.
bluetooth_blue = "#0082fc"


def shade(color, factor):
    """Mix a colour towards the bar background so it dims but stays legible."""
    top = colors[color][0] if color in colors else color
    bottom = colors["dark"][0]
    channels = (
        round(
            int(top.lstrip("#")[i : i + 2], 16) * factor
            + int(bottom.lstrip("#")[i : i + 2], 16) * (1 - factor)
        )
        for i in (0, 2, 4)
    )
    return "#" + "".join(f"{channel:02x}" for channel in channels)


bt_connected = bluetooth_blue
bt_idle = shade(bluetooth_blue, 0.55)
bt_off = shade(bluetooth_blue, 0.30)
rule = shade("light", 0.35)


def item_separator():
    return widget.Sep(**base("active"), linewidth=0, padding=5, height_percent=100)


def bar_edge_separator():
    return widget.Sep(**base("active"), linewidth=0, padding=15, height_percent=100)


def divider():
    return widget.Sep(
        foreground=rule,
        background=colors["dark"],
        linewidth=1,
        padding=12,
        size_percent=55,
    )


def icon(fg="text", bg="dark", fontsize=16, text="?"):
    return widget.TextBox(**base(fg, bg), fontsize=fontsize, text=text, padding=3)


def poll(command):
    """Run a command and return its stdout, or "" if it is unavailable/fails."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=3
        )
    except (OSError, subprocess.SubprocessError):
        return ""

    return result.stdout if result.returncode == 0 else ""


def nmcli_fields(line):
    """Split a terse nmcli line into fields, honouring its backslash escapes."""
    fields, current, escaped = [], "", False

    for char in line:
        if escaped:
            current += char
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == ":":
            fields.append(current)
            current = ""
        else:
            current += char

    fields.append(current)
    return fields


def truncate(text, limit=18):
    """Keep a name short enough that the bar layout stays stable."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def bluetooth_text():
    """The connected device, shading the icon by how active bluetooth is."""
    if "Powered: yes" not in poll(["bluetoothctl", "show"]):
        return f'<span foreground="{bt_off}">󰂲</span>'

    names = []

    for line in poll(["bluetoothctl", "devices", "Connected"]).splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            names.append(parts[2])

    if not names:
        return f'<span foreground="{bt_idle}">󰂯</span>'

    label = truncate(names[0])
    if len(names) > 1:
        label += f" +{len(names) - 1}"

    return (
        f'<span foreground="{bt_connected}">󰂱</span>  '
        + html.escape(label, quote=False)
    )


def network_text():
    """The active wifi/ethernet connection, or an offline indicator."""
    output = poll(
        ["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device", "status"]
    )

    for line in output.splitlines():
        fields = nmcli_fields(line)
        if len(fields) < 4:
            continue

        _, kind, state, connection = fields[:4]
        if kind in ("wifi", "ethernet") and state.startswith("connected"):
            symbol = "󰖩" if kind == "wifi" else "󰈀"
            return f"{symbol}  {truncate(connection)}"

    return "󰖪  Offline"


def bluetooth():
    return widget.GenPollText(
        **base(fg="light"),
        func=bluetooth_text,
        update_interval=5,
    )


def network():
    return widget.GenPollText(
        **base(fg="color5"),
        func=network_text,
        update_interval=5,
        markup=False,
    )


def workspaces():
    return [
        widget.Spacer(**base()),
        widget.GroupBox(
            **base(fg="color1"),
            font="Jetbrains Mono Nerd Font",
            fontsize=20,
            margin_y=0,
            margin_x=0,
            padding_y=0,
            padding_x=0,
            borderwidth=0,
            active=colors["active"],
            inactive=colors["inactive"],
            rounded=False,
            highlight_method="block",
            highlight_color=colors["light"],
            urgent_alert_method="block",
            urgent_border=colors["urgent"],
            this_current_screen_border=colors["focus"],
            this_screen_border=colors["grey"],
            other_current_screen_border=colors["dark"],
            other_screen_border=colors["dark"],
            disable_drag=True,
            hide_unused=True,
        ),
        widget.Spacer(**base()),
    ]


primary_widgets = [
    bar_edge_separator(),
    widget.Clock(**base(fg="color1"), format="%A %d %B %H:%M %p"),
    divider(),
    network(),
    divider(),
    bluetooth(),
    *workspaces(),
    widget.CPU(**base(fg="color2"), format="󰧑  {load_percent}%"),
    item_separator(),
    widget.Memory(**base(fg="color3"), format=" 󰑹 {MemPercent}%"),
    item_separator(),
    widget.Volume(**base(fg="color4"), fmt=" 󰟅 {}", volume_app="pavucontrol"),
    item_separator(),
    widget.ThermalSensor(
        **base(fg="color5"),
        threshold=90,
        fmt="󰏈  {}",
        padding=5,
    ),
    item_separator(),
    widget.Battery(
        **base(fg="color6"),
        padding=5,
        format="{char} {percent:2.0%}",
        discharge_char="󱟞",
        full_char="󱈏",
        charge_char="󱈑",
        show_short_text=False,
        update_interval=5,
    ),
    bar_edge_separator(),
]

widget_defaults = {
    "font": "JetBrainsMono Nerd Font Bold",
    "fontsize": 15,
    "padding": 0,
}

extension_defaults = widget_defaults.copy()
