#!/usr/bin/env bash
# Install YT Downloader for the current user (default) or system-wide.
#
#   ./scripts/install.sh                 # → ~/.local
#   sudo PREFIX=/usr/local ./scripts/install.sh
#   ./scripts/install.sh --desktop-shortcut   # also put a launcher icon on the desktop
#
# Re-running the script upgrades an existing install (and pulls the latest yt-dlp).
set -euo pipefail

APP_ID="com.thevoid.YTDownloader"
SLUG="yt-downloader"
PREFIX="${PREFIX:-$HOME/.local}"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PREFIX/share/$SLUG"
VENV="$APP_DIR/venv"
BIN_DIR="$PREFIX/bin"
SHARE="$PREFIX/share"

bold() { printf '\033[1m%s\033[0m\n' "$*"; }
warn() { printf '\033[33mwarning:\033[0m %s\n' "$*" >&2; }
die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

DESKTOP_SHORTCUT=0
for arg in "$@"; do
    case "$arg" in
        --desktop-shortcut) DESKTOP_SHORTCUT=1 ;;
        -h|--help) sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) die "unknown option: $arg (try --help)" ;;
    esac
done

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null || die "python3 is required"
"$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
    || die "Python 3.10 or newer is required (found $("$PYTHON" --version))"
"$PYTHON" -c 'import venv, ensurepip' 2>/dev/null \
    || die "the Python venv module is missing (Debian/Ubuntu: sudo apt install python3-venv)"

command -v ffmpeg >/dev/null || warn "ffmpeg not found — install it for HD video, audio conversion and embedding"
command -v deno >/dev/null || warn "deno not found — install it for full YouTube support (see README)"

bold "Installing YT Downloader to $PREFIX"

# Reuse the distro's PySide6 when present: saves a ~300 MB download and matches the system theme.
venv_args=()
if "$PYTHON" -c 'import PySide6' 2>/dev/null; then
    venv_args+=(--system-site-packages)
    echo "→ using system PySide6"
fi

rm -rf "$VENV"
mkdir -p "$APP_DIR" "$BIN_DIR"
"$PYTHON" -m venv "${venv_args[@]}" "$VENV"
"$VENV/bin/python" -m pip install --quiet --upgrade pip
echo "→ installing Python packages (this can take a minute)"
"$VENV/bin/python" -m pip install --quiet --upgrade "$SRC_DIR"

ln -sf "$VENV/bin/yt-downloader" "$BIN_DIR/yt-downloader"
ln -sf "$VENV/bin/yt-downloader-cli" "$BIN_DIR/yt-downloader-cli"

# Desktop integration. Exec gets an absolute path so launchers work even if ~/.local/bin
# isn't on the session PATH.
install -d "$SHARE/applications" "$SHARE/metainfo" "$SHARE/icons/hicolor/scalable/apps"
sed "s|^Exec=yt-downloader|Exec=$BIN_DIR/yt-downloader|" \
    "$SRC_DIR/data/$APP_ID.desktop" > "$SHARE/applications/$APP_ID.desktop"
chmod 644 "$SHARE/applications/$APP_ID.desktop"
install -m644 "$SRC_DIR/data/$APP_ID.metainfo.xml" "$SHARE/metainfo/"
install -m644 "$SRC_DIR/src/yt_downloader/resources/$APP_ID.svg" \
    "$SHARE/icons/hicolor/scalable/apps/"
# Sized PNGs too: some launchers/taskbars ignore SVG-only icons.
for png in "$SRC_DIR"/data/icons/hicolor/*/apps/"$APP_ID".png; do
    size_dir="$(basename "$(dirname "$(dirname "$png")")")"
    install -Dm644 "$png" "$SHARE/icons/hicolor/$size_dir/apps/$APP_ID.png"
done

command -v update-desktop-database >/dev/null \
    && update-desktop-database -q "$SHARE/applications" 2>/dev/null || true
# Only refresh an existing icon cache; creating one in ~/.local can hide other apps' icons.
[ -f "$SHARE/icons/hicolor/icon-theme.cache" ] && command -v gtk-update-icon-cache >/dev/null \
    && gtk-update-icon-cache -q -t "$SHARE/icons/hicolor" 2>/dev/null || true
# KDE: full rebuild so Plasma picks up the entry and icon immediately.
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1 || true

if [ "$DESKTOP_SHORTCUT" = 1 ]; then
    desktop_dir="$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")"
    mkdir -p "$desktop_dir"
    shortcut="$desktop_dir/$APP_ID.desktop"
    install -m755 "$SHARE/applications/$APP_ID.desktop" "$shortcut"  # executable = trusted on KDE
    command -v gio >/dev/null && gio set "$shortcut" metadata::trusted true 2>/dev/null || true
    echo "→ added launcher icon to $desktop_dir"
fi

bold "Done!"
echo "Launch \"YT Downloader\" from your app menu, or run: yt-downloader"
case ":$PATH:" in
    *":$BIN_DIR:"*) ;;
    *) warn "$BIN_DIR is not on your PATH — add it to use the commands from a terminal" ;;
esac
