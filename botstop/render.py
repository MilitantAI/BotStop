from __future__ import annotations

import base64
from pathlib import Path

import imageio.v3 as iio
import numpy as np
from PIL import Image

from botstop.challenge import Challenge, render_frames


def frames_to_pil(frames: list[np.ndarray]) -> list[Image.Image]:
    return [Image.fromarray(frame, mode="L") for frame in frames]


def render_gif(
    challenge: Challenge,
    output_path: Path,
    *,
    fps: float = 12.0,
    loop: int = 0,
) -> Path:
    """Write an animated GIF for a challenge."""
    frames = render_frames(challenge)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    duration_ms = int(round(1000.0 / fps))
    iio.imwrite(
        output_path,
        np.stack(frames, axis=0),
        extension=".gif",
        duration=duration_ms,
        loop=0,  # 0 = repeat forever
    )
    return output_path


def render_preview_html(
    challenge: Challenge,
    output_path: Path,
    *,
    fps: float = 12.0,
    gif_path: Path | None = None,
    demo: bool = True,
) -> Path:
    """Write a standalone HTML preview page."""
    if gif_path is None:
        gif_path = output_path.with_suffix(".gif")
        if not gif_path.exists():
            render_gif(challenge, gif_path, fps=fps)

    gif_bytes = gif_path.read_bytes()
    encoded = base64.b64encode(gif_bytes).decode("ascii")

    demo_footer = ""
    demo_controls = ""
    if demo:
        demo_controls = f"""
      <button type="button" id="check">Check answer</button>
      <div id="result"></div>
      <p class="hint">Local demo only — the answer is embedded here for preview, not for production.</p>"""
        demo_footer = f"""
  <script>
    const expected = {challenge.answer!r};
    const button = document.getElementById("check");
    const input = document.getElementById("answer");
    const result = document.getElementById("result");
    button.addEventListener("click", () => {{
      const value = input.value.trim().replace(/\\s+/g, "");
      if (!value) {{
        result.textContent = "Enter what you read.";
        result.style.color = "#f5c542";
        return;
      }}
      if (value === expected) {{
        result.textContent = "Correct.";
        result.style.color = "#6dffb0";
      }} else {{
        result.textContent = "Not quite. Keep watching the motion.";
        result.style.color = "#ff7b7b";
      }}
    }});
    input.addEventListener("keydown", (event) => {{
      if (event.key === "Enter") button.click();
    }});
  </script>"""
    else:
        demo_controls = """
      <p class="hint">Submit this challenge ID and your answer to the server for verification.</p>"""

    html = f"""<!DOCTYPE html>
<html lang="en-AU">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BotStop preview</title>
  <style>
    :root {{
      color-scheme: dark;
      font-family: "Segoe UI", system-ui, sans-serif;
      background: #111;
      color: #eee;
    }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px;
    }}
    main {{
      width: min(640px, 100%);
      display: grid;
      gap: 16px;
    }}
    h1 {{
      font-size: 1.25rem;
      font-weight: 600;
      margin: 0;
    }}
    p {{
      margin: 0;
      line-height: 1.5;
      color: #bbb;
    }}
    .panel {{
      background: #1b1b1b;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 16px;
      display: grid;
      gap: 12px;
    }}
    img {{
      width: 100%;
      image-rendering: auto;
      border-radius: 8px;
      background: #000;
    }}
    label {{
      display: grid;
      gap: 6px;
      font-size: 0.9rem;
    }}
    input {{
      font: inherit;
      padding: 10px 12px;
      border-radius: 8px;
      border: 1px solid #444;
      background: #0d0d0d;
      color: #fff;
      letter-spacing: 0.2em;
      font-variant-numeric: tabular-nums;
    }}
    button {{
      font: inherit;
      padding: 10px 12px;
      border: 0;
      border-radius: 8px;
      background: #3d7eff;
      color: #fff;
      cursor: pointer;
    }}
    #result {{
      min-height: 1.25rem;
      font-size: 0.95rem;
    }}
    .hint {{
      font-size: 0.85rem;
      color: #888;
    }}
  </style>
</head>
<body>
  <main>
    <div>
      <h1>BotStop</h1>
      <p>Watch the static. The answer is the moving letters you perceive over time.</p>
    </div>
    <div class="panel">
      <img src="data:image/gif;base64,{encoded}" alt="BotStop captcha animation">
      <p class="hint">Challenge ID: {challenge.challenge_id}</p>
      <label>
        Your answer
        <input id="answer" autocomplete="off" spellcheck="false" inputmode="numeric" pattern="[0-9]*" maxlength="{challenge.config.text_length}">
      </label>{demo_controls}
    </div>
  </main>{demo_footer}
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
