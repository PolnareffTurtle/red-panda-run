"""Plays random actions in the env and summarises what happened. Run from the repo root:

    python rl/random_agent.py --level 1 --episodes 200

Use it as a sanity check after every env change, and to see whether a reward function ranks
outcomes the way you expect (wins above timeouts above deaths).
"""

import argparse
import math
import time
from collections import defaultdict

import numpy as np
from env import RedPandaRunEnv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=int, default=1, help="level number")
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument(
        "--hold",
        type=int,
        default=2,
        help="repeat each random action for this many steps (on top of the env's frame skip)",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    env = RedPandaRunEnv(level=args.level)
    env.action_space.seed(args.seed)

    returns = defaultdict(list)  # outcome -> episode returns
    lengths = defaultdict(list)
    step_rewards = []
    steps = 0
    start = time.perf_counter()

    for episode in range(args.episodes):
        env.reset(seed=args.seed + episode)
        total, length, done = 0.0, 0, False
        while not done:
            if length % args.hold == 0:
                action = env.action_space.sample()
            _, reward, terminated, truncated, _ = env.step(action)
            if not math.isfinite(reward):
                raise ValueError(f"reward {reward} at episode {episode}, step {length}")
            total += reward
            length += 1
            step_rewards.append(reward)
            done = terminated or truncated
        outcome = env.game.scene.result or "timeout"
        returns[outcome].append(total)
        lengths[outcome].append(length)
        steps += length

    elapsed = time.perf_counter() - start
    print(f"level {args.level}, {args.episodes} episodes, {steps / elapsed:,.0f} steps/s\n")
    print(f"{'outcome':<8} {'count':>6} {'length':>8} {'return mean':>12} {'min':>9} {'max':>9}")
    for outcome in ("win", "lose", "timeout"):
        if outcome not in returns:
            print(f"{outcome:<8} {0:>6}")
            continue
        r = np.array(returns[outcome])
        length = np.mean(lengths[outcome])
        print(
            f"{outcome:<8} {len(r):>6} {length:>8.0f} {r.mean():>12.3f} {r.min():>9.3f} {r.max():>9.3f}"
        )

    rewards = np.array(step_rewards)
    print(
        f"\nper-step reward: min {rewards.min():.4f}, max {rewards.max():.4f}, "
        f"nonzero on {np.count_nonzero(rewards) / len(rewards):.1%} of steps"
    )

    # Warnings for reward functions that rank outcomes the wrong way. Random episodes are noisy,
    # so these compare the best of the worse outcome against the worst of the better one.
    def best(outcome):
        return max(returns[outcome]) if outcome in returns else None

    def worst(outcome):
        return min(returns[outcome]) if outcome in returns else None

    for better, worse in (("win", "lose"), ("win", "timeout"), ("timeout", "lose")):
        if best(worse) is not None and worst(better) is not None and best(worse) > worst(better):
            print(
                f"warning: a '{worse}' episode returned {best(worse):.3f}, "
                f"more than a '{better}' episode ({worst(better):.3f})"
            )


if __name__ == "__main__":
    main()
