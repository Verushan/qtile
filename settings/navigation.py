# Moving focus and windows across monitors as if they were one desk.
#
# The layout's own h/l stop dead at the edge of a monitor. These carry on
# onto the monitor that physically sits that way, so the keys go where the
# eyes do. Screens are found by where they are, not by qtile's numbering,
# which follows the order xrandr lists them in rather than left to right.

from libqtile.lazy import lazy

from . import desktops


def screen_towards(qtile, direction):
    """The nearest monitor to the left or right of the focused one."""
    here = qtile.current_screen

    if direction == "left":
        candidates = [s for s in qtile.screens if s.x + s.width <= here.x]
        return max(candidates, key=lambda s: s.x, default=None)

    candidates = [s for s in qtile.screens if s.x >= here.x + here.width]
    return min(candidates, key=lambda s: s.x, default=None)


def anything_towards(qtile, direction):
    """Whether a tiled window on this monitor lies that way of the focused
    one - the same question the Bsp layout asks before it moves anywhere.
    Max stacks every window in the same spot, so it never has a neighbour."""
    window = qtile.current_window
    if window is None or window.floating:
        return False

    others = [w for w in qtile.current_group.windows if w is not window and not w.floating]
    if direction == "left":
        return any(w.x + w.width <= window.x for w in others)

    return any(w.x >= window.x + window.width for w in others)


def arrive(qtile, screen, window=None):
    """Put focus on a monitor - on ``window`` if given - and bring the
    pointer along. Without the pointer, focus-follows-mouse hands focus
    straight back to whatever the cursor was left resting on."""
    qtile.focus_screen(screen.index, warp=False)
    if window is not None:
        screen.group.focus(window, warp=False)

    window = qtile.current_window
    if window is None:
        qtile.warp_to_screen()
    else:
        window.window.warp_pointer(window.width // 2, window.height // 2)


@lazy.function
def focus(qtile, direction):
    """Focus the window that way, or the monitor that way once at the edge."""
    if anything_towards(qtile, direction):
        getattr(qtile.current_layout, direction)()
        return

    screen = screen_towards(qtile, direction)
    if screen is not None:
        arrive(qtile, screen)


@lazy.function
def shuffle(qtile, direction):
    """Swap the window that way, or carry it onto the monitor that way once
    it is already against the edge."""
    if anything_towards(qtile, direction):
        getattr(qtile.current_layout, f"shuffle_{direction}")()
        return

    move_to_screen(qtile, direction)


def move_to_screen(qtile, direction):
    window = qtile.current_window
    screen = screen_towards(qtile, direction)
    if window is None or screen is None:
        return

    window.togroup(screen.group.name)
    arrive(qtile, screen, window)


@lazy.function
def focus_screen(qtile, direction):
    screen = screen_towards(qtile, direction)
    if screen is not None:
        arrive(qtile, screen)


@lazy.function
def send_to_screen(qtile, direction):
    move_to_screen(qtile, direction)


@lazy.function
def go_to_desktop(qtile, desktop):
    desktops.switch(qtile, desktop)


@lazy.function
def send_to_desktop(qtile, desktop):
    """Move the window to another desktop, keeping it on the same monitor.
    Like Windows, you stay where you are - it is waiting there for you."""
    window = qtile.current_window
    if window is not None:
        window.togroup(desktops.group_name(desktop, desktops.monitor_of(qtile, window)))
