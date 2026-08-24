# Theming for Qtile

import subprocess
import json

from os import path
from .path import qtile_path
from .config import config


def load_theme():
    theme = config.read_config("theme")
    theme_file = path.join(qtile_path, "themes", f"{theme}.json")

    if not path.isfile(theme_file):
        raise Exception(f'"{theme_file}" does not exist')

    with open(path.join(theme_file)) as f:
        return json.load(f)


if __name__ == "settings.theme":
    colors = load_theme()
