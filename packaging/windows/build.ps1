# Build the Windows app, portable zip and installer.
# Run from the repository root in PowerShell:  .\packaging\windows\build.ps1
# Needs: Python 3.10+ on PATH, Inno Setup 6 (iscc) for the installer step.
$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

python -m pip install --upgrade pip
python -m pip install . pyinstaller
$version = python packaging/windows/make_version_info.py

pyinstaller --noconfirm --clean packaging/pyinstaller/yt-downloader.spec

# Bundle ffmpeg + deno in a bin\ folder next to the exe (found via use_bundled_tools()).
$bin = "dist\THE VOID DOWNLOADER\bin"
New-Item -ItemType Directory -Force -Path $bin, build\tools | Out-Null
Invoke-WebRequest "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile build\tools\ffmpeg.zip
Expand-Archive build\tools\ffmpeg.zip build\tools\ffmpeg -Force
Get-ChildItem build\tools\ffmpeg -Recurse -Include ffmpeg.exe, ffprobe.exe | Copy-Item -Destination $bin
Get-ChildItem build\tools\ffmpeg -Recurse -Filter LICENSE | Select-Object -First 1 | Copy-Item -Destination "$bin\FFMPEG-LICENSE.txt"
Invoke-WebRequest "https://github.com/denoland/deno/releases/latest/download/deno-x86_64-pc-windows-msvc.zip" -OutFile build\tools\deno.zip
Expand-Archive build\tools\deno.zip $bin -Force

Copy-Item LICENSE "dist\THE VOID DOWNLOADER\LICENSE.txt"
Compress-Archive -Path "dist\THE VOID DOWNLOADER\*" -DestinationPath "dist\THE-VOID-DOWNLOADER-$version-Windows-Portable.zip" -Force

$iscc = (Get-Command iscc -ErrorAction SilentlyContinue).Source
if (-not $iscc) { $iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" }
& $iscc "/DAppVersion=$version" packaging\windows\installer.iss

Write-Host "Built dist\THE-VOID-DOWNLOADER-$version-Setup.exe and the portable zip."
