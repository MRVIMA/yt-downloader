; Inno Setup script for YT Downloader. Build after PyInstaller:
;   iscc /DAppVersion=1.0.0 packaging\windows\installer.iss
; Output: dist\YT-Downloader-<version>-Setup.exe

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "YT Downloader"
#define AppExe "YT Downloader.exe"
#define Publisher "THE VOID PROTOCOL"
#define AppURL "https://github.com/MRVIMA/yt-downloader"

[Setup]
AppId={{6F1C2D7E-4B8A-4C55-9E2F-5A7D3B9C0E41}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#Publisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
LicenseFile=..\..\LICENSE
SetupIconFile=yt-downloader.ico
UninstallDisplayIcon={app}\{#AppExe}
OutputDir=..\..\dist
OutputBaseFilename=YT-Downloader-{#AppVersion}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\..\dist\YT Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
