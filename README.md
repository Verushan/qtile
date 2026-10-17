# qtile

My [qtile](https://qtile.org) desktop: a single bar with live hardware readouts,
click-to-open menus for the session, Wi-Fi and Bluetooth, BSP tiling with gaps,
drop-down scratchpads and rotating wallpapers.

![Desktop](screenshots/desktop.png)

## The bar

![Left of the bar](screenshots/bar-left.png)
![Right of the bar](screenshots/bar-right.png)

Everything on the bar is live, and the icons that make sense to click, do.

| Widget | Shows | Click |
| --- | --- | --- |
| Distro mark | – | Session menu: lock, suspend, log out, restart, shut down |
| Clock | Day, date and time | |
| Network | The connected Wi-Fi/ethernet name, or *Offline* | Wi-Fi menu: pick a network, rescan, toggle the radio |
| Bluetooth | The connected device (+ how many more); icon shades by state | Bluetooth menu: connect, pair, disconnect, toggle power |
| Music | A play/pause icon for the current MPRIS player (hidden when nothing is playing); hover for the track, artist and player | Play/pause; scroll for previous/next |
| Notifications | qtile's own notification server, so `notify-send` works without a separate daemon. Nothing on the bar: each notification drops down as a toast below the bar's right end, and any desktop out of sight with a window of the app that sent it has its number lit up | Click the toast to dismiss; right-click follows the notification's action |
| Workspaces | One dot per workspace that has windows | |
| System tray | Application tray icons (takes no space while empty) | |
| CPU | Load and package temperature (turns red at 90 °C) | |
| GPU | NVIDIA load and temperature; dims to just the icon while the card is powered down, and never wakes it to ask | |
| Fans | RPM of every chassis fan, behind an icon that spins in proportion to how hard they're working | |
| Memory | Used RAM | |
| Volume | Level, with an icon that tracks it | Opens `pavucontrol` |
| Battery | Charge and charger state | |

## Layout and workspaces

- **Layouts:** BSP (`Mod+Tab` cycles to Max and back).
- **Workspaces:** nine of them, `Mod+1`…`Mod+9`; only the ones with windows in
  them appear on the bar.
- **Scratchpads:** a terminal, a mixer and a file manager that drop down over
  whatever you're doing and hide again with the same key.
- **Gaps and borders** are set in `config.json`; the focused window gets the
  theme's `active` colour.

## Requirements

Arch package names; anything marked *optional* is skipped gracefully when it
isn't there.

| For | Packages |
| --- | --- |
| The window manager | `qtile`, `python-psutil` |
| Font | `ttf-jetbrains-mono-nerd` (every icon on the bar, distro mark included, comes from it) |
| Menus | `rofi` |
| Compositor and wallpaper | `picom`, `feh`, `imagemagick` |
| Wi-Fi and Bluetooth readouts/menus | `networkmanager`, `bluez-utils` |
| Volume and brightness keys | `alsa-utils`, `libpulse` (`pactl`), `pavucontrol`, `brightnessctl` |
| Default applications | `ghostty`, `firefox`, `dolphin`, `flameshot` |
| GPU readout (*optional*) | `nvidia-utils` (`nvidia-smi`) |
| Lock screen (*optional*) | any of `betterlockscreen`, `i3lock`, `xsecurelock`, `slock` |

## Install

```sh
git clone git@github.com:Verushan/qtile.git ~/.config/qtile
cd ~/.config/qtile
cp default-config.json config.json   # then edit to taste
```

Put some wallpapers in `~/Pictures/Victus` (or point `wallpapers=` in
`autostart.sh` somewhere else), then log in to qtile — or, if it's already
running, `Mod+Ctrl+R` reloads the config in place.

## Configuration

`config.json` holds the few things worth changing without touching Python:

```json
{
    "theme": "kanagawa-dragon",
    "border-width": 2,
    "gap": 10,
    "primary-monitor": "external",
    "external-monitor-side": "left",
    "external-scale": 1
}
```

- **theme** – the name of a file in `themes/`. `kanagawa-dragon`,
  `catppuccin-mocha` and `nord` are included; `themes/README.md` explains the
  handful of colours a theme needs if you want to add your own. The terminal
  (ghostty, and fish through it) and rofi follow the theme on the next reload;
  the login screen follows once you run `sudo ~/.config/sddm/install.sh`.
- **border-width** – window border, in pixels.
- **gap** – space between windows and around the screen, in pixels.
- **primary-monitor** – `external` or `laptop`: which screen is primary while
  a monitor is plugged in. The primary screen carries the full bar (tray,
  notifications, system readouts) and is where windows gather when monitors
  come and go; the others get a slim bar. Without a monitor the laptop is
  always primary.
- **external-monitor-side** – `left` or `right`: which side of the laptop
  external monitors sit on, so the cursor and `Mod+H/L` cross over the edge
  they physically meet.
- **external-scale** – how big things look on an external monitor. `match`
  makes them the same physical size as on the laptop, so a big monitor with
  big pixels shows more rather than everything blown up; `1` leaves the
  monitor at its native pixels; a number like `0.8` draws things at that
  share of their native size. X11 can only do this by drawing the monitor's
  desktop larger and having the GPU shrink it to fit, so text there is a
  touch softer, and a fullscreen game renders the larger size too. It needs
  the monitor to hang off the Intel GPU (the USB-C/DisplayPort outputs): the
  HDMI port belongs to the NVIDIA card, which shows the larger desktop
  unshrunk, running off the edge of the monitor - keep `1` there.

Monitors take care of themselves: each one is switched on at its native
resolution and fastest refresh rate as soon as it is plugged in, and switched
off when it is pulled out. Run `scripts/monitors.py` to apply a change to
these settings straight away.

Default programs (`terminal`, `browser`, `file_explorer`) live at the top of
`settings/keys.py`. The wallpaper folder and how often it changes are the first
two lines of `autostart.sh`; `scripts/wallpaper.sh` pulls overly bright
pictures down so text on top of them stays readable.

### Hardware readouts

The bar reads its sensors through `psutil`, so it works on anything the kernel
exposes as hwmon, but a couple of things are tuned to the laptop it was written
on (an HP Victus 15):

- **Fans** – the icon's spin is scaled to a full-speed reading of
  `fan_max_rpm = 5400` in `settings/widgets.py`. On another machine, force
  your fans to full (`pwm1_enable=0` on hp-wmi, or a stress test), read the
  peak, and put that number in. With no fan sensor at all the widget hides.
- **CPU temperature** comes from the `coretemp` *Package id* sensor (Intel).
  On AMD, swap that for `k10temp`'s `Tctl` in `cpu_temperature()`.
- **GPU** expects an NVIDIA card; without `nvidia-smi` it shows a dimmed icon.

## Keybindings

`Mod` is the Super/Windows key.

### Windows

| Keys | Action |
| --- | --- |
| `Mod+H/J/K/L` | Focus left / down / up / right — `H`/`L` carry on to the next monitor at the edge |
| `Mod+Shift+H/J/K/L` | Move window left / down / up / right — `H`/`L` push it onto the next monitor at the edge |
| `Mod+Ctrl+H/J/K/L` | Grow window left / down / up / right |
| `Mod+Shift+F` | Toggle floating |
| `Mod+Shift+M` | Toggle fullscreen |
| `Mod+Shift+Q` | Close window |
| `Mod+Tab` / `Mod+Shift+Tab` | Next / previous layout |
| `Mod+Drag` (left button) | Move floating window |
| `Mod+Drag` (right button) | Resize floating window |
| `Mod+Middle-click` | Bring window to front |

### Desktops and monitors

Like Windows 11's virtual desktops, each desktop spans every monitor: switching
desktop switches all of them, and each monitor comes back to whatever it had
open there. Each bar numbers every desktop that has a window open, by the key
that reaches it: bright where that desktop has windows on this monitor, dim
where they are all on another, and the desktop on show sits in a block. A
desktop whose number turns the urgent colour has something asking for you - a
window wanting attention, or a notification from an app with a window there -
and stays lit until you go to it.
Docking moves the open windows onto the primary monitor, and undocking brings
everything back to the laptop.

| Keys | Action |
| --- | --- |
| `Mod+1`…`9` | Switch every monitor to desktop N |
| `Mod+Shift+1`…`9` | Send window to desktop N, on the monitor it is on |
| `Mod+,` / `Mod+.` | Focus the monitor to the left / right |
| `Mod+Shift+,` / `Mod+Shift+.` | Send window to the monitor to the left / right |

### Scratchpads

| Keys | Drops down |
| --- | --- |
| `Mod+Shift+Enter` | Terminal |
| `Mod+Shift+V` | Mixer (`alsamixer`) |
| `Mod+Shift+E` | File manager |

### Applications

| Keys | Action |
| --- | --- |
| `Mod+Enter` | Terminal |
| `Mod+B` | Browser |
| `Mod+E` | File manager |
| `Mod+P` | Application launcher (`rofi -show drun`) |
| `Mod+Shift+P` | Window switcher |
| `Mod+Shift+S` | Screenshot (`flameshot`) |

### Hardware

| Keys | Action |
| --- | --- |
| `Mod+Up` / `Mod+Down` | Volume up / down |
| `Mod+M` | Mute |
| `Mod+Right` / `Mod+Left` | Brightness up / down |

### qtile

| Keys | Action |
| --- | --- |
| `Mod+Ctrl+R` | Reload config |
| `Mod+Ctrl+Q` | Quit qtile |

## Layout of the repo

```
config.py            entry point; pulls everything from settings/
settings/
  widgets.py         the bar and every widget on it
  keys.py            keybindings and default programs
  groups.py          desktop keys and scratchpads
  desktops.py        desktops that span every monitor
  navigation.py      moving focus and windows across monitors
  layouts.py         BSP and Max
  screens.py         a bar for each monitor
  theme.py           loads themes/<name>.json
scripts/
  power-menu.sh      session menu (rofi)
  wifi-menu.sh       Wi-Fi menu (rofi + nmcli)
  bluetooth-menu.sh  Bluetooth menu (rofi + bluetoothctl)
  wallpaper.sh       picks and dims a wallpaper
  monitors.py        lays out monitors, and again whenever one is plugged in
  menu.sh            shared rofi helpers
  apply-theme.py     carries the theme over to ghostty and rofi
autostart.sh         monitors, wallpaper rotation, picom, screen-blanking off
themes/              colour schemes
```

## Credits

The `settings/` split started from
[Antonio Sarosi's dotfiles](https://github.com/antoniosarosi/dotfiles).
Licensed under the [MIT License](LICENSE).
