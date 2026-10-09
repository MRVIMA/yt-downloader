"""The main application window: URL entry, options and the download queue."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication, QKeySequence
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from yt_downloader import APP_NAME, __version__
from yt_downloader.core.presets import PRESETS
from yt_downloader.core.utils import extract_urls, has_ffmpeg, has_js_runtime, state_dir
from yt_downloader.gui.download_item import DownloadItem, ElidedLabel, State
from yt_downloader.gui.icons import app_icon, themed
from yt_downloader.gui.settings import AppSettings
from yt_downloader.gui.settings_dialog import SettingsDialog

log = logging.getLogger(__name__)

STYLESHEET = """
#downloadItem { background: palette(base); border: 1px solid palette(midlight);
                border-radius: 8px; }
#downloadItem[state="failed"] #itemStatus { color: #d64545; }
#downloadItem[state="done"] #itemStatus { color: #2e9e5b; }
#banner { background: rgba(232, 160, 32, 0.15); border: 1px solid rgba(232, 160, 32, 0.55);
          border-radius: 6px; }
#emptyState { font-size: 15px; }
"""


class MainWindow(QMainWindow):
    def __init__(self, settings: AppSettings | None = None) -> None:
        super().__init__()
        self.settings = settings or AppSettings()
        self.items: list[DownloadItem] = []
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(self.settings.max_concurrent)

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLESHEET)
        self.resize(820, 600)
        if geometry := self.settings.window_geometry:
            self.restoreGeometry(geometry)

        self._build_menu()
        self._build_ui()
        self._update_counts()

    # UI construction -------------------------------------------------------------------

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        paste = QAction(themed("edit-paste"), "&Paste and Download", self)
        paste.setShortcut(QKeySequence("Ctrl+Shift+V"))
        paste.triggered.connect(self.paste_and_download)
        file_menu.addAction(paste)
        open_folder = QAction(themed("folder-open"), "&Open Download Folder", self)
        open_folder.setShortcut(QKeySequence("Ctrl+O"))
        open_folder.triggered.connect(self.open_download_folder)
        file_menu.addAction(open_folder)
        file_menu.addSeparator()
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        edit_menu = self.menuBar().addMenu("&Edit")
        prefs = QAction("&Preferences…", self)
        prefs.setShortcut(QKeySequence("Ctrl+,"))
        prefs.triggered.connect(self.open_settings)
        edit_menu.addAction(prefs)

        help_menu = self.menuBar().addMenu("&Help")
        logs = QAction("Open &Log Folder", self)
        logs.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(state_dir()))))
        help_menu.addAction(logs)
        about = QAction(f"&About {APP_NAME}", self)
        about.triggered.connect(self.show_about)
        help_menu.addAction(about)

    def _build_ui(self) -> None:
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)

        # Missing-dependency banner
        warnings = []
        if not has_ffmpeg():
            warnings.append("<b>ffmpeg</b> is not installed — most video downloads (including "
                            "YouTube), audio conversion and embedding won't work.")
        if not has_js_runtime():
            warnings.append("<b>deno</b> is not installed — some YouTube videos may fail "
                            "or offer fewer formats.")
        if warnings:
            banner = QLabel("<br>".join(warnings) + " See the README for install steps.")
            banner.setObjectName("banner")
            banner.setWordWrap(True)
            banner.setContentsMargins(10, 8, 10, 8)
            root.addWidget(banner)

        # URL row
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a video or playlist URL — or drop links here")
        self.url_edit.setClearButtonEnabled(True)
        self.url_edit.setMinimumHeight(36)
        self.url_edit.returnPressed.connect(self.start_from_input)

        paste_btn = QToolButton()
        paste_btn.setIcon(themed("edit-paste"))
        paste_btn.setToolTip("Paste from clipboard")
        paste_btn.setMinimumHeight(36)
        paste_btn.clicked.connect(self.paste_into_input)

        self.download_btn = QPushButton(themed("download"), "Download")
        self.download_btn.setDefault(True)
        self.download_btn.setMinimumHeight(36)
        self.download_btn.clicked.connect(self.start_from_input)

        url_row = QHBoxLayout()
        url_row.addWidget(self.url_edit, 1)
        url_row.addWidget(paste_btn)
        url_row.addWidget(self.download_btn)
        root.addLayout(url_row)

        # Options row
        self.preset_combo = QComboBox()
        for p in PRESETS:
            self.preset_combo.addItem(p.label, p.key)
        self.preset_combo.setCurrentIndex(max(self.preset_combo.findData(self.settings.preset),
                                              0))
        self.preset_combo.currentIndexChanged.connect(
            lambda: setattr(self.settings, "preset", self.preset_combo.currentData()))

        self.playlist_cb = QCheckBox("Whole playlist")
        self.playlist_cb.setToolTip("If the link belongs to a playlist, download every video")
        self.playlist_cb.setChecked(self.settings.playlist)
        self.playlist_cb.toggled.connect(lambda v: setattr(self.settings, "playlist", v))

        self.folder_label = ElidedLabel()
        self.folder_label.setEnabled(False)
        folder_btn = QPushButton(themed("folder-open"), "Change…")
        folder_btn.clicked.connect(self.choose_folder)

        options_row = QHBoxLayout()
        options_row.addWidget(QLabel("Quality:"))
        options_row.addWidget(self.preset_combo)
        options_row.addSpacing(8)
        options_row.addWidget(self.playlist_cb)
        options_row.addSpacing(16)
        options_row.addWidget(QLabel("Save to:"))
        options_row.addWidget(self.folder_label, 1)
        options_row.addWidget(folder_btn)
        root.addLayout(options_row)
        self._refresh_folder_label()

        # Queue
        self.queue_widget = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_widget)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(8)
        self.empty_label = QLabel("No downloads yet.\nPaste a link above to get started.")
        self.empty_label.setObjectName("emptyState")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setEnabled(False)
        self.queue_layout.addWidget(self.empty_label, 1)
        self.queue_layout.addStretch(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(self.queue_widget)
        root.addWidget(scroll, 1)

        # Footer
        self.count_label = QLabel()
        self.count_label.setEnabled(False)
        self.cancel_all_btn = QPushButton(themed("process-stop"), "Cancel All")
        self.cancel_all_btn.clicked.connect(self.cancel_all)
        self.clear_btn = QPushButton(themed("edit-clear-history"), "Clear Finished")
        self.clear_btn.clicked.connect(self.clear_finished)
        footer = QHBoxLayout()
        footer.addWidget(self.count_label, 1)
        footer.addWidget(self.cancel_all_btn)
        footer.addWidget(self.clear_btn)
        root.addLayout(footer)

        self.setCentralWidget(central)
        self.url_edit.setFocus()

    # Actions -----------------------------------------------------------------------------

    def start_from_input(self) -> None:
        text = self.url_edit.text()
        urls = extract_urls(text)
        if not urls:
            if text.strip():
                self.statusBar().showMessage("That doesn't look like a link (http:// or https://)",
                                             5000)
            return
        self.add_urls(urls)
        self.url_edit.clear()

    def add_urls(self, urls: list[str]) -> None:
        for url in urls:
            self._enqueue(url)

    def paste_into_input(self) -> None:
        self.url_edit.setText(QGuiApplication.clipboard().text().strip())
        self.url_edit.setFocus()

    def paste_and_download(self) -> None:
        urls = extract_urls(QGuiApplication.clipboard().text())
        if urls:
            self.add_urls(urls)
        else:
            self.statusBar().showMessage("No links found on the clipboard", 5000)

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder",
                                                  str(self.settings.output_dir))
        if folder:
            self.settings.output_dir = Path(folder)
            self._refresh_folder_label()

    def open_download_folder(self) -> None:
        folder = self.settings.output_dir
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def open_settings(self) -> None:
        dialog = SettingsDialog(self.settings, self)
        if dialog.exec():
            self.pool.setMaxThreadCount(self.settings.max_concurrent)
            self.preset_combo.setCurrentIndex(
                max(self.preset_combo.findData(self.settings.preset), 0))
            self._refresh_folder_label()

    def cancel_all(self) -> None:
        for item in self.items:
            item.cancel()

    def clear_finished(self) -> None:
        for item in [i for i in self.items if not i.state.is_active]:
            self._remove_item(item)

    def show_about(self) -> None:
        QMessageBox.about(
            self, f"About {APP_NAME}",
            f"<h3>{APP_NAME} {__version__}</h3>"
            "<p>Download video and audio from YouTube and hundreds of other sites.</p>"
            "<p><b>Credits</b><br>"
            "A <b>THE VOID</b> project by <b>THE VOID PROTOCOL</b><br>"
            "Owner of THE VOID: <b>MRVIMA</b> (alias <b>VOIDVIMA</b>)</p>"
            "<p>Powered by <a href='https://github.com/yt-dlp/yt-dlp'>yt-dlp</a> and Qt.<br>"
            "Released under the MIT License · "
            "<a href='https://github.com/MRVIMA/yt-downloader'>github.com/MRVIMA/yt-downloader</a></p>"
            "<p>Please respect copyright and each site's terms of service.</p>")

    # Queue management --------------------------------------------------------------------

    def _enqueue(self, url: str) -> None:
        options = self.settings.download_options()
        options.preset = self.preset_combo.currentData()
        options.playlist = self.playlist_cb.isChecked()
        item = DownloadItem(url, options)
        item.state_changed.connect(self._update_counts)
        item.retry_requested.connect(self._retry)
        item.remove_requested.connect(self._remove_item)
        self.items.append(item)
        self.queue_layout.insertWidget(self.queue_layout.count() - 1, item)
        self.empty_label.hide()
        self.pool.start(item.create_worker())
        self._update_counts()
        log.info("Queued %s (%s)", url, options.preset)

    def _retry(self, item: DownloadItem) -> None:
        self.pool.start(item.create_worker())
        self._update_counts()

    def _remove_item(self, item: DownloadItem) -> None:
        if item.state.is_active:
            return
        self.items.remove(item)
        self.queue_layout.removeWidget(item)
        item.deleteLater()
        self.empty_label.setVisible(not self.items)
        self._update_counts()

    def _update_counts(self) -> None:
        counts = {s: 0 for s in State}
        for item in self.items:
            counts[item.state] += 1
        running = counts[State.FETCHING] + counts[State.DOWNLOADING] + counts[State.PROCESSING]
        parts = []
        if running:
            parts.append(f"{running} downloading")
        if counts[State.QUEUED]:
            parts.append(f"{counts[State.QUEUED]} queued")
        if counts[State.DONE]:
            parts.append(f"{counts[State.DONE]} completed")
        if counts[State.FAILED]:
            parts.append(f"{counts[State.FAILED]} failed")
        self.count_label.setText(" · ".join(parts) or "Ready")
        active = any(i.state.is_active for i in self.items)
        self.cancel_all_btn.setEnabled(active)
        self.clear_btn.setEnabled(any(not i.state.is_active for i in self.items))

    def _refresh_folder_label(self) -> None:
        folder = str(self.settings.output_dir)
        home = str(Path.home())
        self.folder_label.setText("~" + folder[len(home):] if folder.startswith(home) else folder)
        self.folder_label.setToolTip(folder)

    # Events ------------------------------------------------------------------------------

    def dragEnterEvent(self, event) -> None:  # noqa: N802
        mime = event.mimeData()
        if mime.hasUrls() or mime.hasText():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802
        mime = event.mimeData()
        text = "\n".join(u.toString() for u in mime.urls()) if mime.hasUrls() else mime.text()
        if urls := extract_urls(text):
            self.add_urls(urls)
            event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: N802
        active = [i for i in self.items if i.state.is_active]
        if active:
            answer = QMessageBox.question(
                self, "Downloads in progress",
                f"{len(active)} download(s) are still running. Cancel them and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.cancel_all()
            self.pool.clear()
            self.pool.waitForDone(10_000)
        self.settings.window_geometry = self.saveGeometry()
        self.settings.sync()
        event.accept()
