"""Build FireflyFlight.exe: draws the app icon, then packages the game with PyInstaller.

Usage:
    pip install -r requirements.txt pyinstaller pillow
    python build_app.py
The exe lands in dist/FireflyFlight.exe.
"""

import os
import subprocess
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

from firefly import make_glow  # noqa: E402


def draw_icon(path, size=256):
    """Night-sky tile with a glowing firefly, used for the exe and window icon."""
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    pygame.draw.rect(s, (18, 16, 52), s.get_rect(), border_radius=size // 5)
    glow = make_glow(size // 2, (190, 255, 110), 0.9)
    s.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    k = size / 48  # scale from the in-game 48px bug sprite
    c = size / 2
    pygame.draw.ellipse(s, (170, 190, 235), (c - 9 * k, c - 15 * k, 20 * k, 9 * k))  # wing
    pygame.draw.ellipse(s, (220, 255, 120), (c - 16 * k, c - 6 * k, 20 * k, 16 * k))  # abdomen
    pygame.draw.ellipse(s, (40, 30, 54), (c - 3 * k, c - 7 * k, 14 * k, 12 * k))  # thorax
    pygame.draw.ellipse(s, (64, 42, 76), (c + 6 * k, c - 6 * k, 10 * k, 8 * k))  # head
    pygame.draw.circle(s, (255, 255, 255), (c + 13 * k, c - 3 * k), 2 * k)  # eye
    pygame.image.save(s, path)


def main():
    pygame.init()
    draw_icon("icon.png")
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
        "--name", "FireflyFlight", "--icon", "icon.png",
        "--add-data", f"icon.png{os.pathsep}.",
        "firefly.py",
    ], check=True)


if __name__ == "__main__":
    main()
