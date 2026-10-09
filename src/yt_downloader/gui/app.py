"""GUI entry point: ``yt-downloader``."""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from yt_downloader import APP_ID, APP_NAME, APP_SLUG, __version__
from yt_downloader.core.utils import extract_urls, state_dir, use_bundled_tools


def _setup_logging(debug: bool) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        log_dir = state_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(log_dir / f"{APP_SLUG}.log", maxBytes=1_000_000,
                                            backupCount=3, encoding="utf-8"))
    except OSError:
        pass
    handlers[0].setLevel(logging.DEBUG if debug else logging.WARNING)
    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO, handlers=handlers,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    parser = argparse.ArgumentParser(prog=APP_SLUG, description=f"{APP_NAME} desktop app")
    parser.add_argument("urls", nargs="*", metavar="URL", help="URLs to start downloading")
    parser.add_argument("--debug", action="store_true", help="verbose logging to the terminal")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args, qt_args = parser.parse_known_args(argv[1:])

    _setup_logging(args.debug)
    use_bundled_tools()

    # Import Qt only after argument parsing so --help/--version work without a display.
    from PySide6.QtWidgets import QApplication

    from yt_downloader.gui.icons import app_icon
    from yt_downloader.gui.main_window import MainWindow

    QApplication.setApplicationName(APP_SLUG)
    QApplication.setApplicationDisplayName(APP_NAME)
    QApplication.setApplicationVersion(__version__)
    QApplication.setDesktopFileName(APP_ID)  # Wayland app_id → correct taskbar icon

    app = QApplication([argv[0], *qt_args])
    app.setWindowIcon(app_icon())

    window = MainWindow()
    window.show()
    if urls := extract_urls(" ".join(args.urls)):
        window.add_urls(urls)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
