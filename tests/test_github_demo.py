from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_build_github_demo_writes_pool(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "build_github_demo.py"
    output = tmp_path / "challenges"

    subprocess.run(
        [sys.executable, str(script), "--count", "2", "--output", str(output)],
        check=True,
        cwd=root,
    )

    pool = json.loads((output / "pool.json").read_text(encoding="utf-8"))
    assert len(pool) == 2
    for entry in pool:
        assert (output / Path(entry["gif"]).name).is_file()
        assert (output / Path(entry["frame"]).name).is_file()
        assert entry["answer"].isdigit()
        assert len(entry["answer"]) == entry["digit_length"]
