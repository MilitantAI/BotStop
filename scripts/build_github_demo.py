#!/usr/bin/env python3
"""Generate static assets for the GitHub Pages demo in docs/.

Regenerate after changing captcha settings::

    python scripts/build_github_demo.py --count 8

Preview locally::

    cd docs && python -m http.server 8080

Publish: GitHub repo Settings → Pages → branch main, folder /docs.
Update footer links in docs/index.html when the repository URL is final.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from botstop.challenge import ChallengeConfig, generate_challenge, render_frames  # noqa: E402
from botstop.render import render_gif  # noqa: E402

from PIL import Image  # noqa: E402


def write_frame_png(challenge, output_path: Path) -> None:
    frame = render_frames(challenge)[0]
    Image.fromarray(frame, mode="L").save(output_path, format="PNG", optimize=True)


def build_pool(*, count: int, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config = ChallengeConfig()
    pool: list[dict] = []

    for index in range(count):
        challenge = generate_challenge(config=config, secret=f"github-demo-{index}")
        stem = f"c{index}"
        gif_path = output_dir / f"{stem}.gif"
        frame_path = output_dir / f"{stem}-f0.png"

        render_gif(challenge, gif_path)
        write_frame_png(challenge, frame_path)

        pool.append(
            {
                "id": challenge.challenge_id,
                "answer": challenge.answer,
                "digit_length": config.text_length,
                "gif": f"challenges/{stem}.gif",
                "frame": f"challenges/{stem}-f0.png",
            }
        )

    manifest_path = output_dir / "pool.json"
    manifest_path.write_text(json.dumps(pool, indent=2), encoding="utf-8")
    return pool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build GitHub Pages demo challenge pool.")
    parser.add_argument("--count", type=int, default=8, help="Number of challenges to pre-generate.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "challenges",
        help="Directory for GIF/PNG assets and pool.json.",
    )
    args = parser.parse_args(argv)

    pool = build_pool(count=max(1, args.count), output_dir=args.output)
    print(f"Wrote {len(pool)} challenges to {args.output}")
    print(f"Manifest: {args.output / 'pool.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
