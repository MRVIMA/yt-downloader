"""Command-line interface: ``yt-downloader-cli``."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from yt_downloader import __version__
from yt_downloader.core import (
    PRESETS,
    DownloadFailed,
    DownloadJob,
    DownloadOptions,
    JobCancelled,
    MediaInfo,
    Progress,
)
from yt_downloader.core.options import CONTAINERS, COOKIE_BROWSERS
from yt_downloader.core.utils import (
    default_download_dir,
    format_bytes,
    format_eta,
    has_ffmpeg,
    has_js_runtime,
    use_bundled_tools,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yt-downloader-cli",
        description="Download video or audio from YouTube and hundreds of other sites.",
    )
    parser.add_argument("urls", nargs="+", metavar="URL", help="one or more video/playlist URLs")
    parser.add_argument("-o", "--output", type=Path, default=default_download_dir(),
                        help="output directory (default: %(default)s)")
    parser.add_argument("-f", "--format", dest="preset", default="best",
                        choices=[p.key for p in PRESETS],
                        help="quality preset (default: %(default)s)")
    parser.add_argument("-a", "--audio", action="store_const", const="mp3", dest="preset",
                        help="shortcut for --format mp3")
    parser.add_argument("-c", "--container", choices=CONTAINERS, default="auto",
                        help="video container (default: %(default)s)")
    parser.add_argument("-p", "--playlist", action="store_true",
                        help="download the whole playlist when the URL contains one")
    parser.add_argument("--subs", metavar="LANGS",
                        help="embed subtitles, comma-separated language codes (e.g. en,de)")
    parser.add_argument("--no-metadata", action="store_true", help="don't embed metadata")
    parser.add_argument("--no-thumbnail", action="store_true", help="don't embed thumbnail")
    parser.add_argument("--cookies-from-browser", choices=COOKIE_BROWSERS, metavar="BROWSER",
                        help=f"use cookies from a browser ({', '.join(COOKIE_BROWSERS)})")
    parser.add_argument("-v", "--verbose", action="store_true", help="show yt-dlp log output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def options_from_args(args: argparse.Namespace) -> DownloadOptions:
    return DownloadOptions(
        output_dir=args.output,
        preset=args.preset,
        container=args.container,
        playlist=args.playlist,
        embed_metadata=not args.no_metadata,
        embed_thumbnail=not args.no_thumbnail,
        embed_subtitles=bool(args.subs),
        subtitle_langs=tuple(s.strip() for s in args.subs.split(",")) if args.subs else ("en",),
        cookies_from_browser=args.cookies_from_browser,
    )


class _Printer:
    def __init__(self) -> None:
        self._tty = sys.stderr.isatty()
        self._last_line = ""

    def info(self, info: MediaInfo) -> None:
        kind = f"playlist, {info.entry_count} items" if info.is_playlist else info.uploader
        print(f"\n▶ {info.title}" + (f"  ({kind})" if kind else ""), file=sys.stderr)

    def progress(self, p: Progress) -> None:
        prefix = f"[{p.item_index}/{p.item_count}] " if p.item_index and p.item_count else ""
        if p.status == "downloading":
            pct = f"{p.fraction * 100:5.1f}%" if p.fraction is not None else "  ?  "
            speed = f"{format_bytes(p.speed)}/s" if p.speed else "-"
            line = (f"{prefix}{pct}  of {format_bytes(p.total)}  at {speed}  "
                    f"ETA {format_eta(p.eta)}")
        else:
            line = f"{prefix}{p.detail}..."
        if line == self._last_line:
            return
        self._last_line = line
        if self._tty:
            print(f"\r\033[K  {line}", end="", file=sys.stderr, flush=True)
        elif p.status != "downloading":
            print(f"  {line}", file=sys.stderr)

    def done(self) -> None:
        if self._tty:
            print("\r\033[K", end="", file=sys.stderr)


def _safe_console() -> None:
    """Never crash on symbols like ✓ when the console/pipe uses a legacy code page (Windows)."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _safe_console()
    # Errors are reported once by us below; yt-dlp's own log lines only appear with -v.
    logging.basicConfig(level=logging.INFO if args.verbose else logging.CRITICAL,
                        format="%(message)s")
    use_bundled_tools()
    try:
        options = options_from_args(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if not has_ffmpeg():
        print("warning: ffmpeg not found - merging, audio conversion and embedding are disabled",
              file=sys.stderr)
    if not has_js_runtime():
        print("warning: no JavaScript runtime (deno) found - some YouTube formats may be missing",
              file=sys.stderr)

    printer = _Printer()
    failures = 0
    for url in args.urls:
        job = DownloadJob(url, options, on_info=printer.info, on_progress=printer.progress)
        try:
            files = job.run()
        except KeyboardInterrupt:
            printer.done()
            print("\nCancelled.", file=sys.stderr)
            return 130
        except JobCancelled:
            printer.done()
            return 130
        except DownloadFailed as exc:
            printer.done()
            print(f"  ✗ {url}: {exc}", file=sys.stderr)
            failures += 1
            continue
        printer.done()
        for path in files:
            print(f"  ✓ {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
