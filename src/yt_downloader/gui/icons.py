"""Icon lookup: prefer the desktop theme (Breeze, Adwaita…), fall back to Qt's built-ins."""

from __future__ import annotations

from importlib.resources import files

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QStyle

from yt_downloader import APP_ID

_SP = QStyle.StandardPixmap
_FALLBACKS = {
    "process-stop": _SP.SP_BrowserStop,
    "view-refresh": _SP.SP_BrowserReload,
    "folder-open": _SP.SP_DirOpenIcon,
    "edit-delete": _SP.SP_TrashIcon,
    "edit-paste": _SP.SP_FileDialogContentsView,
    "document-open": _SP.SP_FileIcon,
    "dialog-warning": _SP.SP_MessageBoxWarning,
    "edit-clear-history": _SP.SP_DialogResetButton,
    "download": _SP.SP_ArrowDown,
}


def themed(name: str) -> QIcon:
    if QIcon.hasThemeIcon(name):
        return QIcon.fromTheme(name)
    fallback = _FALLBACKS.get(name)
    if fallback is not None:
        return QApplication.style().standardIcon(fallback)
    return QIcon()


def app_icon() -> QIcon:
    bundled = QIcon(str(files("yt_downloader") / "resources" / f"{APP_ID}.svg"))
    return QIcon.fromTheme(APP_ID, bundled)
