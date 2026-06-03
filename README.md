# BotStop

**Stop bots, not humans.**

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

- **Python package** — generator, verifier, API server
- **`@botstop/client`** — npm/pnpm client and drop-in widget
- **Built-in** — refresh, TTL, rate limits, optional API key
- **Language-agnostic** — any stack that can POST JSON and display a GIF

## Install (Python)

```powershell
pip install botstop[api]

# development
pip install -e ".[api,dev]"
```

## Run the API

```powershell
# set secrets first (see .env.example)
botstop serve

# or bind publicly
botstop serve --host 0.0.0.0 --port 8787
```

OpenAPI docs: `http://127.0.0.1:8787/docs`

### Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `BOTSTOP_SECRET` | `local-dev-secret` | HMAC signing key (**change in production**) |
| `BOTSTOP_API_KEY` | _(empty)_ | Require `X-API-Key` header when set |
| `BOTSTOP_TTL_SECONDS` | `300` | Challenge expiry |
| `BOTSTOP_CORS_ORIGINS` | `*` | Comma-separated allowed origins |
| `BOTSTOP_RATE_LIMIT` | `60` | Requests per IP per minute |
| `BOTSTOP_STORAGE_DIR` | `.botstop-data` | GIF storage |

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

## JavaScript / TypeScript

Build the client package:

```bash
cd client
pnpm install
pnpm build
```

Use in your app:

```bash
pnpm add @botstop/client
```

```ts
import { BotStopClient, mountBotStopWidget } from "@botstop/client";

const client = new BotStopClient({
  baseUrl: "http://127.0.0.1:8787",
  apiKey: import.meta.env.VITE_BOTSTOP_API_KEY,
});

mountBotStopWidget(client, {
  target: document.getElementById("captcha")!,
  onVerified: (result) => {
    if (result.ok) submitForm();
  },
});
```

## CLI (local / dev)

```powershell
botstop generate --reveal-answer
botstop verify --bundle outputs\<id>.bundle.json --answer 482913
```

## Python library

Embed generation and verification in your own backend:

```python
from botstop import create_captcha, verify_captcha

result = create_captcha(demo_html=False)
check = verify_captcha(bundle_path=result.bundle_path, submitted_answer="482913")
```

## Production checklist

1. Set a strong `BOTSTOP_SECRET`
2. Set `BOTSTOP_API_KEY` and pass it from your frontend or backend proxy
3. Restrict `BOTSTOP_CORS_ORIGINS` to your domain
4. Run behind HTTPS (reverse proxy)
5. Use `demo_html=False` — never ship answers to the browser
6. Proxy API calls through your backend if the API key should not live in the client

## Build

```powershell
python -m pip install build
python -m build
```

Outputs: `dist/botstop-0.3.0-py3-none-any.whl`

## GitHub Pages demo

A static interactive demo lives in [`docs/`](docs/). It shows the single-frame vs in-motion comparison and lets visitors try the captcha in the browser (demo-only client-side verification). Test it yourself — take a screenshot.

Regenerate challenge assets after changing captcha settings:

```powershell
python scripts/build_github_demo.py --count 8
```

Preview locally:

```powershell
cd docs
python -m http.server 8080
# open http://127.0.0.1:8080
```

Publish on GitHub: **Settings → Pages → Build from branch → `main` → `/docs`**.

Update the footer links in `docs/index.html` once the repository URL is known.

## License

MIT — see [LICENSE](LICENSE).
