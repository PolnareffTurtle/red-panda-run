"""Shared setup. Runs before any test module, so the game can be imported from them."""

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
GAME_DIR = REPO_ROOT / "game"

# no window or sound, on CI or locally
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
sys.path.insert(0, str(GAME_DIR))


def pytest_configure(config):
    # Asset paths are relative to game/, and src/tilemap.py opens one as it's imported. Here, not
    # at the top of this file, because pytest still needs the repo root to find testpaths.
    os.chdir(GAME_DIR)


@pytest.fixture(scope="session")
def session_game():
    from main import Game

    return Game()


@pytest.fixture
def game(session_game):
    # Game() is slow and only one can exist, so tests share it and get it back in a clean state
    from src.scenes.main_menu import MainMenuScene

    session_game.level = 1
    session_game.next_scene = None
    session_game.soundon = True
    session_game.scene = MainMenuScene(session_game)
    return session_game
