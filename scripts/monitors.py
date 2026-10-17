#!/usr/bin/env python3
"""Lay the monitors out, and keep them laid out as they come and go.

Run plainly, it sets up whatever is plugged in right now: every monitor on at
its native resolution and the fastest refresh rate it offers there, external
ones beside the laptop on the side `config.json` names, and the primary one
picked by `config.json` too. An external monitor with bigger pixels than the
laptop's is drawn with more desktop squeezed onto it, so that things come
out the same size on it as they do on the laptop rather than larger. qtile treats the primary monitor as its first
screen, so that is the one with the full bar and the one windows gather on.
Monitors that have been unplugged are switched off, so nothing is left
drawing to a screen that is not there.

Run with --watch WALLPAPERS, it waits for monitors to be plugged in or
pulled out and lays them out again each time, then hangs a fresh wallpaper
from WALLPAPERS across them. X does none of this by itself: a monitor that turns up stays dark until
something gives it a mode, and one that goes keeps its share of the desktop.
"""

import fcntl
import json
import math
import os
import re
import subprocess
import sys
from os import path

qtile_path = path.dirname(path.dirname(path.realpath(__file__)))

# Laptop panels go by these names; everything else is an external monitor.
internal_prefixes = ("eDP", "LVDS", "DSI")


def settings():
    """The monitor settings from config.json, falling back to the defaults
    for a config that predates them."""
    chosen = {
        "primary-monitor": "external",
        "external-monitor-side": "left",
        "external-scale": 1,
    }
    try:
        with open(path.join(qtile_path, "config.json")) as f:
            config = json.load(f)
    except (OSError, ValueError):
        return chosen

    return {key: config.get(key, default) for key, default in chosen.items()}


def outputs():
    """Every output xrandr knows of, in its order, as dicts of name,
    connected, active, physical width in millimetres, and the native
    resolution with its fastest rate.

    xrandr lists an output's native resolution first, its rates after it,
    marked * for the current one and + for the preferred one.
    """
    found = []
    query = subprocess.run(["xrandr", "--query"], capture_output=True, text=True, check=True)

    for line in query.stdout.splitlines():
        header = re.match(r"(\S+) (connected|disconnected)\b(.*)", line)
        if header:
            name, state, rest = header.groups()
            found.append(
                {
                    "name": name,
                    "connected": state == "connected",
                    # An output in use has its geometry before the bracket.
                    "active": bool(re.search(r"\d+x\d+\+\d+\+\d+", rest.split("(")[0])),
                    "mm": int(re.search(r"(\d+)mm x", rest).group(1)) if "mm x" in rest else 0,
                    "mode": None,
                    "rate": None,
                }
            )
            continue

        mode = re.match(r"\s+(\d+x\d+)\s+(\d.*)", line)
        if mode and found and found[-1]["mode"] is None:
            rates = [float(rate.strip("*+")) for rate in mode.group(2).split() if rate != "+"]
            found[-1]["mode"] = mode.group(1)
            found[-1]["rate"] = f"{max(rates):.2f}"

    return found


def stretch(output, laptop, setting):
    """How much desktop to draw on an output for each of its pixels.

    1 leaves it alone. "match" draws an external monitor so that things are
    the same size on it as on the laptop: its pixels are bigger by the ratio
    of the two pixel widths, so it is given that much more desktop. A number
    is how big things should look against the monitor's own pixels, so 0.75
    draws them at three quarters of their size. A monitor with smaller
    pixels than the laptop's is never blown up to match, as that only blurs
    it.
    """
    if output is laptop or setting in (None, 1, "none"):
        return 1.0

    if setting == "match":
        if laptop is None or not output["mm"] or not laptop["mm"]:
            return 1.0

        def pitch(o):
            return o["mm"] / int(o["mode"].split("x")[0])

        return max(pitch(output) / pitch(laptop), 1.0)

    return max(1 / float(setting), 1.0)


def arrange():
    config = settings()
    every = outputs()
    connected = [o for o in every if o["connected"] and o["mode"]]
    laptop = next((o for o in connected if o["name"].startswith(internal_prefixes)), None)
    externals = [o for o in connected if o is not laptop]

    if not connected:
        return

    if externals and (config["primary-monitor"] == "external" or laptop is None):
        primary = externals[0]
    else:
        primary = laptop

    command = ["xrandr"]

    for output in every:
        if output["active"] and output not in connected:
            command += ["--output", output["name"], "--off"]

    # Externals line up beside the laptop, each one further out than the
    # last. Positions are worked out here rather than with --left-of, which
    # places outputs by their pixels and so overlaps a scaled one.
    row = [o for o in [laptop] if o] + externals
    if config["external-monitor-side"] != "right":
        row.reverse()

    x = 0
    for output in row:
        scale = stretch(output, laptop, config["external-scale"])
        width, _ = (int(n) for n in output["mode"].split("x"))
        command += ["--output", output["name"], "--mode", output["mode"], "--rate", output["rate"]]
        command += ["--scale", f"{scale:.4f}x{scale:.4f}", "--pos", f"{x}x0"]
        if output is primary:
            command.append("--primary")
        x += math.ceil(width * scale)

    # One call, so qtile sees the finished layout rather than every step.
    subprocess.run(command, check=False)


def connected_outputs(conn, randr, root):
    """The names of plugged-in outputs, asked of X without making it probe
    the hardware again the way `xrandr --query` does."""
    resources = randr.GetScreenResourcesCurrent(root).reply()
    names = set()
    for output in resources.outputs:
        info = randr.GetOutputInfo(output, resources.config_timestamp).reply()
        if info.connection == xcffib.randr.Connection.Connected:
            names.add(bytes(info.name).decode())

    return names


def watch(wallpapers):
    # One watcher per session is plenty; a second would lay everything out
    # twice over.
    lock = open(path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "qtile-monitors.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return

    conn = xcffib.connect()
    randr = conn(xcffib.randr.key)
    randr.QueryVersion(1, 5).reply()
    root = conn.get_setup().roots[0].root
    randr.SelectInput(root, xcffib.randr.NotifyMask.OutputChange)
    conn.flush()

    known = connected_outputs(conn, randr, root)
    while True:
        # Gives out once the X session ends, and the watcher with it.
        conn.wait_for_event()
        while conn.poll_for_event():
            pass

        # Laying the monitors out sends output events of its own; only a
        # monitor actually arriving or leaving is worth acting on.
        now = connected_outputs(conn, randr, root)
        if now == known:
            continue

        known = now
        arrange()
        subprocess.run([path.join(qtile_path, "scripts", "wallpaper.sh"), wallpapers], check=False)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--watch"]:
        import xcffib
        import xcffib.randr

        watch(sys.argv[2])
    else:
        arrange()
