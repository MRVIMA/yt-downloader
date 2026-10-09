#!/usr/bin/env bash
# Publish (or update) the "yt-downloader" package on the AUR.
#
# Before the first run:
#   1. The GitHub release tag must exist (e.g. v1.0.0 at github.com/MRVIMA/yt-downloader).
#   2. You need an AUR account with your SSH public key added (see packaging/arch/README.md).
#
# Usage:  ./packaging/arch/aur-publish.sh            # build-test, then push to the AUR
#         ./packaging/arch/aur-publish.sh --dry-run  # everything except the push
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

bold() { printf '\n\033[1m==> %s\033[0m\n' "$*"; }
die() { printf '\033[31merror:\033[0m %s\n' "$*" >&2; exit 1; }

# shellcheck disable=SC1091
source <(grep -E '^(pkgname|pkgver|pkgrel|url)=' PKGBUILD)
tarball_url="$url/archive/refs/tags/v$pkgver.tar.gz"

bold "Checking the GitHub release v$pkgver"
curl -fsIL "$tarball_url" >/dev/null \
    || die "$tarball_url not found. Push the repo and the v$pkgver tag to GitHub first."

bold "Updating the checksum"
sum=$(curl -fsSL "$tarball_url" | sha256sum | cut -d' ' -f1)
sed -i "s/^sha256sums=.*/sha256sums=('$sum')/" PKGBUILD
echo "sha256: $sum"

bold "Test build (makepkg)"
build_dir=$(mktemp -d)
cp PKGBUILD "$build_dir/"
(cd "$build_dir" && makepkg --syncdeps --cleanbuild --force --noconfirm) \
    || die "makepkg failed; nothing was published"
command -v namcap >/dev/null && namcap "$build_dir"/*.pkg.tar.zst || true
rm -rf "$build_dir"

makepkg --printsrcinfo > .SRCINFO

if [ "$DRY_RUN" = 1 ]; then
    bold "Dry run: PKGBUILD and .SRCINFO are ready, nothing was pushed"
    exit 0
fi

bold "Pushing to the AUR"
aur_dir=$(mktemp -d)
git clone "ssh://aur@aur.archlinux.org/$pkgname.git" "$aur_dir" \
    || die "Couldn't reach the AUR over SSH. Is your key added at https://aur.archlinux.org/account/?"
cp PKGBUILD .SRCINFO "$aur_dir/"
cd "$aur_dir"
git add PKGBUILD .SRCINFO
if git diff --cached --quiet; then
    echo "The AUR already has this version."
else
    git commit -m "Update to $pkgver-$pkgrel"
    git push origin HEAD:master
    bold "Published: https://aur.archlinux.org/packages/$pkgname"
fi
rm -rf "$aur_dir"
