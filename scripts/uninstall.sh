#!/usr/bin/env bash
# Remove a YT Downloader install made by scripts/install.sh. Settings and downloads are kept.
set -euo pipefail

APP_ID="com.thevoid.YTDownloader"
SLUG="yt-downloader"
PREFIX="${PREFIX:-$HOME/.local}"
SHARE="$PREFIX/share"

rm -rf "$SHARE/$SLUG"
rm -f "$PREFIX/bin/yt-downloader" "$PREFIX/bin/yt-downloader-cli" \
      "$SHARE/applications/$APP_ID.desktop" \
      "$SHARE/metainfo/$APP_ID.metainfo.xml" \
      "$SHARE/icons/hicolor/scalable/apps/$APP_ID.svg" \
      "$SHARE"/icons/hicolor/*/apps/"$APP_ID".png \
      "$(xdg-user-dir DESKTOP 2>/dev/null || echo "$HOME/Desktop")/$APP_ID.desktop"

command -v update-desktop-database >/dev/null \
    && update-desktop-database -q "$SHARE/applications" 2>/dev/null || true
# Only refresh an existing icon cache; creating one in ~/.local can hide other apps' icons.
[ -f "$SHARE/icons/hicolor/icon-theme.cache" ] && command -v gtk-update-icon-cache >/dev/null \
    && gtk-update-icon-cache -q -t "$SHARE/icons/hicolor" 2>/dev/null || true

echo "YT Downloader removed from $PREFIX."
echo "Your settings are in ~/.config/$SLUG and logs in ~/.local/state/$SLUG — delete them if you like."
