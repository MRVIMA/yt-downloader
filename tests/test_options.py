from pathlib import Path

import pytest
from yt_dlp import YoutubeDL

from yt_downloader.core.options import DownloadOptions, build_ydl_opts


def keys(ydl_opts):
    return [pp["key"] for pp in ydl_opts.get("postprocessors", [])]


def test_best_video_defaults(tmp_path):
    o = build_ydl_opts(DownloadOptions(output_dir=tmp_path))
    assert o["format"] == "bv*+ba/b"
    assert o["noplaylist"] is True
    assert "merge_output_format" not in o
    assert keys(o) == ["FFmpegThumbnailsConvertor", "FFmpegMetadata", "EmbedThumbnail"]
    assert "deno" in o["js_runtimes"]


def test_height_and_mp4_container(tmp_path):
    o = build_ydl_opts(DownloadOptions(output_dir=tmp_path, preset="720", container="mp4"))
    assert o["format"].startswith("bv*[height<=720][ext=mp4]+ba[ext=m4a]")
    assert o["merge_output_format"] == "mp4"


def test_audio_preset_extracts(tmp_path):
    o = build_ydl_opts(DownloadOptions(output_dir=tmp_path, preset="mp3",
                                       embed_thumbnail=False, embed_metadata=False))
    assert o["format"] == "ba/b"
    assert o["postprocessors"] == [
        {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "0"}]


def test_without_ffmpeg_uses_single_file_and_no_postprocessing(tmp_path):
    o = build_ydl_opts(DownloadOptions(output_dir=tmp_path, preset="1080"),
                       ffmpeg_available=False)
    assert o["format"] == "b[height<=1080]/b"
    assert "postprocessors" not in o
    assert "writethumbnail" not in o


def test_subtitles_only_for_video(tmp_path):
    video = build_ydl_opts(DownloadOptions(output_dir=tmp_path, embed_subtitles=True,
                                           subtitle_langs=("en", "de")))
    assert video["subtitleslangs"] == ["en", "de"]
    assert "FFmpegEmbedSubtitle" in keys(video)
    audio = build_ydl_opts(DownloadOptions(output_dir=tmp_path, preset="m4a",
                                           embed_subtitles=True))
    assert "writesubtitles" not in audio


def test_cookies_and_validation(tmp_path):
    o = build_ydl_opts(DownloadOptions(output_dir=tmp_path, cookies_from_browser="firefox"))
    assert o["cookiesfrombrowser"] == ("firefox",)
    with pytest.raises(ValueError):
        DownloadOptions(cookies_from_browser="netscape")
    with pytest.raises(ValueError):
        DownloadOptions(container="avi")


def _filename(opts, info):
    with YoutubeDL({"outtmpl": build_ydl_opts(opts)["outtmpl"], "quiet": True}) as ydl:
        return Path(ydl.prepare_filename(info))


def test_output_template_single_video(tmp_path):
    info = {"id": "abc", "title": "My Video", "ext": "mp4"}
    assert _filename(DownloadOptions(output_dir=tmp_path), info) == tmp_path / "My Video [abc].mp4"


def test_output_template_playlist(tmp_path):
    opts = DownloadOptions(output_dir=tmp_path, playlist=True)
    info = {"id": "abc", "title": "Song", "ext": "mp4", "playlist_title": "Mix",
            "playlist_index": 7}
    assert _filename(opts, info) == tmp_path / "Mix" / "007 - Song [abc].mp4"
    # A plain video URL with "whole playlist" ticked still lands in the output folder.
    single = {"id": "abc", "title": "Song", "ext": "mp4"}
    assert _filename(opts, single) == tmp_path / "Song [abc].mp4"
