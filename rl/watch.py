"""Opens the game window and plays a level with a trained model, or randomly. Run from the repo root:

    python rl/watch.py --level 0                              # random actions
    python rl/watch.py --level 0 --model level1_1027-153000   # a model from rl/models/

--model takes a run name from rl/models/, or a path to a .zip relative to the repo root.
Close the window or press Ctrl+C to stop.
"""

import argparse
from pathlib import Path

from env import RedPandaRunEnv
from stable_baselines3 import PPO

RL_DIR = Path(__file__).resolve().parent


def find_model(name):
    # env.py changes the working directory to game/, so resolve against known folders instead
    for path in (RL_DIR / "models" / f"{name}.zip", RL_DIR.parent / name, Path(name)):
        if path.is_file():
            return path
    raise SystemExit(f"no model '{name}' in {RL_DIR / 'models'} or the repo root")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", type=int, default=0, help="level index (0 is level 1)")
    parser.add_argument("--model", help="trained model to watch; random actions if left out")
    parser.add_argument(
        "--stochastic",
        action="store_true",
        help="sample actions like during training, instead of always taking the most likely one",
    )
    parser.add_argument(
        "--hold", type=int, default=2, help="random play only: repeat each action this many steps"
    )
    args = parser.parse_args()

    model = PPO.load(find_model(args.model), device="cpu") if args.model else None
    env = RedPandaRunEnv(level=args.level, render_mode="human")

    episode = 0
    try:
        while True:
            obs, _ = env.reset()
            total, length, done = 0.0, 0, False
            while not done:
                if model:
                    action, _ = model.predict(obs, deterministic=not args.stochastic)
                elif length % args.hold == 0:
                    action = env.action_space.sample()
                obs, reward, terminated, truncated, _ = env.step(action)
                total += reward
                length += 1
                done = terminated or truncated
            episode += 1
            outcome = env.game.scene.result or "timeout"
            print(f"episode {episode}: {outcome} after {length} steps, return {total:.3f}")
    except KeyboardInterrupt:
        env.close()


if __name__ == "__main__":
    main()
