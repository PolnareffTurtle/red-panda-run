"""Trains a PPO agent on one level. Run from the repo root:

    python rl/train.py --level 1 --steps 1000000

Watch it learn with `tensorboard --logdir rl/runs` (http://localhost:6006). The finished model
is saved to rl/models/<run name>.zip, with checkpoints along the way in rl/models/<run name>/.
"""

import argparse
import time
from pathlib import Path

from env import RedPandaRunEnv
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import SubprocVecEnv

# env.py changes the working directory to game/, so build these from this file instead
RL_DIR = Path(__file__).resolve().parent
RUNS_DIR = RL_DIR / "runs"
MODELS_DIR = RL_DIR / "models"

GAMMA = 0.99  # discount: how much a reward one step later is worth


def make_model(env, seed):
    return PPO(
        "MlpPolicy",
        env,
        # SB3's defaults apart from ent_coef, written out so they're easy to find and change
        n_steps=2048,  # steps each env plays before every update
        batch_size=64,
        n_epochs=10,  # passes over the collected steps per update
        gamma=GAMMA,
        learning_rate=3e-4,
        # bonus for staying random. At 0 the first run settled on standing still (it's never
        # punished) before it had found the bamboo once
        ent_coef=0.01,
        tensorboard_log=str(RUNS_DIR),
        seed=seed,
        # small MLPs train faster on the CPU than on the GPU
        device="cpu",
        verbose=1,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=int, default=1, help="level number")
    parser.add_argument("--steps", type=int, default=1_000_000, help="total env steps to train")
    parser.add_argument("--envs", type=int, default=8, help="copies of the level run in parallel")
    parser.add_argument(
        "--name", help="run name for tensorboard and the saved model (default: level + time)"
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    name = args.name or f"level{args.level}_{time.strftime('%m%d-%H%M%S')}"

    # each env runs in its own process, so all CPU cores step the game at once
    env = make_vec_env(
        RedPandaRunEnv,
        n_envs=args.envs,
        seed=args.seed,
        env_kwargs={"level": args.level},
        vec_env_cls=SubprocVecEnv,
    )

    model = make_model(env, args.seed)

    checkpoints = CheckpointCallback(
        # save_freq counts calls per env, so divide to get one save per 100k total steps
        save_freq=max(100_000 // args.envs, 1),
        save_path=str(MODELS_DIR / name),
        name_prefix="ppo",
    )

    try:
        model.learn(total_timesteps=args.steps, callback=checkpoints, tb_log_name=name)
    except KeyboardInterrupt:
        print("\nstopped early, saving what it has learned so far")
    finally:
        path = MODELS_DIR / f"{name}.zip"
        model.save(path)
        env.close()
        print(f"saved {path}")


# SubprocVecEnv starts new processes that import this file, so training must only start here
if __name__ == "__main__":
    main()
