"""Trains one PPO agent per reward function and compares how well they play. Run from the repo root:

    python rl/compare_rewards.py --level 1 --steps 300000 --seeds 3
    python rl/compare_rewards.py --rewards sparse progress   # only these

To try a new reward, write a function below and add it to REWARDS.

Returns can't be compared between reward functions, so every agent is scored the same way: playing
the plain env and counting wins. Each model is saved to rl/models/<run name>.zip for watch.py.
Tensorboard's ep_rew_mean also stays comparable (see RewardWrapper), so `tensorboard --logdir
rl/runs` shows the runs side by side.
"""

import argparse
import time
from dataclasses import dataclass

import gymnasium as gym
import numpy as np
from env import BAMBOO, PAD, RedPandaRunEnv
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv
from train import GAMMA, MODELS_DIR, make_model

from src.gamestate import UNFINISHED_LEVELS

TIME_PENALTY = 0.001  # a full 450 step timeout costs 0.45, so it's still better than dying


@dataclass
class Transition:
    """What a reward function gets to see about one env step. Distances are in pixels, straight
    to the nearest bamboo, so they ignore walls: on a winding level, closer isn't always better."""

    base: float  # the env's own reward: 1 for a win, -1 for a death, otherwise 0
    terminated: bool
    distance: float
    previous: float  # distance before this step
    closest: float  # smallest distance so far in the episode, before this step
    start: float  # distance at the start of the level


def sparse(t):
    return t.base


def time_penalty(t):
    return t.base - TIME_PENALTY


def potential(t):
    # Potential-based shaping, which doesn't change which policy is best. Sums to about +1 for
    # walking from the start to the bamboo, and walking back takes it all away again.
    after = 0 if t.terminated else -t.distance / t.start
    return t.base + GAMMA * after + t.previous / t.start


def progress(t):
    # only pays for getting closer than ever before, so pacing back and forth earns nothing
    return t.base + max(t.closest - t.distance, 0) / t.start


def progress_time(t):
    return progress(t) - TIME_PENALTY


REWARDS = {f.__name__: f for f in (sparse, time_penalty, potential, progress, progress_time)}


class RewardWrapper(gym.Wrapper):
    """Replaces the env's reward with reward_fn(Transition). make_vec_env puts this outside its
    Monitor, so PPO trains on the new reward while ep_rew_mean keeps reporting the env's own."""

    def __init__(self, env, reward_fn):
        super().__init__(env)
        self.reward_fn = reward_fn

    def _distance(self):
        center = np.array(self.unwrapped.game.scene.player.rect().center)
        return np.linalg.norm(self.bamboo - center, axis=1).min()

    def reset(self, **kwargs):
        result = self.env.reset(**kwargs)
        # (y, x) in the padded grid to (x, y) pixels at the middle of each tile
        tiles = np.argwhere(self.unwrapped.grid == BAMBOO) - PAD
        self.bamboo = tiles[:, ::-1] * 16 + 8
        self.start = self.distance = self.closest = self._distance()
        return result

    def step(self, action):
        obs, base, terminated, truncated, info = self.env.step(action)
        previous, self.distance = self.distance, self._distance()
        reward = self.reward_fn(
            Transition(base, terminated, self.distance, previous, self.closest, self.start)
        )
        self.closest = min(self.closest, self.distance)
        return obs, float(reward), terminated, truncated, info


class FirstWin(BaseCallback):
    """Remembers the step of the first win, which is most of what shaping is meant to speed up."""

    def __init__(self):
        super().__init__()
        self.step = None

    def _on_step(self):
        if self.step is None and any(i.get("is_success") for i in self.locals["infos"]):
            self.step = self.num_timesteps
        return True


def evaluate(model, env, episodes):
    """Plays the plain env, so the score doesn't depend on the reward. Actions are sampled: the
    level never changes, so always taking the likeliest action would replay one episode."""
    outcomes, win_ticks = [], []
    for _ in range(episodes):
        obs, _ = env.reset()
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=False)
            obs, _, terminated, truncated, _ = env.step(action)
            done = terminated or truncated
        outcomes.append(env.game.scene.result or "timeout")
        if outcomes[-1] == "win":
            win_ticks.append(env.ticks)
    return {
        "win": outcomes.count("win") / episodes,
        "lose": outcomes.count("lose") / episodes,
        "timeout": outcomes.count("timeout") / episodes,
        "ticks": np.mean(win_ticks) if win_ticks else None,
    }


def train(reward, level, steps, envs, seed):
    name = f"reward_level{level}_{reward}_seed{seed}_{time.strftime('%m%d-%H%M%S')}"
    env = make_vec_env(
        RedPandaRunEnv,
        n_envs=envs,
        seed=seed,
        env_kwargs={"level": level},
        vec_env_cls=SubprocVecEnv,
        wrapper_class=RewardWrapper,
        wrapper_kwargs={"reward_fn": REWARDS[reward]},
    )
    model = make_model(env, seed)
    model.verbose = 0
    first_win = FirstWin()
    try:
        model.learn(total_timesteps=steps, callback=first_win, tb_log_name=name)
    finally:
        env.close()
    model.save(MODELS_DIR / f"{name}.zip")
    return model, first_win.step


def mean_text(values, spec):
    values = [v for v in values if v is not None]
    return format(np.mean(values), spec) if values else "-"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=int, default=1, help="level number")
    parser.add_argument("--steps", type=int, default=300_000, help="env steps to train each agent")
    parser.add_argument("--envs", type=int, default=8, help="copies of the level run in parallel")
    parser.add_argument("--seeds", type=int, default=3, help="agents to train per reward function")
    parser.add_argument("--episodes", type=int, default=50, help="evaluation episodes per agent")
    parser.add_argument("--rewards", nargs="+", choices=REWARDS, default=list(REWARDS))
    args = parser.parse_args()
    if args.level in UNFINISHED_LEVELS:
        parser.error(f"level {args.level} has no bamboo to reach")

    eval_env = RedPandaRunEnv(level=args.level)
    results = {reward: [] for reward in args.rewards}
    for reward in args.rewards:
        for seed in range(args.seeds):
            start = time.perf_counter()
            model, first_win = train(reward, args.level, args.steps, args.envs, seed)
            score = evaluate(model, eval_env, args.episodes)
            results[reward].append({**score, "first_win": first_win})
            print(
                f"{reward} seed {seed}: {score['win']:.0%} wins, first win at step {first_win} "
                f"({time.perf_counter() - start:.0f}s)",
                flush=True,
            )

    print(f"\nlevel {args.level}, {args.steps:,} steps, {args.seeds} seeds, averaged per seed")
    print(
        f"{'reward':<14} {'win':>6} {'best':>6} {'worst':>6} {'lose':>6} {'timeout':>8} "
        f"{'first win':>10} {'win ticks':>10}"
    )
    # ranked by win rate, with the best and worst seed because one lucky seed proves little
    ranked = sorted(results.items(), key=lambda r: -np.mean([s["win"] for s in r[1]]))
    for reward, scores in ranked:
        wins = [s["win"] for s in scores]
        print(
            f"{reward:<14} {np.mean(wins):>6.0%} {max(wins):>6.0%} {min(wins):>6.0%} "
            f"{np.mean([s['lose'] for s in scores]):>6.0%} "
            f"{np.mean([s['timeout'] for s in scores]):>8.0%} "
            f"{mean_text([s['first_win'] for s in scores], ',.0f'):>10} "
            f"{mean_text([s['ticks'] for s in scores], '.0f'):>10}"
        )


# SubprocVecEnv starts new processes that import this file, so training must only start here
if __name__ == "__main__":
    main()
