from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _split_origins(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


@dataclass(frozen=True)
class Settings:
    secret: str
    storage_dir: Path
    ttl_seconds: int
    host: str
    port: int
    cors_origins: list[str]
    rate_limit_per_minute: int
    api_key: str | None

    @classmethod
    def from_env(cls) -> Settings:
        storage = Path(os.environ.get("BOTSTOP_STORAGE_DIR", ".botstop-data"))
        api_key = os.environ.get("BOTSTOP_API_KEY")
        return cls(
            secret=os.environ.get("BOTSTOP_SECRET", "local-dev-secret"),
            storage_dir=storage,
            ttl_seconds=int(os.environ.get("BOTSTOP_TTL_SECONDS", "300")),
            host=os.environ.get("BOTSTOP_HOST", "127.0.0.1"),
            port=int(os.environ.get("BOTSTOP_PORT", "8787")),
            cors_origins=_split_origins(os.environ.get("BOTSTOP_CORS_ORIGINS", "*")),
            rate_limit_per_minute=int(os.environ.get("BOTSTOP_RATE_LIMIT", "60")),
            api_key=api_key if api_key else None,
        )
