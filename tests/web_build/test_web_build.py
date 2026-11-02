"""Checks the real pygbag output. Needs a build and a browser, so it only runs when named:

    pygbag --build game
    playwright install chromium
    pytest tests/web_build

BUILD_DIR points it at a different build folder. The page loads the Python runtime from pygbag's
CDN, so this needs network access, like the build itself.
"""

import functools
import http.server
import io
import os
import threading
import time
import zipfile
from pathlib import Path

import pygame
import pytest
from playwright.sync_api import sync_playwright

GAME_DIR = Path(__file__).resolve().parents[2] / "game"
BUILD_DIR = Path(os.environ.get("BUILD_DIR", GAME_DIR / "build" / "web"))

STARTUP_TIMEOUT = 120  # seconds for the runtime and game to download and start
SCENE_CHANGE_WAIT = 3000  # milliseconds, long enough for a wipe to finish on a slow machine
CLICK_EVERY = 3  # seconds. Browsers hold audio until a click, so pygbag waits for one to start
MIN_COLORS = 8  # a sample of the canvas with fewer than this is a loading screen, not the game


def bundled_files():
    with zipfile.ZipFile(BUILD_DIR / "game.apk") as apk:
        return {name.removeprefix("assets/") for name in apk.namelist()}


def test_bundle_has_everything_the_game_loads():
    files = bundled_files()
    sources = [GAME_DIR / "main.py", *(GAME_DIR / "src").rglob("*.py")]
    assets = [
        *(GAME_DIR / "assets" / "levels").glob("*.json"),
        *(GAME_DIR / "assets" / "music").glob("*.ogg"),
        GAME_DIR / "assets" / "redpandarun.json",
        GAME_DIR / "assets" / "tileset" / "Assets2.png",
        GAME_DIR / "assets" / "fonts" / "PublicPixel.ttf",
        GAME_DIR / "assets" / "text" / "facts.json",
    ]
    missing = {str(path.relative_to(GAME_DIR)) for path in [*sources, *assets]} - files
    assert not missing


def test_bundle_has_nothing_it_should_not():
    for name in bundled_files():
        assert not name.startswith(("rl/", "tools/", "tests/", "build/")), name
        assert not name.endswith((".DS_Store", ".pyc")), name


@pytest.fixture(scope="module")
def page_url():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(QuietHandler, directory=BUILD_DIR)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}/"
    server.shutdown()


def canvas_image(page):
    return page.locator("#canvas").screenshot()


def color_count(png):
    image = pygame.image.load(io.BytesIO(png))
    width, height = image.get_size()
    pixels = (
        tuple(image.get_at((x * width // 32, y * height // 32)))
        for x in range(32)
        for y in range(32)
    )
    return len(set(pixels))


def wait_for_game_to_draw(page):
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        page.mouse.click(640, 360)
        page.wait_for_timeout(CLICK_EVERY * 1000)
        if color_count(canvas_image(page)) >= MIN_COLORS:
            return
    pytest.fail("the game never drew anything")


def test_game_runs_in_a_browser(page_url):
    # A Python crash doesn't reach the browser console: it goes to pygbag's terminal and the
    # canvas just stops. So this plays into level 1 and checks the picture keeps changing,
    # which the level timer makes it do on every frame
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"]
        )
        page = browser.new_page()
        page_errors = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))
        page.goto(page_url)

        wait_for_game_to_draw(page)
        for _ in range(2):  # main menu to the fact card, then into the level
            page.keyboard.press("Enter", delay=100)
            page.wait_for_timeout(SCENE_CHANGE_WAIT)

        first = canvas_image(page)
        page.wait_for_timeout(1000)
        second = canvas_image(page)
        browser.close()

    assert not page_errors
    assert color_count(second) >= MIN_COLORS
    assert first != second, "the canvas stopped changing, so the game has crashed or hung"
