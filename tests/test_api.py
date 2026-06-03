from __future__ import annotations

from pathlib import Path

from botstop import ChallengeConfig, create_captcha, verify_captcha


def test_create_captcha_writes_artifacts(tmp_path: Path):
    result = create_captcha(
        answer="TEST",
        config=ChallengeConfig(frame_count=24),
        output_dir=tmp_path,
        write_bundle=True,
        secret="test-secret",
    )

    assert result.challenge.answer == "TEST"
    assert result.gif_path.is_file()
    assert result.html_path.is_file()
    assert result.metadata_path.is_file()
    assert result.bundle_path is not None
    assert result.bundle_path.is_file()


def test_verify_captcha_round_trip(tmp_path: Path):
    result = create_captcha(
        answer="482913",
        output_dir=tmp_path,
        write_bundle=True,
        secret="test-secret",
    )
    assert result.bundle_path is not None

    ok = verify_captcha(
        bundle_path=result.bundle_path,
        submitted_answer="482 913",
        secret="test-secret",
    )
    assert ok.ok
