import gc
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    QtWidgets = pytest.importorskip("PySide6.QtWidgets")
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    yield app
    _delete_widgets(app)


@pytest.fixture(autouse=True)
def _cleanup_widgets(request):
    """Delete every window a test created, so Qt never tears them down at interpreter exit.

    Without this, pip's PySide6 can segfault while shutting down after the tests have passed.
    """
    yield
    if "qapp" in request.fixturenames:
        _delete_widgets(request.getfixturevalue("qapp"))


def _delete_widgets(app):
    from PySide6.QtCore import QCoreApplication, QEvent

    for widget in app.topLevelWidgets():
        widget.close()
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()
    gc.collect()


@pytest.fixture
def settings(tmp_path, qapp):
    from PySide6.QtCore import QSettings

    from yt_downloader.gui.settings import AppSettings

    qs = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    s = AppSettings(qs)
    s.output_dir = tmp_path / "downloads"
    return s
