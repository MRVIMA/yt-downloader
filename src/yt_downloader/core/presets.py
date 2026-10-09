"""Quality presets shown to the user."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    key: str
    label: str
    max_height: int | None = None
    audio_codec: str | None = None

    @property
    def is_audio(self) -> bool:
        return self.audio_codec is not None


PRESETS: tuple[Preset, ...] = (
    Preset("best", "Video — Best available"),
    Preset("2160", "Video — 4K (2160p)", max_height=2160),
    Preset("1440", "Video — 1440p", max_height=1440),
    Preset("1080", "Video — 1080p", max_height=1080),
    Preset("720", "Video — 720p", max_height=720),
    Preset("480", "Video — 480p", max_height=480),
    Preset("360", "Video — 360p", max_height=360),
    Preset("mp3", "Audio — MP3", audio_codec="mp3"),
    Preset("m4a", "Audio — M4A (AAC)", audio_codec="m4a"),
    Preset("opus", "Audio — Opus", audio_codec="opus"),
)

_BY_KEY = {p.key: p for p in PRESETS}

DEFAULT_PRESET = "best"


def get_preset(key: str) -> Preset:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise ValueError(f"Unknown preset {key!r}. Choose from: {', '.join(_BY_KEY)}") from None
