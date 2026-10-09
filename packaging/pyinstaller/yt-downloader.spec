# PyInstaller spec shared by the Windows and Linux (AppImage) builds. Run from the repo root:
#   pyinstaller packaging/pyinstaller/yt-downloader.spec
# Windows → dist/YT Downloader/{YT Downloader.exe, yt-downloader-cli.exe}
# Linux   → dist/yt-downloader/{yt-downloader, yt-downloader-cli}

import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

WINDOWS = sys.platform == "win32"
ROOT = SPECPATH + "/../.."
WIN = ROOT + "/packaging/windows"

datas = [(ROOT + "/src/yt_downloader/resources", "yt_downloader/resources")]
datas += collect_data_files("yt_dlp_ejs")  # JavaScript challenge solvers used with deno
hiddenimports = collect_submodules("yt_dlp_ejs")

# Qt modules the app never uses; dropping them saves ~100 MB.
excludes = [
    "tkinter", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
    "PySide6.QtMultimedia", "PySide6.QtCharts", "PySide6.QtDataVisualization",
    "PySide6.QtPdf", "PySide6.QtBluetooth", "PySide6.QtSql", "PySide6.QtTest",
]

common = dict(pathex=[ROOT + "/src"], datas=datas, hiddenimports=hiddenimports,
              excludes=excludes, noarchive=False)
win_extras = dict(icon=WIN + "/yt-downloader.ico", version=WIN + "/version_info.txt") \
    if WINDOWS else {}

gui_a = Analysis([SPECPATH + "/launch_gui.py"], **common)
cli_a = Analysis([SPECPATH + "/launch_cli.py"], **common)

gui_exe = EXE(
    PYZ(gui_a.pure), gui_a.scripts, [], exclude_binaries=True,
    name="YT Downloader" if WINDOWS else "yt-downloader",
    console=False, upx=False, strip=not WINDOWS, **win_extras,
)
cli_exe = EXE(
    PYZ(cli_a.pure), cli_a.scripts, [], exclude_binaries=True,
    name="yt-downloader-cli", console=True, upx=False, strip=not WINDOWS, **win_extras,
)

coll = COLLECT(
    gui_exe, gui_a.binaries, gui_a.datas,
    cli_exe, cli_a.binaries, cli_a.datas,
    name="YT Downloader" if WINDOWS else "yt-downloader", upx=False, strip=not WINDOWS,
)
