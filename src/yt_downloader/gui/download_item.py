"""One row in the download queue."""

from __future__ import annotations

import enum
from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
)

from yt_downloader.core import DownloadOptions, MediaInfo, Progress, get_preset
from yt_downloader.core.utils import format_bytes, format_eta
from yt_downloader.gui.icons import themed
from yt_downloader.gui.worker import DownloadWorker


class ElidedLabel(QLabel):
    """A single-line label that shrinks with "…" instead of forcing the window wider."""

    def __init__(self, text: str = "", parent=None) -> None:
        super().__init__(parent)
        self._full_text = ""
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.setText(text)

    def setText(self, text: str) -> None:  # noqa: N802 (Qt naming)
        self._full_text = text
        self._update_elided()

    def text(self) -> str:
        return self._full_text

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self) -> None:
        elided = self.fontMetrics().elidedText(self._full_text, Qt.TextElideMode.ElideRight,
                                               max(self.width(), 50))
        super().setText(elided)


class State(enum.Enum):
    QUEUED = "Queued"
    FETCHING = "Fetching info…"
    DOWNLOADING = "Downloading"
    PROCESSING = "Processing"
    DONE = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"

    @property
    def is_active(self) -> bool:
        return self in (State.QUEUED, State.FETCHING, State.DOWNLOADING, State.PROCESSING)


class DownloadItem(QFrame):
    """Shows title, status and progress for one URL, and owns its worker."""

    state_changed = Signal()
    retry_requested = Signal(object)  # DownloadItem
    remove_requested = Signal(object)  # DownloadItem

    def __init__(self, url: str, options: DownloadOptions, parent=None) -> None:
        super().__init__(parent)
        self.url = url
        self.options = options
        self.state = State.QUEUED
        self.files: list[Path] = []
        self.worker: DownloadWorker | None = None

        self.setObjectName("downloadItem")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.title_label = ElidedLabel(url)
        self.title_label.setObjectName("itemTitle")
        self.title_label.setToolTip(url)
        font = self.title_label.font()
        font.setBold(True)
        self.title_label.setFont(font)

        self.meta_label = QLabel(get_preset(options.preset).label)
        self.meta_label.setObjectName("itemMeta")
        self.meta_label.setEnabled(False)  # renders as secondary text in every theme

        self.status_label = ElidedLabel(State.QUEUED.value)
        self.status_label.setObjectName("itemStatus")

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(8)

        self.cancel_btn = self._tool_button("process-stop", "Cancel", self.cancel)
        self.retry_btn = self._tool_button("view-refresh", "Retry",
                                           lambda: self.retry_requested.emit(self))
        self.open_btn = self._tool_button("folder-open", "Show in folder", self.open_folder)
        self.remove_btn = self._tool_button("edit-delete", "Remove from list",
                                            lambda: self.remove_requested.emit(self))

        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(self.title_label)
        text_col.addWidget(self.meta_label)
        text_col.addWidget(self.progress)
        text_col.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.setSpacing(2)
        for btn in (self.cancel_btn, self.retry_btn, self.open_btn, self.remove_btn):
            buttons.addWidget(btn)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 8, 10)
        row.addLayout(text_col, 1)
        row.addLayout(buttons)

        self._set_state(State.QUEUED)

    def _tool_button(self, icon: str, tip: str, slot) -> QToolButton:
        btn = QToolButton()
        btn.setIcon(themed(icon))
        btn.setToolTip(tip)
        btn.setAutoRaise(True)
        btn.clicked.connect(slot)
        return btn

    # Worker wiring ----------------------------------------------------------------------

    def create_worker(self) -> DownloadWorker:
        self.worker = DownloadWorker(self.url, self.options)
        s = self.worker.signals
        s.started.connect(lambda: self._set_state(State.FETCHING))
        s.info.connect(self.on_info)
        s.progress.connect(self.on_progress)
        s.finished.connect(self.on_finished)
        s.failed.connect(self.on_failed)
        s.cancelled.connect(lambda: self._set_state(State.CANCELLED))
        self._set_state(State.QUEUED)
        return self.worker

    def cancel(self) -> None:
        if self.worker and self.state.is_active:
            self.worker.cancel()
            if self.state == State.QUEUED:
                self._set_state(State.CANCELLED)
            else:
                self.status_label.setText("Cancelling…")

    # Slots -------------------------------------------------------------------------------

    def on_info(self, info: MediaInfo) -> None:
        self.title_label.setText(info.title)
        self.title_label.setToolTip(f"{info.title}\n{self.url}")
        parts = [get_preset(self.options.preset).label]
        if info.is_playlist:
            parts.insert(0, f"Playlist · {info.entry_count or '?'} items")
        elif info.uploader:
            parts.insert(0, info.uploader)
        if info.duration and not info.is_playlist:
            parts.append(format_eta(info.duration))
        self.meta_label.setText("  ·  ".join(parts))

    def on_progress(self, p: Progress) -> None:
        if self.state in (State.CANCELLED, State.FAILED, State.DONE):
            return
        prefix = f"Item {p.item_index} of {p.item_count} · " if p.item_index and p.item_count \
            else ""
        if p.status == "downloading":
            self._set_state(State.DOWNLOADING, update_label=False)
            if p.fraction is None:
                self.progress.setRange(0, 0)
                pct = ""
            else:
                self.progress.setRange(0, 1000)
                self.progress.setValue(int(p.fraction * 1000))
                pct = f"{p.fraction * 100:.0f}% · "
            speed = f" · {format_bytes(p.speed)}/s" if p.speed else ""
            eta = f" · {format_eta(p.eta)} left" if p.eta is not None else ""
            detail = f"{p.detail} · " if p.detail else ""
            self.status_label.setText(
                f"{prefix}{detail}{pct}{format_bytes(p.downloaded)} of {format_bytes(p.total)}"
                f"{speed}{eta}")
        else:
            self._set_state(State.PROCESSING, update_label=False)
            self.progress.setRange(0, 0)
            self.status_label.setText(f"{prefix}{p.detail or 'Processing'}…")

    def on_finished(self, files: list[Path]) -> None:
        self.files = files
        self._set_state(State.DONE)
        if len(files) == 1:
            self.status_label.setText(f"Saved as {files[0].name}")
            self.status_label.setToolTip(str(files[0]))
        else:
            self.status_label.setText(f"Saved {len(files)} files to {self.output_folder()}")

    def on_failed(self, message: str) -> None:
        self._set_state(State.FAILED)
        self.status_label.setText(message)
        self.status_label.setToolTip(message)

    # Helpers -----------------------------------------------------------------------------

    def output_folder(self) -> Path:
        if self.files:
            return self.files[0].parent
        return self.options.output_dir

    def open_folder(self) -> None:
        folder = self.output_folder()
        if not folder.exists():
            folder = self.options.output_dir
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _set_state(self, state: State, *, update_label: bool = True) -> None:
        changed = state != self.state
        self.state = state
        if update_label:
            self.status_label.setText(state.value)
            self.status_label.setToolTip("")
        if state in (State.DONE, State.FAILED, State.CANCELLED):
            self.progress.setRange(0, 1000)
            self.progress.setValue(1000 if state == State.DONE else self.progress.value())
        elif state in (State.QUEUED, State.FETCHING):
            self.progress.setRange(0, 0 if state == State.FETCHING else 1000)
            if state == State.QUEUED:
                self.progress.setValue(0)

        self.setProperty("state", state.name.lower())
        for widget in (self, self.status_label):  # re-apply the [state=...] stylesheet rules
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self.cancel_btn.setVisible(state.is_active)
        self.retry_btn.setVisible(state in (State.FAILED, State.CANCELLED))
        self.open_btn.setVisible(state == State.DONE)
        self.remove_btn.setVisible(not state.is_active)
        if changed:
            self.state_changed.emit()
