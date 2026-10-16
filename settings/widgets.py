import html
import subprocess
import time
from glob import glob
from math import tau
from os import path

import psutil

from libqtile import bar, pangocffi, widget
from libqtile.lazy import lazy
from libqtile.widget.battery import BatteryState, _LinuxBattery
from .path import qtile_path
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


class Mpris2(Centred, widget.Mpris2):
    pass


class Notify(Centred, widget.Notify):
    pass


class Systray(widget.Systray):
    """A tray that survives a config reload.

    qtile's Systray finishes by dropping its own window from the window map,
    but on a reload that window has already gone. The KeyError then escapes
    ``Bar.finalize``, so every widget to the right of the tray is left
    unfinalised and keeps polling into the bar that has just been replaced.
    Put the entry back so the delete finds what it is looking for.
    """

    def finalize(self):
        self.qtile.windows_map.setdefault(self.wid, self)
        super().finalize()


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


class CollapsingGap(widget.Sep):
    """A gap that goes away along with the widget it spaces.

    The tray is empty whenever nothing has planted an icon in it, and a plain
    ``gap`` beside it would hold that space open anyway. ``Sep`` fixes its
    length when it is built, so make it a calculated one instead and answer 0
    for as long as the partner has nothing to draw.
    """

    def __init__(self, partner, **config):
        super().__init__(**config)
        self.partner = partner
        self.length_type = bar.CALCULATED

    def calculate_length(self):
        # Widgets are configured in bar order, so a partner further right has
        # no bar to measure itself against yet.
        if not self.partner.configured or not self.partner.length:
            return 0

        return self.padding + self.linewidth


def gap(size):
    """An exact horizontal space. Sep's width is padding + linewidth, not x2."""
    return widget.Sep(background=colors["dark"], linewidth=0, padding=size)


def collapsing_gap(partner, size=14):
    return CollapsingGap(partner, background=colors["dark"], linewidth=0, padding=size)


def collapsing_divided(partner, left=9, right=10):
    """A rule and its gaps, all of which come and go with the widget they
    introduce - the music widget is empty whenever nothing is playing, and
    the bar should close up behind it rather than keep a rule hanging."""
    return [
        collapsing_gap(partner, left),
        CollapsingGap(
            partner,
            foreground=rule,
            background=colors["dark"],
            linewidth=1,
            padding=0,
            size_percent=55,
        ),
        collapsing_gap(partner, right),
    ]


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
    to line up with the rule beside it.

    The monospaced Nerd Font gives every icon a single cell of advance and lets
    the wider ones spill past it, so the bar clipped the right half of this
    one. The Propo variant advances each icon by its real width."""

    nudge = -2

    def __init__(self, **config):
        config.setdefault("font", "JetBrainsMono Nerd Font Propo Bold")
        super().__init__(**config)


def logo():
    """The distro mark for the bar's left corner, and the way into the session
    menu. U+F322 is the font-logos ``linux-endeavour`` glyph - the
    neighbouring codepoints are other distros, so check the name rather than
    the shape before swapping it."""
    return Logo(
        **base(fg="color5"),
        text="\U0000f322",
        mouse_callbacks={"Button1": applet("power-menu.sh")},
    )


def applet(name):
    """Open one of the bar's rofi menus. The widget beside it polls every few
    seconds, so the bar catches up on its own once the menu has acted."""
    return lazy.spawn(path.join(qtile_path, "scripts", name))


def poll(command):
    """Run a command and return its stdout, or "" if it is unavailable/fails."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
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

    return f'<span foreground="{connected}">󰂱</span> ' + html.escape(label, quote=False)


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
            return f'<span foreground="{connected}">{symbol} </span> ' + html.escape(
                truncate(connection), quote=False
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


# The icon turns at a rate proportional to how hard the fans are working. Both
# fans plateau at ~5400 RPM when hp-wmi is told to run them flat out
# (``pwm1_enable`` = 0), so that is full speed. The icon has three-fold
# symmetry, so at 20 frames a second it can only be shown turning below
# ~3.3 turns a second before it starts to look like it is running backwards;
# 2.5 keeps clear of that while leaving the idle ~2200 RPM at a visible 1/s.
fan_max_rpm = 5400
fan_max_turns_per_second = 2.5
fan_frame_rate = 20


def fan_speeds():
    """Every chassis fan's RPM, in the order the hwmon driver lists them."""
    return [
        int(fan.current) for chip in psutil.sensors_fans().values() for fan in chip
    ]


def fan_text(speeds):
    """The readings side by side under one unit, or nothing where there is no
    fan to read so the widget closes up rather than leaving a lone icon."""
    if not speeds:
        return ""

    return " · ".join(str(rpm) for rpm in speeds) + " RPM"


class Fan(GenPollText):
    """Fan speed behind an icon that actually turns.

    The bar's other icons are glyphs in the same text run as their reading,
    but pango cannot rotate a glyph. This one is drawn through cairo's own
    text API instead, spun about the centre of its ink box - the hub of the
    fan - by an angle that advances between frames in proportion to how close
    the fastest fan is to its top speed. The reading is still an ordinary
    layout, placed where it would fall after an icon and a space so it lines
    up with the CPU and GPU readouts beside it.
    """

    glyph = "\U000F0210"  # Material Design ``fan``

    def __init__(self, **config):
        super().__init__(func=self.read, **config)
        self.rpm = 0
        self.angle = 0.0
        self.last_frame = time.monotonic()

    def read(self):
        speeds = fan_speeds()
        self.rpm = max(speeds, default=0)
        return fan_text(speeds)

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)

        # ``font`` is a pango description, so let pango pull the family out of
        # it; the icon looks the same at every weight.
        self.family = pangocffi.FontDescription.from_string(self.font).get_family()
        self.select_glyph_font()
        x_bearing, y_bearing, width, height, *_ = self.drawer.ctx.text_extents(
            self.glyph
        )
        self.hub = (x_bearing + width / 2, y_bearing + height / 2)

        lead = self.drawer.textlayout(
            self.glyph + " ", self.foreground, self.font, self.fontsize, None
        )
        self.text_offset = lead.width
        lead.finalize()

    def select_glyph_font(self):
        self.drawer.ctx.select_font_face(self.family)
        self.drawer.ctx.set_font_size(self.fontsize)

    def timer_setup(self):
        super().timer_setup()
        self.turn()

    def turn(self):
        """Advance the icon by however far the fan has turned since the last
        frame, then draw. A stopped fan skips the draw, so an idle machine is
        not repainting the bar twenty times a second for nothing."""
        now = time.monotonic()
        elapsed, self.last_frame = now - self.last_frame, now

        if self.rpm and self.text:
            speed = min(self.rpm / fan_max_rpm, 1)
            turned = tau * elapsed * fan_max_turns_per_second * speed
            self.angle = (self.angle + turned) % tau
            self.draw()

        self.timeout_add(1 / fan_frame_rate, self.turn)

    def calculate_length(self):
        if not self.text:
            return 0

        return self.text_offset + self.layout.width + self.padding * 2

    def draw(self):
        if not self.can_draw():
            return

        self.drawer.clear(self.background or self.bar.background)

        if self.text:
            ctx = self.drawer.ctx
            ctx.save()
            self.select_glyph_font()
            self.drawer.set_source_rgb(self.foreground)
            ctx.translate(self.padding + self.hub[0], self.bar.size / 2)
            ctx.rotate(self.angle)
            ctx.move_to(-self.hub[0], -self.hub[1])
            ctx.show_text(self.glyph)
            ctx.restore()

            y = (self.bar.size - self.layout.height) / 2 + 1
            self.layout.draw(self.padding + self.text_offset, y)

        self.draw_at_default_position()


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


def fans():
    return Fan(**base(fg="color1"), update_interval=5)


def bluetooth():
    return GenPollText(
        **base(fg="color1"),
        func=bluetooth_text,
        update_interval=5,
        mouse_callbacks={"Button1": applet("bluetooth-menu.sh")},
    )


def network():
    return GenPollText(
        **base(fg="color1"),
        func=network_text,
        update_interval=5,
        mouse_callbacks={"Button1": applet("wifi-menu.sh")},
    )


def music():
    """What the current MPRIS player is playing. Empty - and so invisible -
    while nothing is, since ``stopped_text`` and ``no_metadata_text`` are
    what qtile falls back on then."""
    return Mpris2(
        **base(fg="color4"),
        name="music",
        format="{xesam:title} · {xesam:artist}",
        playing_text="󰝚 {track}",
        paused_text="󰏤 {track}",
        stopped_text="",
        no_metadata_text="",
        scroll=False,
        max_chars=25,
        mouse_callbacks={
            "Button1": lazy.widget["music"].play_pause(),
            "Button4": lazy.widget["music"].previous(),
            "Button5": lazy.widget["music"].next(),
        },
    )


def notifications():
    """qtile's own notification server.

    Nothing else on this machine owns ``org.freedesktop.Notifications``, so
    without this every ``notify-send`` - the bar's menus report their failures
    with one - times out unheard. Click to dismiss, right-click to follow the
    notification's own action, scroll through a backlog.
    """
    return Notify(
        **base(fg="color7"),
        default_timeout=8,
        default_timeout_urgent=15,
        foreground_low=shade("color7", 0.6),
        foreground_urgent=colors["urgent"][0],
        background_low=colors["dark"][0],
        background_urgent=colors["dark"][0],
        max_chars=40,
    )


def trayed():
    """The X11 system tray, followed by a gap that comes and goes with it.

    Only one tray may exist across every bar, and it hosts real client windows
    rather than text, so it sits outside the Centred family and takes its size
    in pixels rather than from the font.
    """
    icons = Systray(background=colors["dark"], icon_size=20, padding=8)
    return [icons, collapsing_gap(icons)]


def workspaces():
    return widget.GroupBox(
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
    )


# A rule that comes and goes has to be told what it is spacing, so the
# widgets it introduces exist before the list that places them.
music_playing = music()
notified = notifications()

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
    *collapsing_divided(music_playing),
    music_playing,
    *collapsing_divided(notified),
    notified,
    # All the slack in the bar lives here, so the left-hand readouts keep
    # their place while the music has room to grow into.
    widget.Spacer(**base()),
    workspaces(),
    widget.Spacer(**base()),
    gap(14),
    # The tray is empty until an application plants an icon in it, so it
    # takes up no room on the bar until one does.
    *trayed(),
    *spaced(
        cpu(),
        gpu(),
        fans(),
        Memory(**base(fg="color6"), format="  {MemPercent}%"),
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


def secondary_widgets():
    """A slimmer bar for every other monitor. A widget can only live in one
    bar, so each screen needs its own fresh set - and the tray, notification
    server and system readouts stay on the laptop's bar, since there can only
    be one tray and one notification server."""
    return [
        bar_edge_separator(),
        logo(),
        *divided(left=10, right=9),
        Clock(**base(fg="color1"), format="%A %d %B %H:%M %p"),
        widget.Spacer(**base()),
        workspaces(),
        widget.Spacer(**base()),
        bar_edge_separator(),
    ]


widget_defaults = {
    "font": "JetBrainsMono Nerd Font Bold",
    "fontsize": 15,
    "padding": 0,
}

extension_defaults = widget_defaults.copy()
