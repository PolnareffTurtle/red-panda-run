"""Rules the browser build depends on, checked without running the game.

Desktop Python is happy to break all of these, so nothing else would catch them before itch.io.
See https://pygame-web.github.io/wiki/pygbag/ and the pygbag section of CLAUDE.md.
"""

import ast
import fnmatch
from pathlib import Path

import pytest

GAME_DIR = Path(__file__).resolve().parents[2] / "game"
ASSETS = GAME_DIR / "assets"
MUSIC = ASSETS / "music"
IMAGES = ASSETS / "images"

# what the game imports today. pygbag only ships part of the stdlib, and packages need extra
# setup, so a new import should be a decision (and tested in the browser), not an accident
ALLOWED_IMPORTS = {
    "asyncio",
    "collections",
    "enum",
    "json",
    "math",
    "os",
    "pygame",
    "random",
    "src",
    "sys",
}
BLOCKING_CALLS = {
    "input",
    "pygame.event.wait",
    "pygame.time.delay",
    "pygame.time.wait",
    "time.sleep",
}
# the keys src/keys.py groups into sets. K_ESCAPE and the like are fine to compare directly
GROUPED_KEYS = {
    f"K_{name}"
    for name in (
        *("UP", "DOWN", "LEFT", "RIGHT", "RETURN", "KP_ENTER"),
        *("w", "a", "s", "d", "KP8", "KP2", "KP4", "KP6"),
    )
}
UNSUPPORTED_EXTENSIONS = {".wav", ".aiff", ".aif", ".m4a", ".mp3", ".bmp"}
MAX_ASSETS_MB = 40

SOURCES = [GAME_DIR / "main.py", *sorted((GAME_DIR / "src").rglob("*.py"))]
TREES = {path: ast.parse(path.read_text(encoding="utf-8")) for path in SOURCES}


def label(path):
    return str(path.relative_to(GAME_DIR))


def game_files():
    # game/build is pygbag's output, not something that gets packaged
    build = GAME_DIR / "build"
    return [
        path
        for path in GAME_DIR.rglob("*")
        if path.is_file() and build not in path.parents and "__pycache__" not in path.parts
    ]


def calls(tree):
    return [ast.unparse(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)]


@pytest.fixture(params=SOURCES, ids=label)
def tree(request):
    return TREES[request.param]


def music_files():
    return [path for path in MUSIC.iterdir() if path.name != ".DS_Store"]


def test_there_is_music():
    # Music picks a random track at startup, which crashes on an empty folder
    assert music_files()


@pytest.mark.parametrize("path", music_files(), ids=lambda path: path.name)
def test_music_is_really_ogg(path):
    assert path.suffix == ".ogg"
    # the file's own header, so a renamed mp3 doesn't get through
    assert path.read_bytes()[:4] == b"OggS"


def test_no_unsupported_file_formats():
    assert not [f for f in game_files() if f.suffix.lower() in UNSUPPORTED_EXTENSIONS]


@pytest.mark.parametrize("folder", ["background", "player", "wind_anim"])
def test_load_images_folders_only_hold_pngs(folder):
    # load_images loads everything in the folder but .DS_Store
    files = [f for f in (IMAGES / folder).rglob("*") if f.is_file() and f.name != ".DS_Store"]
    assert files
    assert not [f for f in files if f.suffix != ".png"]


def test_no_reserved_file_names():
    assert not [f for f in game_files() if fnmatch.fnmatch(f.name, "*-pygbag.*")]


def test_assets_stay_small_enough_to_download():
    size = sum(f.stat().st_size for f in ASSETS.rglob("*") if f.is_file())
    assert size < MAX_ASSETS_MB * 1024 * 1024


def test_imports_are_available_in_the_browser(tree):
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.add(node.module.split(".")[0])
    assert modules <= ALLOWED_IMPORTS


def test_no_blocking_calls(tree):
    assert not BLOCKING_CALLS & set(calls(tree))


def test_no_print(tree):
    assert "print" not in calls(tree)


def test_inputs_go_through_the_key_sets():
    for path, tree in TREES.items():
        if path.name == "keys.py":
            continue
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        assert not names & GROUPED_KEYS, label(path)


def test_source_parses_as_python_312():
    # pygbag's runtime is CPython 3.12, whatever version runs the tests
    for path in SOURCES:
        ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 12))


@pytest.mark.parametrize(
    "path", sorted((GAME_DIR / "src" / "scenes").glob("*.py")), ids=lambda path: path.name
)
def test_scenes_never_loop(path):
    # a scene that waits in a loop never gets back to the frame loop's yield
    assert not [n for n in ast.walk(TREES[path]) if isinstance(n, ast.While)]


def async_functions():
    tree = TREES[GAME_DIR / "main.py"]
    return {n.name: n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)}


def test_frame_loops_await_next_frame():
    functions = async_functions()
    loops = [
        (name, loop)
        for name, function in functions.items()
        for loop in ast.walk(function)
        if isinstance(loop, ast.While)
    ]
    assert {name for name, _ in loops} == {"run", "transition_out"}
    for name, loop in loops:
        awaited = [ast.unparse(n.value) for n in ast.walk(loop) if isinstance(n, ast.Await)]
        assert "self.next_frame()" in awaited, name


def test_next_frame_yields_to_the_browser():
    function = async_functions()["next_frame"]
    awaited = [ast.unparse(n.value) for n in ast.walk(function) if isinstance(n, ast.Await)]
    assert "asyncio.sleep(0)" in awaited


def test_asyncio_run_is_the_last_statement():
    # pygbag doesn't run anything after it
    last = TREES[GAME_DIR / "main.py"].body[-1]
    assert isinstance(last, ast.If)
    assert calls(last.body[-1])[0] == "asyncio.run"
