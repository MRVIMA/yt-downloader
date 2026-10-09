#!/usr/bin/env bash
# Build THE-VOID-DOWNLOADER-<version>-x86_64.AppImage (with ffmpeg and deno bundled).
#
#   ./packaging/appimage/build-appimage.sh
#
# For an AppImage that runs on most distros, build on an OLD base system (the GitHub workflow
# uses Ubuntu 22.04): an AppImage only runs where glibc is at least as new as the build host's.
#
# Environment:
#   USE_SYSTEM_PYSIDE=1   reuse the distro's PySide6 instead of downloading it (local tests only)
#   SKIP_TOOLS=1          don't bundle ffmpeg/deno (the app then uses the system's)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
APP_ID="com.thevoid.YTDownloader"
VERSION="$(python3 -c "import re;print(re.search(r'__version__ = \"(.+?)\"', open('src/yt_downloader/__init__.py').read())[1])")"
ARCH="x86_64"
BUILD="$ROOT/build/appimage"
APPDIR="$BUILD/AppDir"
OUT="$ROOT/dist/THE-VOID-DOWNLOADER-$VERSION-$ARCH.AppImage"
UPDATE_INFO="gh-releases-zsync|MRVIMA|yt-downloader|latest|THE-VOID-DOWNLOADER-*-$ARCH.AppImage.zsync"

step() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
fetch() { curl -fL --retry 3 --progress-bar -o "$2" "$1"; }

mkdir -p "$BUILD/tools" "$ROOT/dist"

step "Python environment"
venv_args=()
[ "${USE_SYSTEM_PYSIDE:-0}" = 1 ] && venv_args+=(--system-site-packages)
python3 -m venv "${venv_args[@]}" "$BUILD/venv"
"$BUILD/venv/bin/python" -m pip install -q --upgrade pip
"$BUILD/venv/bin/python" -m pip install -q "$ROOT" pyinstaller

step "PyInstaller"
"$BUILD/venv/bin/pyinstaller" --noconfirm --clean --log-level WARN \
    --distpath "$BUILD/dist" --workpath "$BUILD/work" packaging/pyinstaller/yt-downloader.spec

step "AppDir"
rm -rf "$APPDIR"
LIB="$APPDIR/usr/lib/yt-downloader"
mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" \
         "$APPDIR/usr/share/metainfo" "$APPDIR/usr/share/icons/hicolor/scalable/apps"
cp -a "$BUILD/dist/yt-downloader" "$LIB"
ln -s ../lib/yt-downloader/yt-downloader "$APPDIR/usr/bin/yt-downloader"
ln -s ../lib/yt-downloader/yt-downloader-cli "$APPDIR/usr/bin/yt-downloader-cli"
install -m755 packaging/appimage/AppRun "$APPDIR/AppRun"
install -m644 "data/$APP_ID.desktop" "$APPDIR/$APP_ID.desktop"
install -m644 "data/$APP_ID.desktop" "$APPDIR/usr/share/applications/"
install -m644 "data/$APP_ID.metainfo.xml" "$APPDIR/usr/share/metainfo/$APP_ID.appdata.xml"
install -m644 "src/yt_downloader/resources/$APP_ID.svg" "$APPDIR/$APP_ID.svg"
install -m644 "src/yt_downloader/resources/$APP_ID.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp -r data/icons/hicolor "$APPDIR/usr/share/icons/"
# .DirIcon should be a PNG (file managers and AppImage tools use it as the file's icon).
install -m644 "data/icons/hicolor/256x256/apps/$APP_ID.png" "$APPDIR/.DirIcon"
install -m644 LICENSE "$LIB/LICENSE"

if [ "${SKIP_TOOLS:-0}" != 1 ]; then
    step "Bundling ffmpeg + deno"
    # Static ffmpeg build: no shared-library dependencies, runs on any distro.
    [ -f "$BUILD/tools/ffmpeg.tar.xz" ] || \
        fetch https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz "$BUILD/tools/ffmpeg.tar.xz"
    [ -f "$BUILD/tools/deno.zip" ] || \
        fetch https://github.com/denoland/deno/releases/latest/download/deno-x86_64-unknown-linux-gnu.zip "$BUILD/tools/deno.zip"
    mkdir -p "$LIB/bin" "$BUILD/tools/ffmpeg"
    tar -xJf "$BUILD/tools/ffmpeg.tar.xz" -C "$BUILD/tools/ffmpeg" --strip-components=1
    install -m755 "$BUILD/tools/ffmpeg/ffmpeg" "$BUILD/tools/ffmpeg/ffprobe" "$LIB/bin/"
    install -m644 "$BUILD/tools/ffmpeg/GPLv3.txt" "$LIB/bin/FFMPEG-LICENSE.txt"
    unzip -oq "$BUILD/tools/deno.zip" -d "$LIB/bin"
fi

step "appimagetool"
TOOL="$BUILD/tools/appimagetool"
[ -x "$TOOL" ] || { fetch "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage" "$TOOL"; chmod +x "$TOOL"; }
# --appimage-extract-and-run: works without FUSE (containers, CI).
ARCH=$ARCH "$TOOL" --appimage-extract-and-run --no-appstream -u "$UPDATE_INFO" "$APPDIR" "$OUT"
[ -f "$OUT.zsync" ] || mv -f "$(basename "$OUT").zsync" "$OUT.zsync" 2>/dev/null || true

step "Done"
ls -lh "$OUT"*
