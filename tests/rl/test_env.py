"""Checks the gymnasium env against the game. Needs requirements.txt, so it's its own job."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rl"))

from env import FRAME_SKIP, MAX_TICKS, TILE_CODES, RedPandaRunEnv  # noqa: E402

GAME_DIR = Path(__file__).resolve().parents[2] / "game"
LEVELS = range(1, len(list((GAME_DIR / "assets" / "levels").glob("*.json"))) + 1)

NOTHING, LEFT, RIGHT, JUMP, JUMP_LEFT, JUMP_RIGHT = range(6)


@pytest.fixture(scope="module")
def shared_env():
    # no close(): that quits pygame for everything after this module's tests
    return RedPandaRunEnv()


@pytest.fixture
def env(shared_env):
    shared_env.level = 1
    shared_env.reset()
    return shared_env


def test_env_passes_gymnasium_checks(env):
    check_env(env, skip_render_check=True)


@pytest.mark.parametrize("level", LEVELS)
def test_observations_stay_in_bounds(shared_env, level):
    shared_env.level = level
    obs, _ = shared_env.reset()
    for _ in range(200):
        assert shared_env.observation_space.contains(obs)
        obs, _, terminated, truncated, _ = shared_env.step(shared_env.action_space.sample())
        if terminated or truncated:
            obs, _ = shared_env.reset()


@pytest.mark.parametrize(
    ("action", "movement"),
    [
        (NOTHING, [False, False]),
        (LEFT, [True, False]),
        (RIGHT, [False, True]),
        (JUMP, [False, False]),
        (JUMP_LEFT, [True, False]),
        (JUMP_RIGHT, [False, True]),
    ],
)
def test_actions_move_the_player(env, action, movement):
    env.step(action)
    assert env.game.scene.movement == movement
    assert env.jump_held == (action >= JUMP)


def test_holding_jump_only_jumps_once(env):
    jumps = []
    env.game.scene.player.jump = lambda: jumps.append(1)
    env.step(JUMP)
    env.step(JUMP)
    assert jumps == [1]


def test_each_step_runs_frame_skip_ticks(env):
    env.step(NOTHING)
    assert env.ticks == FRAME_SKIP


@pytest.mark.parametrize(("result", "reward"), [("win", 1), ("lose", -1)])
def test_rewards_end_the_episode(env, result, reward):
    getattr(env.game.scene, result)()
    _, got, terminated, truncated, info = env.step(NOTHING)
    assert got == reward
    assert terminated
    assert not truncated
    assert info["is_success"] == (result == "win")


def test_episode_is_cut_off_at_the_tick_limit(env):
    env.ticks = MAX_TICKS - 1
    _, _, _, truncated, _ = env.step(NOTHING)
    assert truncated


def test_every_tile_type_has_a_code():
    tileset = json.loads((GAME_DIR / "assets" / "redpandarun.json").read_text())
    assert {tile["type"] for tile in tileset["tiles"]} <= set(TILE_CODES)


def test_ppo_trains_saves_and_loads(tmp_path, shared_env):
    vec_env = make_vec_env(lambda: shared_env, n_envs=1)
    model = PPO("MlpPolicy", vec_env, n_steps=64, batch_size=32, device="cpu")
    model.learn(total_timesteps=128)
    path = tmp_path / "model.zip"
    model.save(path)

    obs, _ = shared_env.reset()
    action, _ = PPO.load(path, device="cpu").predict(obs)
    assert shared_env.action_space.contains(int(action))
    assert np.isfinite(obs).all()
