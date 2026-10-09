# Contributing

Thanks for helping out! Bug reports, ideas and pull requests are all welcome.

## Development setup

```bash
git clone https://github.com/MRVIMA/yt-downloader.git
cd yt-downloader
make venv      # creates .venv and installs the app in editable mode with dev tools
make run       # launches the GUI with debug logging
```

For the Android app, see [`android/README.md`](android/README.md).

## Before opening a pull request

```bash
make lint      # ruff
make test      # pytest (runs headless)
```

- Keep `core/` free of Qt imports — it is shared by the CLI and GUI.
- Add or update tests for behaviour changes.
- Add a line under an `Unreleased` heading in `CHANGELOG.md`.

## Releasing

1. Bump the version everywhere:
   - `__version__` in `src/yt_downloader/__init__.py` (the Windows build reads it from here)
   - `pkgver` in `packaging/arch/PKGBUILD`
   - a new `<release>` entry in `data/com.thevoid.YTDownloader.metainfo.xml`
   - `versionName` and `versionCode` (+1) in `android/app/build.gradle.kts`
2. Update `CHANGELOG.md`, and write `docs/release-notes/vX.Y.Z.md`, which becomes the text of the GitHub release page.
3. Tag and push: `git tag v1.2.3 && git push --tags`. GitHub Actions then attaches everything to
   the release: the Python wheel and sdist, the Linux AppImage, the Windows installer and portable zip, and the Android APKs.
