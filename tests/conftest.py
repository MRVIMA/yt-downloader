import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture
def qapp():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app


@pytest.fixture
def settings(tmp_path, qapp):
    from PySide6.QtCore import QSettings

    from yt_downloader.gui.settings import AppSettings

    qs = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    s = AppSettings(qs)
    s.output_dir = tmp_path / "downloads"
    return s
