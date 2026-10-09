# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.0.0] — 2026-10-09

### Added
- **Linux AppImage:** one file for any distro (glibc 2.35+), with ffmpeg and Deno included, a built-in CLI (`… cli`), and in-place updates via zsync.
- **Windows app:** installer (`Setup.exe`, per-user or all users, optional desktop icon) and a portable zip, both with ffmpeg and Deno included. Built by GitHub Actions.
- **Android app** (Android 8+): native Kotlin/Compose app with Share → Download, background downloads with notifications, cancel and retry, saving to `Download/YT Downloader`, in-app yt-dlp updates, and THE VOID dark theme.
- Qt 6 desktop app with a download queue, per-item progress, speed and ETA.
- Quality presets: best, 4K, 1440p, 1080p, 720p, 480p, 360p, MP3, M4A, Opus.
- Whole-playlist downloads into numbered files.
- Embedded metadata, chapters, thumbnails and subtitles (via ffmpeg).
- Browser cookie support for age-restricted and members-only videos.
- Drag-and-drop and clipboard links; URLs can be passed on the command line.
- Preferences dialog; settings in `~/.config/yt-downloader/`, logs in `~/.local/state/yt-downloader/`.
- `yt-downloader-cli` command-line interface.
- Install script (`--desktop-shortcut` option), desktop entry, AppStream metadata, and app icons as SVG plus PNGs from 16 to 512 px.
- Arch Linux AUR package (`yt-downloader`) with a one-command publish script.
- Signed Android APKs (one per CPU type plus universal), with SHA-256 checksums published for every release.
- A clear error message when a video needs ffmpeg but it isn't installed.
- GitHub Actions: tests on every push, plus automatic Linux, Windows and Android builds for each release tag.
