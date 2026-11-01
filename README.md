FIREFLY FLIGHT
==============

Guide a glowing firefly through a night forest, between mushroom
stumps and hanging moss. Each gap you pass is one point.

**[Download FireflyFlight.exe for Windows](https://github.com/Shaikhaan/firefly-flight/releases/latest/download/FireflyFlight.exe)**
(no Python needed; all versions on the [Releases page](https://github.com/Shaikhaan/firefly-flight/releases))

Run from source instead:

Setup (once):
    pip install -r requirements.txt

Play:
    python firefly.py

Controls:
    Space / Up / W / left click   flutter
    Esc                           quit

Your best score is saved to firefly_best.txt next to the game.
Tweak gravity, speed and gap size at the top of firefly.py.

Build the Windows app (FireflyFlight.exe):
    pip install -r requirements.txt pyinstaller pillow
    python build_app.py
The exe appears in dist/. It runs without Python installed.
