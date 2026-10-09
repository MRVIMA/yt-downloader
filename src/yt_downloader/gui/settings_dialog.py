"""Preferences dialog."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from yt_downloader.core.options import COOKIE_BROWSERS, DEFAULT_TEMPLATE
from yt_downloader.core.presets import PRESETS
from yt_downloader.core.utils import default_download_dir
from yt_downloader.gui.settings import MAX_CONCURRENT_LIMIT, AppSettings

CONTAINER_LABELS = {"auto": "Automatic (best quality)", "mp4": "MP4 (most compatible)",
                    "mkv": "MKV"}


class SettingsDialog(QDialog):
    def __init__(self, settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(520)

        # Downloads
        self.folder_edit = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_edit, 1)
        folder_row.addWidget(browse)

        self.preset_combo = QComboBox()
        for p in PRESETS:
            self.preset_combo.addItem(p.label, p.key)

        self.container_combo = QComboBox()
        for key, label in CONTAINER_LABELS.items():
            self.container_combo.addItem(label, key)

        self.template_edit = QLineEdit()
        self.template_edit.setPlaceholderText(DEFAULT_TEMPLATE)
        self.template_edit.setToolTip(
            "yt-dlp output template, e.g. %(uploader)s/%(title)s.%(ext)s\n"
            "See https://github.com/yt-dlp/yt-dlp#output-template")

        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, MAX_CONCURRENT_LIMIT)

        downloads = QGroupBox("Downloads")
        form = QFormLayout(downloads)
        form.addRow("Save to:", folder_row)
        form.addRow("Default quality:", self.preset_combo)
        form.addRow("Video container:", self.container_combo)
        form.addRow("File name:", self.template_edit)
        form.addRow("Simultaneous downloads:", self.concurrent_spin)

        # Post-processing
        self.metadata_cb = QCheckBox("Embed title, artist and chapters")
        self.thumbnail_cb = QCheckBox("Embed thumbnail as cover art")
        self.subs_cb = QCheckBox("Embed subtitles (video only)")
        self.subs_edit = QLineEdit()
        self.subs_edit.setPlaceholderText("en, de, fr")
        self.subs_cb.toggled.connect(self.subs_edit.setEnabled)

        processing = QGroupBox("Post-processing (requires ffmpeg)")
        pform = QFormLayout(processing)
        pform.addRow(self.metadata_cb)
        pform.addRow(self.thumbnail_cb)
        pform.addRow(self.subs_cb)
        pform.addRow("Subtitle languages:", self.subs_edit)

        # Network
        self.cookies_combo = QComboBox()
        self.cookies_combo.addItem("Don't use browser cookies", "")
        for browser in COOKIE_BROWSERS:
            self.cookies_combo.addItem(browser.capitalize(), browser)
        self.cookies_combo.setToolTip(
            "Use your browser's login session for age-restricted or members-only videos,\n"
            "or when YouTube asks you to confirm you're not a bot.")

        network = QGroupBox("Account")
        nform = QFormLayout(network)
        nform.addRow("Cookies from:", self.cookies_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.RestoreDefaults)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(
            self._restore_defaults)

        layout = QVBoxLayout(self)
        layout.addWidget(downloads)
        layout.addWidget(processing)
        layout.addWidget(network)
        layout.addWidget(buttons)

        self._load()

    def _load(self) -> None:
        s = self.settings
        self.folder_edit.setText(str(s.output_dir))
        self._select(self.preset_combo, s.preset)
        self._select(self.container_combo, s.container)
        template = s.filename_template
        self.template_edit.setText("" if template == DEFAULT_TEMPLATE else template)
        self.concurrent_spin.setValue(s.max_concurrent)
        self.metadata_cb.setChecked(s.embed_metadata)
        self.thumbnail_cb.setChecked(s.embed_thumbnail)
        self.subs_cb.setChecked(s.embed_subtitles)
        self.subs_edit.setText(s.subtitle_langs)
        self.subs_edit.setEnabled(s.embed_subtitles)
        self._select(self.cookies_combo, s.cookies_from_browser)

    def _restore_defaults(self) -> None:
        self.folder_edit.setText(str(default_download_dir()))
        self._select(self.preset_combo, "best")
        self._select(self.container_combo, "auto")
        self.template_edit.clear()
        self.concurrent_spin.setValue(2)
        self.metadata_cb.setChecked(True)
        self.thumbnail_cb.setChecked(True)
        self.subs_cb.setChecked(False)
        self.subs_edit.setText("en")
        self._select(self.cookies_combo, "")

    def accept(self) -> None:
        s = self.settings
        folder = self.folder_edit.text().strip()
        s.output_dir = Path(folder).expanduser() if folder else default_download_dir()
        s.preset = self.preset_combo.currentData()
        s.container = self.container_combo.currentData()
        s.filename_template = self.template_edit.text().strip() or DEFAULT_TEMPLATE
        s.max_concurrent = self.concurrent_spin.value()
        s.embed_metadata = self.metadata_cb.isChecked()
        s.embed_thumbnail = self.thumbnail_cb.isChecked()
        s.embed_subtitles = self.subs_cb.isChecked()
        s.subtitle_langs = self.subs_edit.text().strip() or "en"
        s.cookies_from_browser = self.cookies_combo.currentData()
        s.sync()
        super().accept()

    def _browse(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose download folder",
                                                  self.folder_edit.text())
        if folder:
            self.folder_edit.setText(folder)

    @staticmethod
    def _select(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(max(index, 0))
