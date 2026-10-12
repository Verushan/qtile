# Qtile Config File
# http://www.qtile.org/

from libqtile import hook, qtile
from settings.keys import mod, keys
from settings.groups import groups
from settings.layouts import layouts, floating_layout
from settings.widgets import widget_defaults, extension_defaults
from settings.screens import screens
from settings.mouse import mouse
from settings.path import qtile_path
from os import path
import subprocess


@hook.subscribe.startup_once
def autostart():
    subprocess.call([path.join(qtile_path, "autostart.sh")])


@hook.subscribe.startup
def runner():
    subprocess.Popen(["xsetroot", "-cursor_name", "left_ptr"])
    subprocess.Popen([path.join(qtile_path, "scripts", "apply-theme.py")])


# Chromium-based browsers tag new windows with the workspace they were last on
# (_NET_WM_DESKTOP), which qtile honours. Pull them into the current group instead.
open_on_current_group = ("brave-browser",)
startup_done = False


@hook.subscribe.startup
def mark_startup_done():
    global startup_done
    startup_done = True


@hook.subscribe.client_new
def open_on_current(window):
    # Leave windows alone while qtile re-adopts them after a restart
    if not startup_done:
        return

    wm_class = [name.lower() for name in window.get_wm_class() or []]
    if any(name in open_on_current_group for name in wm_class):
        window.togroup(qtile.current_group.name)


main = None
dgroups_key_binder = None
dgroups_app_rules = []
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
auto_fullscreen = True
focus_on_window_activation = "urgent"
wmname = "L3GD"
