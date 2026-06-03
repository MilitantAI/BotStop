# BotStop

**Stop bots, not humans.**

**[Live demo](https://militantai.github.io/BotStop/)** — try the captcha in your browser.

**Install:** [`pip install botstop`](https://pypi.org/project/botstop/) · [`npm install botstop`](https://www.npmjs.com/package/botstop)

BotStop is an anti-AI captcha where the answer lives in *motion*, not in pixels. The digits are cut from the same TV static as the background and bounced across the field. Pause on any frame and there is nothing to read — freeze time, and all discernment is lost to noise. Humans track the moving patch instinctively; bots need a persistent model that understands video, not a screenshot and an OCR pipeline.

## Why BotStop

Most captchas make the **image** harder: warp text, add clutter, distort glyphs. Bots respond with better OCR. BotStop sidesteps that arms race by changing the modality entirely.

| Typical captcha | BotStop |
|-----------------|---------|
| Hides text under noise | Text *is* the noise — same field, cut and moved |
| Escalates distortion to beat OCR | No stable glyph edges to latch onto |
| Solvable from a single frame with enough ML | A single frame gives almost nothing |
| More complexity on a static image | Watch the sequence; can't screenshot it |

When the challenge becomes a static image instead of a process, the signal disappears. That is the design.

## How it works

1. **Generate** a full canvas of point static — a fresh random field for every challenge.
2. **Cut** the answer from that same field. Not overlaid, not filtered: the same pixels.
3. **Move** the cutout across the base static (DVD-style bounce).
4. **Verify** that the user watched and typed what they saw.

Each challenge gets a new static field, answer, and motion path. Nothing carries over between instances, so there is no shared background for reinforcement learning to memorise. Within a single challenge, the base static stays fixed; the security property is temporal integration over time, not pattern matching across sessions.

## Security model

BotStop does not aim for perfect security — that would break legitimate use. It aims for **asymmetry**: make cheap automation economically pointless.

**Strong against**

- Frame scraping and one-shot OCR
- Batch classifiers that treat the web as a pile of PNGs
- Brute force on a repeated static background
- High-volume bots that need low cost per solve

**Does not claim to stop**

- Human solving farms
- Screen recording plus bespoke temporal ML
- Determined adversaries with custom video models

That trade-off is intentional. A captcha cannot stop everything without stopping everyone. The goal is efficiency: block automation at scale, accept that individual motivated solves may still occur, and use TTL, rate limits, server-side verification, and optional API keys to keep residual risk small.

For accessibility, offer an alternative verification path where motion-based challenges are not suitable.

---

## Architecture

```text
Browser / any app          BotStop API (Python)         Storage
     |                              |                            |
     |  POST /v1/challenges         |  create GIF + record       |
     |----------------------------->|---------------------------->|
     |  GET  .../animation.gif      |                            |
     |<-----------------------------|                            |
     |  POST .../verify             |  HMAC + TTL check          |
     |----------------------------->|                            |
```

- **Python** ([PyPI](https://pypi.org/project/botstop/)) — generator, verifier, API server
- **JavaScript** ([npm](https://www.npmjs.com/package/botstop)) — client and drop-in widget
- **Built-in** — refresh, TTL, rate limits, optional API key
- **Language-agnostic** — any stack that can POST JSON and display a GIF

## Deploy

### 1. Run the API (server)

```powershell
pip install botstop[api]
```

Copy `.env.example` to `.env` and set at minimum:

| Variable | Production |
|----------|------------|
| `BOTSTOP_SECRET` | Long random string (required) |
| `BOTSTOP_API_KEY` | Set if the API should require `X-API-Key` |
| `BOTSTOP_CORS_ORIGINS` | Your site origin(s), e.g. `https://yourdomain.com` |
| `BOTSTOP_HOST` | `0.0.0.0` when binding for a reverse proxy |
| `BOTSTOP_PORT` | `8787` (or your choice) |

```powershell
botstop serve --host 0.0.0.0 --port 8787
```

Put **nginx**, **Caddy**, or similar in front with HTTPS. Do not expose the API on plain HTTP in production.

OpenAPI docs (local): `http://127.0.0.1:8787/docs`

### 2. Add the captcha (frontend)

```bash
npm install botstop
```

```ts
import { BotStopClient, mountBotStopWidget } from "botstop";

const client = new BotStopClient({
  baseUrl: "https://api.yourdomain.com",  // your BotStop API URL
  apiKey: import.meta.env.VITE_BOTSTOP_API_KEY,  // omit if not using API keys
});

mountBotStopWidget(client, {
  target: document.getElementById("captcha")!,
  onVerified: (result) => {
    if (result.ok) submitForm();
  },
});
```

If the API key must stay secret, proxy `/v1/*` through your backend instead of calling the BotStop API directly from the browser.

### HTTP API

```http
POST /v1/challenges
→ { "challenge_id", "gif_url", "digit_length", "expires_in" }

GET /v1/challenges/{id}/animation.gif
→ image/gif

POST /v1/challenges/refresh
{ "previous_id": "optional-old-id" }
→ new challenge payload

POST /v1/challenges/{id}/verify
{ "answer": "482913" }
→ { "ok": true, "reason": "ok" }
```

### Environment (reference)

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOTSTOP_SECRET` | `local-dev-secret` | HMAC signing key |
| `BOTSTOP_API_KEY` | _(empty)_ | Require `X-API-Key` when set |
| `BOTSTOP_HOST` | `127.0.0.1` | Bind address |
| `BOTSTOP_PORT` | `8787` | Bind port |
| `BOTSTOP_TTL_SECONDS` | `300` | Challenge expiry |
| `BOTSTOP_CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `BOTSTOP_RATE_LIMIT` | `60` | Requests per IP per minute |
| `BOTSTOP_STORAGE_DIR` | `.botstop-data` | GIF storage |

## Production checklist

1. Strong `BOTSTOP_SECRET`
2. `BOTSTOP_CORS_ORIGINS` locked to your domain
3. HTTPS via reverse proxy
4. `BOTSTOP_API_KEY` set — proxy API calls if the key must not ship to the browser
5. Never use `demo_html=True` or expose answers client-side

## Development

```powershell
pip install -e ".[api,dev]"
botstop serve
```

```powershell
botstop generate --reveal-answer
botstop verify --bundle outputs\<id>.bundle.json --answer 482913
```

## Python library (embedded backend)

Embed generation and verification in your own backend:

```python
from botstop import create_captcha, verify_captcha

result = create_captcha(demo_html=False)
check = verify_captcha(bundle_path=result.bundle_path, submitted_answer="482913")
```

## License

MIT — see [LICENSE](LICENSE).
