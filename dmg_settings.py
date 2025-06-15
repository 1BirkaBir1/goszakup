# dmg_settings.py

import os

application = "ParserZakupok.app"

volume_name = "ParserZakupok"
icon_locations = {
    application: (140, 120),
    "Applications": (380, 120)
}

background = None  # можно указать путь к картинке, если нужно

settings = {
    'volume-icon': None,
    'icon-size': 100,
    'window-size': (520, 300),
    'window-pos': (200, 100),
    'icon-locations': icon_locations,
    'background': background,
    'show-status-bar': False,
    'show-tab-view': False,
    'show-toolbar': False,
    'hide-extension': True
}
