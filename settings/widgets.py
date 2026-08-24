import html
import subprocess
from glob import glob
from os import path

import psutil

from libqtile import widget
from libqtile.widget.battery import BatteryState, _LinuxBattery
from .theme import colors


def base(fg="text", bg="dark"):
    return {"foreground": colors[fg], "background": colors[bg]}


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


# One theme colour per connection state state
connected = colors["color1"][0]
idle = colors["color5"][0]
off = colors["color3"][0]

gpu_asleep = shade("color1", 0.45)
rule = shade("light", 0.35)

# Temperatures worth colouring red.
cpu_alert = 90
gpu_alert = 85


class Centred:
    """Sit text on the bar's real centre line.

    ``libqtile.widget.base._TextBox.draw`` centres its layout and then adds a
    pixel, so every glyph hangs low - obvious next to ``widget.Sep``, which
    centres itself honestly. Wrapping the layout's ``draw`` takes that pixel
    back without reimplementing qtile's ``draw()``.

    ``nudge`` is that correction in pixels; a widget whose glyph is drawn low
    inside its own em box can ask for more.
    """

    nudge = -1

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        draw = self.layout.draw
        nudge = self.nudge
        self.layout.draw = lambda x, y: draw(x, y + nudge)


class Clock(Centred, widget.Clock):
    pass


class GenPollText(Centred, widget.GenPollText):
    pass


class Memory(Centred, widget.Memory):
    pass


class TextBox(Centred, widget.TextBox):
    pass


class Volume(Centred, widget.Volume):
    """qtile only varies the speaker glyph when it is drawing an icon theme,
    so pick one here rather than leaving a single fixed icon in ``fmt``."""

    def _update_drawer(self):
        if self.volume is None or self.volume < 0:
            self.text = "󰖁"
        elif self.is_mute or self.volume == 0:
            self.text = f"󰖁 {self.volume}%"
        elif self.volume <= 30:
            self.text = f"󰕿 {self.volume}%"
        elif self.volume < 80:
            self.text = f"󰖀 {self.volume}%"
        else:
            self.text = f"󰕾 {self.volume}%"


# The charger stops at ~99.4% of the energy_full this battery's firmware
# reports, so energy_now/energy_full never rounds up and the widget sticks at
# 99%. Treat a battery that is plugged in and this close to the top as full.
battery_full_enough = 0.99


class _ToppedUpBattery(_LinuxBattery):
    def update_status(self):
        status = super().update_status()

        if (
            status.state is not BatteryState.DISCHARGING
            and status.percent >= battery_full_enough
        ):
            return status._replace(state=BatteryState.FULL, percent=1.0)

        return status


class Battery(Centred, widget.Battery):
    @staticmethod
    def _load_battery(**config):
        return _ToppedUpBattery(**config)


def item_separator():
    return widget.Sep(**base("active"), linewidth=0, padding=5, height_percent=100)


def bar_edge_separator():
    return widget.Sep(**base("active"), linewidth=0, padding=15, height_percent=100)


def gap(size):
    """An exact horizontal space. Sep's width is padding + linewidth, not x2."""
    return widget.Sep(background=colors["dark"], linewidth=0, padding=size)


def spaced(*widgets, size=14):
    """Lay widgets out with one consistent gap between them, so a widget whose
    icon sits flush against its box is not crowded by its neighbour."""
    laid_out = []
    for item in widgets:
        if laid_out:
            laid_out.append(gap(size))
        laid_out.append(item)

    return laid_out


def divider():
    return widget.Sep(
        foreground=rule,
        background=colors["dark"],
        linewidth=1,
        padding=0,
        size_percent=55,
    )


def divided(left=9, right=10):
    """A rule with optically even gaps.

    Text carries ~1px of side bearing where the nerd font icons carry none, so
    whichever side holds an icon needs the extra pixel to look like the same
    distance.
    """
    return [gap(left), divider(), gap(right)]


def icon(fg="text", bg="dark", fontsize=16, text="?"):
    return TextBox(**base(fg, bg), fontsize=fontsize, text=text, padding=3)


class Logo(TextBox):
    """The font-logos glyphs sit on the text baseline rather than centred on
    the em box the way the Material icons do, so this one needs a second pixel
    to line up with the rule beside it."""

    nudge = -2


def logo():
    """The distro mark for the bar's left corner. U+F322 is the font-logos
    ``linux-endeavour`` glyph - the neighbouring codepoints are other distros,
    so check the name rather than the shape before swapping it."""
    return Logo(**base(fg="color5"), text="\U0000f322")


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


def temperature(degrees, threshold):
    """A reading, in the urgent colour once it is worth noticing."""
    text = f"{degrees:.0f}°C"
    if degrees >= threshold:
        return f'<span foreground="{colors["urgent"][0]}">{text}</span>'

    return text


def bluetooth_text():
    """The connected device, shading the icon by how active bluetooth is."""
    if "Powered: yes" not in poll(["bluetoothctl", "show"]):
        return f'<span foreground="{off}">󰂲</span>'

    names = []

    for line in poll(["bluetoothctl", "devices", "Connected"]).splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            names.append(parts[2])

    if not names:
        return f'<span foreground="{idle}">󰂯</span>'

    label = truncate(names[0], 25)
    if len(names) > 1:
        label += f" +{len(names) - 1}"

    return (
        f'<span foreground="{connected}">󰂱</span> '
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
            return (
                f'<span foreground="{connected}">{symbol}</span> ' + html.escape(truncate(connection), quote=False)
            )

    return "󰖪 Offline"


def cpu_temperature():
    """The CPU package sensor. psutil lists the acpitz chassis zone first, so
    ask coretemp for the package reading by name rather than taking the head
    of the list."""
    for entry in psutil.sensors_temperatures().get("coretemp", []):
        if entry.label.startswith("Package id"):
            return entry.current

    return None


cpu_sampled = False


def cpu_load():
    """Load since the previous poll. psutil measures between calls, so the
    first one has no window to average over - take a short sample instead of
    reporting the 0% it would otherwise return."""
    global cpu_sampled

    if cpu_sampled:
        return psutil.cpu_percent()

    cpu_sampled = True
    return psutil.cpu_percent(interval=0.1)


def cpu_text():
    """Load and package temperature under one processor icon."""
    parts = [f"󰍛 {cpu_load():.0f}%"]

    degrees = cpu_temperature()
    if degrees is not None:
        parts.append(temperature(degrees, cpu_alert))

    return " ".join(parts)


def gpu_runtime_state():
    """The discrete GPU's power-state file, so polling never wakes the card."""
    for device in glob("/sys/bus/pci/devices/*"):
        try:
            with open(path.join(device, "vendor")) as f:
                vendor = f.read().strip()
            with open(path.join(device, "class")) as f:
                pci_class = f.read().strip()
        except OSError:
            continue

        if vendor == "0x10de" and pci_class.startswith("0x03"):
            return path.join(device, "power", "runtime_status")

    return None


gpu_state_path = gpu_runtime_state()


def gpu_suspended():
    """Whether the discrete GPU is asleep. Querying it would wake the card."""
    if not gpu_state_path:
        return False

    try:
        with open(gpu_state_path) as f:
            return f.read().strip() == "suspended"
    except OSError:
        return False


def nvidia_stats():
    """Utilisation and temperature, or None while the card is asleep."""
    if gpu_suspended():
        return None

    reading = poll(
        [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,temperature.gpu",
            "--format=csv,noheader,nounits",
        ]
    )
    parts = [field.strip() for field in reading.split(",")]
    if len(parts) == 2 and all(field.isdigit() for field in parts):
        return int(parts[0]), int(parts[1])

    return None


def gpu_text():
    """Load and temperature under one card icon, dimmed to just the icon while
    the card is asleep."""
    stats = nvidia_stats()
    if stats is None:
        return f'<span foreground="{gpu_asleep}">󰢮</span>'

    usage, degrees = stats
    return f"󰢮 {usage}% {temperature(degrees, gpu_alert)}"


def cpu():
    return GenPollText(
        **base(fg="color2"),
        func=cpu_text,
        update_interval=5,
    )


def gpu():
    return GenPollText(
        **base(fg="color5"),
        func=gpu_text,
        update_interval=5,
    )


def bluetooth():
    return GenPollText(
        **base(fg="color1"),
        func=bluetooth_text,
        update_interval=5,
    )


def network():
    return GenPollText(
        **base(fg="color1"),
        func=network_text,
        update_interval=5,
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
    logo(),
    # The logo is the icon side of this rule, so its gap is the wider one.
    *divided(left=10, right=9),
    Clock(**base(fg="color1"), format="%A %d %B %H:%M %p"),
    *divided(),
    network(),
    *divided(),
    bluetooth(),
    *workspaces(),
    *spaced(
        cpu(),
        gpu(),
        Memory(**base(fg="color3"), format="  {MemPercent}%"),
        Volume(**base(fg="color4"), volume_app="pavucontrol"),
        Battery(
            **base(fg="color6"),
            format="{char} {percent:2.0%}",
            discharge_char="󱟞",
            full_char="󰁹",
            charge_char="󰂄",
            show_short_text=False,
            update_interval=5,
        ),
    ),
    bar_edge_separator(),
]

widget_defaults = {
    "font": "JetBrainsMono Nerd Font Bold",
    "fontsize": 15,
    "padding": 0,
}

extension_defaults = widget_defaults.copy()
