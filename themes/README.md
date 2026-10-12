A theme consists of a simple json file. You can create your own by copying this
json object and changing values:

```json
{
    "terminal": "Nord",
    "dark": [
        "#0f101a",
        "#0f101a"
    ],
    "grey": [
        "#353c4a",
        "#353c4a"
    ],
    "light": [
        "#f1ffff",
        "#f1ffff"
    ],
    "text": [
        "#0f101a",
        "#0f101a"
    ],
    "focus": [
        "#a151d3",
        "#a151d3"
    ],
    "active": [
        "#f1ffff",
        "#f1ffff"
    ],
    "inactive": [
        "#4c566a",
        "#4c566a"
    ],
    "urgent": [
        "#F07178",
        "#F07178"
    ],
    "color1": [
        "#a151d3",
        "#a151d3"
    ],
    "color2": [
        "#F07178",
        "#F07178"
    ],
    "color3": [
        "#fb9f7f",
        "#fb9f7f"
    ],
    "color4": [
        "#ffd47e",
        "#ffd47e"
    ]
}

```

`terminal` is optional: it names the [ghostty](https://ghostty.org) theme to
use alongside this one (`ghostty +list-themes`). Leave it out and the terminal
colours are picked from the theme's own by hue. Either way the terminal takes
the bar's `dark` as its background; `scripts/apply-theme.py` does this on
every qtile start and reload.

rofi takes `~/.config/rofi/<name>.rasi` as its palette when there is one, and
otherwise one made from the theme's colours. The login screen
(`~/.config/sddm`) takes the colours as they are, plus
`background-<name>.jpg` from its theme folder if there is one.

`catppuccin-mocha` is Catppuccin's palette with the accents pulled 18% of the
way towards base, and green and peach traded for teal and flamingo, so the bar
stays as quiet as it is in Kanagawa. The terminal keeps the real palette.
