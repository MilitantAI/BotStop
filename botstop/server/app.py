from __future__ import annotations

import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from botstop.service import ChallengeService, PublicChallenge
from botstop.settings import Settings
from botstop.store import ChallengeStore


class CreateChallengeResponse(BaseModel):
    challenge_id: str
    gif_url: str
    digit_length: int
    expires_in: int


class RefreshChallengeRequest(BaseModel):
    previous_id: str | None = None


class VerifyChallengeRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=32)


class VerifyChallengeResponse(BaseModel):
    ok: bool
    reason: str


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is None:
        return "unknown"
    return request.client.host


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    store = ChallengeStore(ttl_seconds=settings.ttl_seconds)
    service = ChallengeService(
        store=store,
        storage_dir=settings.storage_dir,
        secret=settings.secret,
        ttl_seconds=settings.ttl_seconds,
    )

    rate_buckets: dict[str, deque[float]] = defaultdict(deque)
    rate_lock = __import__("threading").Lock()

    def rate_limit(request: Request) -> None:
        if settings.rate_limit_per_minute <= 0:
            return
        ip = _client_ip(request)
        now = time.time()
        with rate_lock:
            bucket = rate_buckets[ip]
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= settings.rate_limit_per_minute:
                raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="rate_limit")
            bucket.append(now)

    def require_api_key(request: Request) -> None:
        if settings.api_key is None:
            return
        provided = request.headers.get("x-api-key")
        if provided != settings.api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    def protected(request: Request) -> None:
        rate_limit(request)
        require_api_key(request)

    app = FastAPI(
        title="BotStop API",
        version="0.3.0",
        description="Language-agnostic HTTP API for BotStop captcha challenges.",
    )

    allow_origins = settings.cors_origins or ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/challenges", response_model=CreateChallengeResponse, dependencies=[Depends(protected)])
    def create_challenge() -> CreateChallengeResponse:
        challenge = service.create()
        return CreateChallengeResponse(
            challenge_id=challenge.challenge_id,
            gif_url=challenge.gif_url,
            digit_length=challenge.digit_length,
            expires_in=challenge.expires_in,
        )

    @app.post(
        "/v1/challenges/refresh",
        response_model=CreateChallengeResponse,
        dependencies=[Depends(protected)],
    )
    def refresh_challenge(body: RefreshChallengeRequest) -> CreateChallengeResponse:
        challenge = service.refresh(body.previous_id)
        return CreateChallengeResponse(
            challenge_id=challenge.challenge_id,
            gif_url=challenge.gif_url,
            digit_length=challenge.digit_length,
            expires_in=challenge.expires_in,
        )

    @app.get("/v1/challenges/{challenge_id}/animation.gif", dependencies=[Depends(protected)])
    def challenge_animation(challenge_id: str) -> FileResponse:
        path = service.gif_path(challenge_id)
        if path is None or not path.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
        return FileResponse(path, media_type="image/gif", filename=f"{challenge_id}.gif")

    @app.post(
        "/v1/challenges/{challenge_id}/verify",
        response_model=VerifyChallengeResponse,
        dependencies=[Depends(protected)],
    )
    def verify_challenge(challenge_id: str, body: VerifyChallengeRequest) -> VerifyChallengeResponse:
        result = service.verify(challenge_id, body.answer)
        if result.reason == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
        return VerifyChallengeResponse(ok=result.ok, reason=result.reason)

    app.state.settings = settings
    app.state.service = service
    return app
