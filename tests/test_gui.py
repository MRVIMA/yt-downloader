from pathlib import Path

import pytest

pytest.importorskip("PySide6")

from yt_downloader.core import DownloadOptions, MediaInfo, Progress  # noqa: E402


def test_settings_roundtrip(settings):
    settings.preset = "720"
    settings.max_concurrent = 99
    settings.cookies_from_browser = "not-a-browser"
    assert settings.preset == "720"
    assert settings.max_concurrent == 5
    assert settings.cookies_from_browser == ""
    opts = settings.download_options()
    assert opts.preset == "720" and opts.cookies_from_browser is None


def test_main_window_builds(settings):
    from yt_downloader.gui.main_window import MainWindow

    window = MainWindow(settings)
    assert window.count_label.text() == "Ready"
    assert window.preset_combo.count() > 5
    window.url_edit.setText("not a link")
    window.start_from_input()
    assert window.items == []


def test_download_item_state_flow(qapp, tmp_path):
    from yt_downloader.gui.download_item import DownloadItem, State

    item = DownloadItem("https://example.com/v", DownloadOptions(output_dir=tmp_path))
    item.create_worker()
    assert item.state == State.QUEUED and item.cancel_btn.isVisibleTo(item)

    item.on_info(MediaInfo(title="Hello", uploader="Someone", duration=90))
    assert item.title_label.text() == "Hello"
    assert "Someone" in item.meta_label.text()

    item.on_progress(Progress("downloading", downloaded=512, total=1024, speed=100.0, eta=5))
    assert item.state == State.DOWNLOADING
    assert item.progress.value() == 500
    assert "50%" in item.status_label.text()

    item.on_finished([tmp_path / "Hello.mp4"])
    assert item.state == State.DONE
    assert item.output_folder() == Path(tmp_path)
    assert item.open_btn.isVisibleTo(item) and not item.cancel_btn.isVisibleTo(item)


def test_cancel_queued_item(qapp, tmp_path):
    from yt_downloader.gui.download_item import DownloadItem, State

    item = DownloadItem("https://example.com/v", DownloadOptions(output_dir=tmp_path))
    worker = item.create_worker()
    item.cancel()
    assert item.state == State.CANCELLED
    assert worker.job.cancelled
    assert item.retry_btn.isVisibleTo(item)
