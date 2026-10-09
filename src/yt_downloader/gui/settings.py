"""Persistent user preferences, stored with QSettings (~/.config/yt-downloader/)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings

from yt_downloader import APP_SLUG
from yt_downloader.core import DownloadOptions
from yt_downloader.core.options import CONTAINERS, COOKIE_BROWSERS, DEFAULT_TEMPLATE
from yt_downloader.core.presets import DEFAULT_PRESET, PRESETS
from yt_downloader.core.utils import LEGACY_DOWNLOAD_FOLDER, default_download_dir

MAX_CONCURRENT_LIMIT = 5


class AppSettings:
    def __init__(self, qsettings: QSettings | None = None) -> None:
        self._s = qsettings or QSettings(APP_SLUG, APP_SLUG)

    def _get(self, key: str, default, type_):
        return self._s.value(key, default, type=type_)

    # Download defaults -------------------------------------------------------------------

    @property
    def output_dir(self) -> Path:
        default = default_download_dir()
        path = Path(self._get("download/output_dir", str(default), str))
        # Users still on the old default folder move to the new one; custom folders are kept.
        if path == default.parent / LEGACY_DOWNLOAD_FOLDER:
            self.output_dir = default
            return default
        return path

    @output_dir.setter
    def output_dir(self, value: Path) -> None:
        self._s.setValue("download/output_dir", str(value))

    @property
    def preset(self) -> str:
        value = self._get("download/preset", DEFAULT_PRESET, str)
        return value if value in {p.key for p in PRESETS} else DEFAULT_PRESET

    @preset.setter
    def preset(self, value: str) -> None:
        self._s.setValue("download/preset", value)

    @property
    def container(self) -> str:
        value = self._get("download/container", "auto", str)
        return value if value in CONTAINERS else "auto"

    @container.setter
    def container(self, value: str) -> None:
        self._s.setValue("download/container", value)

    @property
    def playlist(self) -> bool:
        return self._get("download/playlist", False, bool)

    @playlist.setter
    def playlist(self, value: bool) -> None:
        self._s.setValue("download/playlist", value)

    @property
    def filename_template(self) -> str:
        return self._get("download/filename_template", DEFAULT_TEMPLATE, str) or DEFAULT_TEMPLATE

    @filename_template.setter
    def filename_template(self, value: str) -> None:
        self._s.setValue("download/filename_template", value)

    @property
    def embed_metadata(self) -> bool:
        return self._get("download/embed_metadata", True, bool)

    @embed_metadata.setter
    def embed_metadata(self, value: bool) -> None:
        self._s.setValue("download/embed_metadata", value)

    @property
    def embed_thumbnail(self) -> bool:
        return self._get("download/embed_thumbnail", True, bool)

    @embed_thumbnail.setter
    def embed_thumbnail(self, value: bool) -> None:
        self._s.setValue("download/embed_thumbnail", value)

    @property
    def embed_subtitles(self) -> bool:
        return self._get("download/embed_subtitles", False, bool)

    @embed_subtitles.setter
    def embed_subtitles(self, value: bool) -> None:
        self._s.setValue("download/embed_subtitles", value)

    @property
    def subtitle_langs(self) -> str:
        return self._get("download/subtitle_langs", "en", str)

    @subtitle_langs.setter
    def subtitle_langs(self, value: str) -> None:
        self._s.setValue("download/subtitle_langs", value)

    @property
    def cookies_from_browser(self) -> str:
        value = self._get("download/cookies_from_browser", "", str)
        return value if value in COOKIE_BROWSERS else ""

    @cookies_from_browser.setter
    def cookies_from_browser(self, value: str) -> None:
        self._s.setValue("download/cookies_from_browser", value)

    # Application ---------------------------------------------------------------------------

    @property
    def max_concurrent(self) -> int:
        value = self._get("app/max_concurrent", 2, int)
        return max(1, min(MAX_CONCURRENT_LIMIT, value))

    @max_concurrent.setter
    def max_concurrent(self, value: int) -> None:
        self._s.setValue("app/max_concurrent", value)

    @property
    def window_geometry(self) -> QByteArray | None:
        value = self._s.value("app/window_geometry")
        return value if isinstance(value, QByteArray) else None

    @window_geometry.setter
    def window_geometry(self, value: QByteArray) -> None:
        self._s.setValue("app/window_geometry", value)

    def reset_download_defaults(self) -> None:
        self._s.remove("download")

    def sync(self) -> None:
        self._s.sync()

    def download_options(self) -> DownloadOptions:
        langs = tuple(x.strip() for x in self.subtitle_langs.split(",") if x.strip()) or ("en",)
        return DownloadOptions(
            output_dir=self.output_dir,
            preset=self.preset,
            container=self.container,
            filename_template=self.filename_template,
            playlist=self.playlist,
            embed_metadata=self.embed_metadata,
            embed_thumbnail=self.embed_thumbnail,
            embed_subtitles=self.embed_subtitles,
            subtitle_langs=langs,
            cookies_from_browser=self.cookies_from_browser or None,
        )
