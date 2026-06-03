from __future__ import annotations

import argparse

from botstop.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="botstop serve", description="Run the BotStop HTTP API.")
    parser.add_argument("--host", help="Bind host (overrides BOTSTOP_HOST).")
    parser.add_argument("--port", type=int, help="Bind port (overrides BOTSTOP_PORT).")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        import uvicorn
    except ImportError as exc:
        raise SystemExit(
            "Missing API dependencies. Install with: pip install botstop[api]"
        ) from exc

    settings = Settings.from_env()
    host = args.host or settings.host
    port = args.port or settings.port

    uvicorn.run(
        "botstop.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=args.reload,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
