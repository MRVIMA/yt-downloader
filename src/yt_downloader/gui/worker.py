"""Runs a DownloadJob on a QThreadPool and relays its callbacks as Qt signals."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QRunnable, Signal

from yt_downloader.core import DownloadFailed, DownloadJob, DownloadOptions, JobCancelled

log = logging.getLogger(__name__)


class WorkerSignals(QObject):
    started = Signal()
    info = Signal(object)  # MediaInfo
    progress = Signal(object)  # Progress
    finished = Signal(list)  # list[Path]
    failed = Signal(str)
    cancelled = Signal()


class DownloadWorker(QRunnable):
    def __init__(self, url: str, options: DownloadOptions) -> None:
        super().__init__()
        # The owning DownloadItem keeps a reference, so Qt must not delete us.
        self.setAutoDelete(False)
        self.signals = WorkerSignals()
        self.job = DownloadJob(
            url, options,
            on_info=self.signals.info.emit,
            on_progress=self.signals.progress.emit,
        )

    def cancel(self) -> None:
        self.job.cancel()

    def run(self) -> None:
        if self.job.cancelled:
            self.signals.cancelled.emit()
            return
        self.signals.started.emit()
        try:
            files = self.job.run()
        except JobCancelled:
            self.signals.cancelled.emit()
        except DownloadFailed as exc:
            log.warning("Download failed for %s: %s", self.job.url, exc)
            self.signals.failed.emit(str(exc))
        except Exception as exc:  # never let an exception escape into the thread pool
            log.exception("Unexpected error downloading %s", self.job.url)
            self.signals.failed.emit(f"Unexpected error: {exc}")
        else:
            self.signals.finished.emit(files)
