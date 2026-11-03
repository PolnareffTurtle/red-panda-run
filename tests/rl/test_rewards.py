"""Checks the reward functions in rl/compare_rewards.py and the wrapper that applies them."""

import sys
from pathlib import Path

import numpy as np
import pytest
from stable_baselines3.common.env_util import make_vec_env

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "rl"))

from compare_rewards import (  # noqa: E402
    GAMMA,
    REWARDS,
    TIME_PENALTY,
    RewardWrapper,
    Transition,
    evaluate,
    potential,
    progress,
    progress_time,
    sparse,
    time_penalty,
)
from env import MAX_TICKS, RedPandaRunEnv  # noqa: E402
from train import make_model  # noqa: E402

NOTHING, RIGHT = 0, 2


@pytest.fixture(scope="module")
def shared_env():
    return RedPandaRunEnv()


def transition(**changes):
    values = dict(base=0, terminated=False, distance=50, previous=60, closest=60, start=100)
    return Transition(**(values | changes))


@pytest.mark.parametrize("reward", REWARDS.values())
def test_every_reward_ranks_a_win_above_a_death(reward):
    win = transition(base=1, terminated=True)
    death = transition(base=-1, terminated=True)
    assert reward(win) > reward(death)


def test_sparse_is_the_envs_reward():
    assert sparse(transition(base=-1)) == -1


def test_time_penalty_charges_every_step():
    assert time_penalty(transition()) == -TIME_PENALTY


def test_potential_refunds_walking_back_apart_from_discounting():
    there = potential(transition(distance=50, previous=60))
    back = potential(transition(distance=60, previous=50))
    assert there > 0 > back
    # the round trip ends where it began, so all that's left is the discount on the way
    assert there + GAMMA * back == pytest.approx(0.6 * (1 - GAMMA**2))


def test_potential_is_a_telescoping_sum():
    # a whole episode's discounted shaping only depends on where it started
    distances = [100, 70, 90, 40, 10]
    total = 0
    for i, (previous, distance) in enumerate(zip(distances, distances[1:], strict=False)):
        terminated = i == len(distances) - 2
        t = transition(distance=distance, previous=previous, terminated=terminated)
        total += GAMMA**i * potential(t)
    assert total == pytest.approx(1)


def test_progress_only_pays_for_a_new_closest_distance():
    assert progress(transition(distance=50, closest=60)) == pytest.approx(0.1)
    assert progress(transition(distance=55, closest=50)) == 0


def test_progress_time_is_both():
    assert progress_time(transition(distance=60, closest=60)) == -TIME_PENALTY


def test_wrapper_measures_distance_to_the_nearest_bamboo(shared_env):
    shared_env.level = 2
    wrapper = RewardWrapper(shared_env, sparse)
    wrapper.reset()
    x, y = shared_env.game.scene.player.rect().center
    assert wrapper.start == pytest.approx(
        min(np.hypot(x - bx, y - by) for bx, by in wrapper.bamboo)
    )
    assert len(wrapper.bamboo) == 2


def test_wrapper_passes_the_episode_end_through(shared_env):
    shared_env.level = 1
    wrapper = RewardWrapper(shared_env, time_penalty)
    wrapper.reset()
    shared_env.game.scene.win()
    _, reward, terminated, truncated, info = wrapper.step(NOTHING)
    assert reward == 1 - TIME_PENALTY
    assert terminated
    assert not truncated
    assert info["is_success"]


def test_wrapper_truncates_like_the_env(shared_env):
    shared_env.level = 1
    wrapper = RewardWrapper(shared_env, sparse)
    wrapper.reset()
    shared_env.ticks = MAX_TICKS - 1
    assert wrapper.step(NOTHING)[3]


def test_walking_towards_the_bamboo_pays(shared_env):
    shared_env.level = 1
    wrapper = RewardWrapper(shared_env, progress)
    wrapper.reset()
    assert sum(wrapper.step(RIGHT)[1] for _ in range(10)) > 0


def test_evaluate_scores_a_short_training_run(shared_env):
    shared_env.level = 1
    vec_env = make_vec_env(lambda: RewardWrapper(shared_env, potential), n_envs=1)
    model = make_model(vec_env, seed=0)
    score = evaluate(model, shared_env, episodes=2)
    assert score["win"] + score["lose"] + score["timeout"] == 1
