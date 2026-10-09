import pytest

from yt_downloader.core.presets import PRESETS, get_preset
from yt_downloader.core.utils import clean_error, extract_urls, format_bytes, format_eta


def test_preset_keys_unique():
    keys = [p.key for p in PRESETS]
    assert len(keys) == len(set(keys))


def test_get_preset_unknown():
    with pytest.raises(ValueError, match="Unknown preset"):
        get_preset("8k")


def test_audio_presets_flagged():
    assert get_preset("mp3").is_audio
    assert not get_preset("1080").is_audio


def test_extract_urls_dedupes_and_strips_punctuation():
    text = "watch https://youtu.be/abc, and (https://example.com/v?id=1) https://youtu.be/abc"
    assert extract_urls(text) == ["https://youtu.be/abc", "https://example.com/v?id=1"]


def test_extract_urls_ignores_non_links():
    assert extract_urls("just some text ftp://x") == []


@pytest.mark.parametrize("raw, expected", [
    ("\x1b[0;31mERROR:\x1b[0m [youtube] dQw4w9WgXcQ: Video unavailable",
     "Video unavailable"),
    ("ERROR: Unsupported URL: https://x.y\nmore", "Unsupported URL: https://x.y"),
    ("", "Unknown error"),
])
def test_clean_error(raw, expected):
    assert clean_error(raw) == expected


def test_format_helpers():
    assert format_bytes(None) == "?"
    assert format_bytes(512) == "512 B"
    assert format_bytes(1536) == "1.5 KiB"
    assert format_bytes(5 * 1024**3) == "5.0 GiB"
    assert format_eta(None) == "--:--"
    assert format_eta(65) == "01:05"
    assert format_eta(3725) == "1:02:05"


def test_state_dir_windows(monkeypatch, tmp_path):
    from yt_downloader.core import utils

    monkeypatch.setattr(utils.sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    assert utils.state_dir() == tmp_path / "YT Downloader" / "logs"


def test_use_bundled_tools_prepends_bin(monkeypatch, tmp_path):
    from yt_downloader.core import utils

    (tmp_path / "bin").mkdir()
    monkeypatch.setattr(utils.sys, "frozen", True, raising=False)
    monkeypatch.setattr(utils.sys, "executable", str(tmp_path / "yt-downloader.exe"))
    monkeypatch.setenv("PATH", "/usr/bin")
    utils.use_bundled_tools()
    assert utils.os.environ["PATH"].split(utils.os.pathsep)[0] == str(tmp_path / "bin")
