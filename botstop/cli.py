from __future__ import annotations

import argparse
from pathlib import Path

from botstop.api import create_captcha, default_secret, verify_captcha
from botstop.challenge import ChallengeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="botstop",
        description="Generate anti-AI static-motion captcha challenges.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="Create a new captcha challenge.")
    generate.add_argument(
        "--text",
        help="Fixed answer for testing only. Omit for a random answer (default).",
    )
    generate.add_argument("--output-dir", type=Path, default=Path("outputs"))
    generate.add_argument("--width", type=int, default=480)
    generate.add_argument("--height", type=int, default=280)
    generate.add_argument("--font-size", type=int, default=192)
    generate.add_argument(
        "--stroke-width",
        type=int,
        default=4,
        help="Outline thickness for glyph strokes.",
    )
    generate.add_argument("--frames", type=int, default=120)
    generate.add_argument("--fps", type=float, default=12.0)
    generate.add_argument(
        "--motion",
        choices=["bounce", "orbit"],
        default="bounce",
        help="How the text patch moves across the static field.",
    )
    generate.add_argument(
        "--grain",
        type=int,
        default=1,
        help="Static speck size in pixels (coarse grid cell width).",
    )
    generate.add_argument(
        "--no-bundle",
        action="store_true",
        help="Skip writing the server-side verification bundle.",
    )
    generate.add_argument(
        "--no-demo-html",
        action="store_true",
        help="Omit the local answer check from the HTML preview (production use).",
    )
    generate.add_argument(
        "--reveal-answer",
        action="store_true",
        help="Print the answer to stdout (testing only; never use in production).",
    )

    verify = subparsers.add_parser("verify", help="Verify a submission against a bundle file.")
    verify.add_argument("--bundle", type=Path, required=True)
    verify.add_argument("--answer", required=True)
    verify.add_argument("--ttl-seconds", type=int, default=300)

    serve = subparsers.add_parser("serve", help="Run the production HTTP API.")
    serve.add_argument("--host", help="Bind host (overrides BOTSTOP_HOST).")
    serve.add_argument("--port", type=int, help="Bind port (overrides BOTSTOP_PORT).")
    serve.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "generate":
        config = ChallengeConfig(
            width=args.width,
            height=args.height,
            font_size=args.font_size,
            stroke_width=max(0, args.stroke_width),
            frame_count=args.frames,
            motion=args.motion,
            grain=max(1, args.grain),
            text_length=len(args.text) if args.text else ChallengeConfig.text_length,
        )
        secret = default_secret()
        result = create_captcha(
            answer=args.text,
            config=config,
            output_dir=args.output_dir,
            secret=secret,
            fps=args.fps,
            write_bundle=not args.no_bundle,
            demo_html=not args.no_demo_html,
        )

        if result.bundle_path:
            print(result.bundle_path)

        print(result.metadata_path)
        if args.reveal_answer:
            print(result.challenge.answer)
        return 0

    if args.command == "verify":
        result = verify_captcha(
            bundle_path=args.bundle,
            submitted_answer=args.answer,
            secret=default_secret(),
            ttl_seconds=args.ttl_seconds,
        )
        print(result.reason)
        return 0 if result.ok else 1

    if args.command == "serve":
        from botstop.serve import main as serve_main

        serve_argv: list[str] = []
        if args.host:
            serve_argv.extend(["--host", args.host])
        if args.port:
            serve_argv.extend(["--port", str(args.port)])
        if args.reload:
            serve_argv.append("--reload")
        return serve_main(serve_argv)

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
