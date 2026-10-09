from pathlib import Path

from yt_downloader.cli import options_from_args, parse_args


def test_defaults():
    args = parse_args(["https://example.com/v"])
    opts = options_from_args(args)
    assert opts.preset == "best"
    assert not opts.playlist and not opts.embed_subtitles


def test_flags():
    args = parse_args(["-a", "-p", "-o", "/tmp/x", "--subs", "en, de", "--no-thumbnail",
                       "https://example.com/v"])
    opts = options_from_args(args)
    assert opts.preset == "mp3"
    assert opts.playlist
    assert opts.output_dir == Path("/tmp/x")
    assert opts.subtitle_langs == ("en", "de")
    assert not opts.embed_thumbnail
