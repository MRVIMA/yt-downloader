"""Runs a single download job on top of yt-dlp, reporting progress through callbacks.

The engine is UI-agnostic: the CLI prints the callbacks, the GUI turns them into Qt signals.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadCancelled, DownloadError, ExtractorError

from yt_downloader.core.options import DownloadOptions, build_ydl_opts
from yt_downloader.core.utils import clean_error, has_ffmpeg

log = logging.getLogger(__name__)

PROGRESS_INTERVAL = 0.2  # seconds between "downloading" updates


NO_FFMPEG_MESSAGE = (
    "This video needs ffmpeg: the site only offers video and audio as separate streams. "
    "Install ffmpeg, or choose an Audio format."
)


class JobCancelled(Exception):
    """The user cancelled the job."""


class DownloadFailed(Exception):
    """yt-dlp could not complete the download."""


@dataclass(frozen=True)
class MediaInfo:
    title: str
    uploader: str | None = None
    duration: float | None = None
    thumbnail: str | None = None
    webpage_url: str | None = None
    is_playlist: bool = False
    entry_count: int | None = None

    @classmethod
    def from_info(cls, info: dict[str, Any]) -> MediaInfo:
        is_playlist = info.get("_type") == "playlist"
        entries = info.get("entries")
        return cls(
            title=info.get("title") or info.get("id") or "Untitled",
            uploader=info.get("uploader") or info.get("channel"),
            duration=info.get("duration"),
            thumbnail=info.get("thumbnail"),
            webpage_url=info.get("webpage_url"),
            is_playlist=is_playlist,
            entry_count=info.get("playlist_count") or (
                len(entries) if is_playlist and isinstance(entries, list) else None),
        )


@dataclass(frozen=True)
class Progress:
    status: str  # "downloading" | "processing"
    downloaded: int | None = None
    total: int | None = None
    speed: float | None = None
    eta: float | None = None
    item_index: int | None = None
    item_count: int | None = None
    detail: str = ""

    @property
    def fraction(self) -> float | None:
        if self.downloaded is None or not self.total:
            return None
        return min(self.downloaded / self.total, 1.0)


class _YdlLogger:
    """Routes yt-dlp output into the logging module instead of the terminal."""

    def debug(self, msg: str) -> None:
        if msg.startswith("[debug] "):
            log.debug(msg)
        else:
            log.info(msg)

    def info(self, msg: str) -> None:
        log.info(msg)

    def warning(self, msg: str) -> None:
        log.warning(msg)

    def error(self, msg: str) -> None:
        log.error(msg)


class DownloadJob:
    """One URL (a video or a playlist) downloaded with the given options.

    ``run()`` blocks, so call it from a worker thread. ``cancel()`` is thread-safe.
    """

    def __init__(
        self,
        url: str,
        options: DownloadOptions,
        *,
        on_info: Callable[[MediaInfo], None] | None = None,
        on_progress: Callable[[Progress], None] | None = None,
    ) -> None:
        self.url = url
        self.options = options
        self._on_info = on_info or (lambda _info: None)
        self._on_progress = on_progress or (lambda _progress: None)
        self._cancel = threading.Event()
        self._last_emit = 0.0
        self.files: list[Path] = []

    @property
    def cancelled(self) -> bool:
        return self._cancel.is_set()

    def cancel(self) -> None:
        self._cancel.set()

    def run(self) -> list[Path]:
        """Download everything and return the final file paths."""
        self._check_cancel()
        ffmpeg = has_ffmpeg()
        ydl_opts = build_ydl_opts(self.options, ffmpeg_available=ffmpeg)
        ydl_opts.update(
            quiet=True,
            noprogress=True,
            logger=_YdlLogger(),
            progress_hooks=[self._progress_hook],
            postprocessor_hooks=[self._postprocessor_hook],
        )
        self.options.output_dir.mkdir(parents=True, exist_ok=True)
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                if info is None:
                    raise DownloadFailed("No downloadable media found at this URL")
                self._check_cancel()
                self._on_info(MediaInfo.from_info(info))
                ydl.process_ie_result(info, download=True)
        except (DownloadCancelled, JobCancelled):
            raise JobCancelled from None
        except (DownloadError, ExtractorError) as exc:
            if self.cancelled:
                raise JobCancelled from None
            message = clean_error(str(exc))
            if not ffmpeg and "Requested format is not available" in message:
                message = NO_FFMPEG_MESSAGE
            raise DownloadFailed(message) from exc

        if not self.files:
            raise DownloadFailed("Nothing was downloaded")
        return self.files

    def _check_cancel(self) -> None:
        if self.cancelled:
            raise JobCancelled

    def _progress_hook(self, d: dict[str, Any]) -> None:
        if self.cancelled:
            # yt-dlp lets this exception propagate and aborts the download.
            raise DownloadCancelled("Cancelled by user")
        status = d.get("status")
        info = d.get("info_dict") or {}
        index, count = info.get("playlist_index"), info.get("n_entries")
        if status == "downloading":
            now = time.monotonic()
            if now - self._last_emit < PROGRESS_INTERVAL:
                return
            self._last_emit = now
            self._on_progress(Progress(
                status="downloading",
                downloaded=d.get("downloaded_bytes"),
                total=d.get("total_bytes") or d.get("total_bytes_estimate"),
                speed=d.get("speed"),
                eta=d.get("eta"),
                item_index=index,
                item_count=count,
                detail=_stream_label(info),
            ))
        elif status == "finished":
            self._last_emit = 0.0
            self._on_progress(Progress(status="processing", item_index=index, item_count=count,
                                       detail="Finishing download"))

    def _postprocessor_hook(self, d: dict[str, Any]) -> None:
        info = d.get("info_dict") or {}
        if d.get("status") == "started":
            self._on_progress(Progress(
                status="processing",
                item_index=info.get("playlist_index"),
                item_count=info.get("n_entries"),
                detail=_PP_LABELS.get(d.get("postprocessor", ""), "Processing"),
            ))
        elif (d.get("status") == "finished" and d.get("postprocessor") == "MoveFiles"
              and (filepath := info.get("filepath"))):
            # MoveFiles is always the last step for each video and knows the final path.
            self.files.append(Path(filepath))


_PP_LABELS = {
    "Merger": "Merging video and audio",
    "ExtractAudio": "Converting audio",
    "FFmpegExtractAudio": "Converting audio",
    "EmbedThumbnail": "Embedding thumbnail",
    "FFmpegMetadata": "Writing metadata",
    "Metadata": "Writing metadata",
    "FFmpegEmbedSubtitle": "Embedding subtitles",
    "EmbedSubtitle": "Embedding subtitles",
    "FFmpegThumbnailsConvertor": "Converting thumbnail",
    "ThumbnailsConvertor": "Converting thumbnail",
    "VideoRemuxer": "Remuxing",
    "VideoConvertor": "Converting video",
    "MoveFiles": "Saving file",
}


def _stream_label(info: dict[str, Any]) -> str:
    vcodec, acodec = info.get("vcodec"), info.get("acodec")
    if vcodec and vcodec != "none" and acodec == "none":
        return "Video stream"
    if acodec and acodec != "none" and vcodec == "none":
        return "Audio stream"
    return ""
