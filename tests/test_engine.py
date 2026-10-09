from pathlib import Path

import pytest
from yt_dlp.utils import DownloadCancelled

from yt_downloader.core import DownloadJob, DownloadOptions, MediaInfo


def make_job(tmp_path, events):
    return DownloadJob("https://example.com/v", DownloadOptions(output_dir=tmp_path),
                       on_progress=events.append)


def test_progress_hook_reports_download(tmp_path):
    events = []
    job = make_job(tmp_path, events)
    job._progress_hook({"status": "downloading", "downloaded_bytes": 50, "total_bytes": 200,
                        "speed": 10.0, "eta": 15,
                        "info_dict": {"vcodec": "vp9", "acodec": "none"}})
    (p,) = events
    assert p.fraction == 0.25
    assert p.detail == "Video stream"


def test_progress_hook_throttles(tmp_path):
    events = []
    job = make_job(tmp_path, events)
    for _ in range(5):
        job._progress_hook({"status": "downloading", "downloaded_bytes": 1, "total_bytes": 2})
    assert len(events) == 1
    job._progress_hook({"status": "finished"})
    assert events[-1].status == "processing"


def test_cancel_aborts_from_hook(tmp_path):
    job = make_job(tmp_path, [])
    job.cancel()
    with pytest.raises(DownloadCancelled):
        job._progress_hook({"status": "downloading"})


def test_postprocessor_hook_collects_final_files(tmp_path):
    events = []
    job = make_job(tmp_path, events)
    job._postprocessor_hook({"status": "started", "postprocessor": "Merger", "info_dict": {}})
    assert events[-1].detail == "Merging video and audio"
    job._postprocessor_hook({"status": "finished", "postprocessor": "MoveFiles",
                             "info_dict": {"filepath": str(tmp_path / "a.mp4")}})
    assert job.files == [Path(tmp_path / "a.mp4")]


def test_media_info_from_playlist():
    info = MediaInfo.from_info({"_type": "playlist", "title": "Mix",
                                "entries": [{}, {}, {}]})
    assert info.is_playlist and info.entry_count == 3
    assert MediaInfo.from_info({"id": "x"}).title == "x"


def test_missing_ffmpeg_gives_clear_error(tmp_path, monkeypatch):
    from yt_dlp.utils import DownloadError

    from yt_downloader.core import DownloadFailed, engine

    class FakeYDL:
        def __init__(self, opts):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def extract_info(self, url, download):
            raise DownloadError("ERROR: [youtube] x: Requested format is not available")

    monkeypatch.setattr(engine, "YoutubeDL", FakeYDL)
    monkeypatch.setattr(engine, "has_ffmpeg", lambda: False)
    job = DownloadJob("https://example.com/v", DownloadOptions(output_dir=tmp_path))
    with pytest.raises(DownloadFailed, match="needs ffmpeg"):
        job.run()
