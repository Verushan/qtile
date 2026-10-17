# Desktops that span every monitor, the way Windows 11's virtual desktops do.
#
# qtile's own groups are one screen wide: showing one on a monitor takes it
# off whichever monitor had it, so the windows in it jump across. Here each
# desktop is instead a row of groups, one pinned to each monitor. Switching
# desktop switches every monitor at once, and each monitor comes back to
# exactly what it was showing on that desktop.

from libqtile import hook
from libqtile.config import Group
from libqtile.scratchpad import ScratchPad

DESKTOPS = 9

# Groups and bars are made for this many monitors whether or not they are
# plugged in, so one that turns up later has somewhere to go straight away.
MONITORS = 3

# Windows a notification has asked attention for, by id. Kept apart from a
# window's own urgency, which qtile recomputes from the window's state each
# time the app touches it - Brave does so constantly - and so would wipe it.
attention = set()


def wants_attention(window):
    return window.urgent or window.wid in attention


def group_name(desktop, monitor):
    return f"{desktop}:{monitor}"


def parse(name):
    """The (desktop, monitor) a group belongs to, or None for any other group."""
    desktop, _, monitor = name.partition(":")
    if desktop.isdigit() and monitor.isdigit():
        return int(desktop), int(monitor)

    return None


def groups():
    # Ordered desktop by desktop, so at startup each monitor is handed its
    # own group of the first desktop.
    return [
        Group(group_name(desktop, monitor), label=str(desktop), screen_affinity=monitor)
        for desktop in range(1, DESKTOPS + 1)
        for monitor in range(MONITORS)
    ]


def current(qtile):
    """The desktop on show, read off the first monitor - the one that stays
    put when others come and go, and so keeps its group through it."""
    owner = parse(qtile.screens[0].group.name)
    return owner[0] if owner else 1


def switch(qtile, desktop):
    """Put every monitor on ``desktop``, keeping focus on the monitor it is
    on. The focused monitor is switched last so that its window ends up
    with the focus."""
    here = qtile.current_screen
    others = [screen for screen in qtile.screens if screen is not here]

    for screen in [*others, here]:
        group = qtile.groups_map.get(group_name(desktop, screen.index))
        if group is not None and screen.group is not group:
            screen.set_group(group, warp=False)

    # Arriving answers whatever on the desktop was asking for attention, not
    # just the one window that ends up focused.
    for screen in qtile.screens:
        for window in screen.group.windows:
            if wants_attention(window):
                window.urgent = False
                attention.discard(window.wid)
                hook.fire("client_urgent_hint_changed", window)


def monitor_of(qtile, window):
    """The monitor a window's desktop group is pinned to."""
    owner = parse(window.group.name) if window.group else None
    return owner[1] if owner else qtile.current_screen.index


def settle(qtile):
    """Line every monitor up on one desktop and gather up stray windows.

    A window can be left outside the desktops - in a group from before this
    scheme, or on a monitor that has since been unplugged. Each one moves to
    the same desktop on a monitor that is still here, the way Windows hands
    an unplugged monitor's windows to the one that remains.
    """
    # qtile tells screens apart by where they are, so once a monitor is gone
    # and the laptop has slid into its spot, the gone monitor's group still
    # looks to be on show - and is passed over when the monitor comes back.
    for group in qtile.groups:
        if group.screen is not None and not any(group.screen is s for s in qtile.screens):
            group.hide()

    # A reload hands each group back the label it had before, so a change
    # of label would otherwise wait for the next login.
    for group in qtile.groups:
        owner = parse(group.name)
        if owner:
            group.label = str(owner[0])

    desktop = current(qtile)
    shown_on = {screen.group.name: screen.index for screen in qtile.screens}
    switch(qtile, desktop)

    for group in list(qtile.groups):
        if isinstance(group, ScratchPad):
            continue

        owner = parse(group.name)
        if owner and owner[1] < len(qtile.screens):
            continue

        if owner:
            home = group_name(owner[0], 0)
        else:
            home = group_name(desktop, min(shown_on.get(group.name, 0), MONITORS - 1))

        for window in list(group.windows):
            window.togroup(home)

        if owner is None:
            qtile.delete_group(group.name)
