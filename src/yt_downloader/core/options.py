"""User-facing download options and their translation into yt-dlp parameters."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from yt_downloader.core.presets import DEFAULT_PRESET, get_preset
from yt_downloader.core.utils import default_download_dir

DEFAULT_TEMPLATE = "%(title)s [%(id)s].%(ext)s"
CONTAINERS = ("auto", "mp4", "mkv")
COOKIE_BROWSERS = (
    "firefox", "chrome", "chromium", "brave", "edge", "opera", "vivaldi", "whale",
)


@dataclass
class DownloadOptions:
    output_dir: Path = field(default_factory=default_download_dir)
    preset: str = DEFAULT_PRESET
    container: str = "auto"
    filename_template: str = DEFAULT_TEMPLATE
    playlist: bool = False
    embed_metadata: bool = True
    embed_thumbnail: bool = True
    embed_subtitles: bool = False
    subtitle_langs: tuple[str, ...] = ("en",)
    cookies_from_browser: str | None = None

    def __post_init__(self) -> None:
        get_preset(self.preset)  # validate early
        if self.container not in CONTAINERS:
            raise ValueError(f"Unknown container {self.container!r}")
        if self.cookies_from_browser and self.cookies_from_browser not in COOKIE_BROWSERS:
            raise ValueError(f"Unsupported browser {self.cookies_from_browser!r}")
        self.output_dir = Path(self.output_dir).expanduser()


def _video_format(max_height: int | None, container: str) -> str:
    h = f"[height<={max_height}]" if max_height else ""
    if container == "mp4":
        return f"bv*{h}[ext=mp4]+ba[ext=m4a]/b{h}[ext=mp4]/bv*{h}+ba/b{h}"
    return f"bv*{h}+ba/b{h}"


def build_ydl_opts(opts: DownloadOptions, *, ffmpeg_available: bool = True) -> dict[str, Any]:
    """Build the yt-dlp parameter dict for ``opts``.

    Without ffmpeg we can't merge streams or convert, so we fall back to
    single-file formats and skip every post-processor.
    """
    preset = get_preset(opts.preset)
    template = opts.filename_template or DEFAULT_TEMPLATE
    if opts.playlist:
        # Empty fields collapse to "" so single videos still land directly in output_dir.
        template = f"%(playlist_title|)s/%(playlist_index&{{:03d}} - |)s{template}"

    ydl: dict[str, Any] = {
        "outtmpl": str(opts.output_dir / template),
        "noplaylist": not opts.playlist,
        "windowsfilenames": False,
        "restrictfilenames": False,
        "continuedl": True,
        "retries": 10,
        "fragment_retries": 10,
        "concurrent_fragment_downloads": 4,
        # Enable every supported JS runtime; yt-dlp uses whichever is installed.
        "js_runtimes": {"deno": {}, "node": {}, "bun": {}, "quickjs": {}},
    }
    if opts.playlist:
        ydl["ignoreerrors"] = "only_download"  # one broken video shouldn't sink the playlist
    if opts.cookies_from_browser:
        ydl["cookiesfrombrowser"] = (opts.cookies_from_browser,)

    postprocessors: list[dict[str, Any]] = []

    if preset.is_audio:
        ydl["format"] = "ba/b"
        if ffmpeg_available:
            postprocessors.append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": preset.audio_codec,
                "preferredquality": "0",
            })
    elif ffmpeg_available:
        ydl["format"] = _video_format(preset.max_height, opts.container)
        if opts.container != "auto":
            ydl["merge_output_format"] = opts.container
        if opts.embed_subtitles:
            ydl.update(writesubtitles=True, subtitleslangs=list(opts.subtitle_langs))
            postprocessors.append({"key": "FFmpegEmbedSubtitle", "already_have_subtitle": False})
    else:
        h = f"[height<={preset.max_height}]" if preset.max_height else ""
        ydl["format"] = f"b{h}/b"

    if ffmpeg_available:
        if opts.embed_metadata:
            postprocessors.append({"key": "FFmpegMetadata", "add_metadata": True,
                                   "add_chapters": True})
        if opts.embed_thumbnail:
            ydl["writethumbnail"] = True
            postprocessors.insert(0, {"key": "FFmpegThumbnailsConvertor", "format": "jpg",
                                      "when": "before_dl"})
            postprocessors.append({"key": "EmbedThumbnail", "already_have_thumbnail": False})

    if postprocessors:
        ydl["postprocessors"] = postprocessors
    return ydl
