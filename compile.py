from sys import platform

import PyInstaller.__main__

args = [
    'main_app.py',
    # '--hidden-import=ipsw_parser',
    '--hidden-import=zeroconf',
    '--hidden-import=zeroconf._utils.ipaddress',
    '--hidden-import=zeroconf._handlers.answers',
    '--add-data=files/:./files',
    '--onefile',
    '--name=Nugget',
]

PyInstaller.__main__.run(args)