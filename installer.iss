[Setup]
AppName=LexGuard
AppVersion=2.2
DefaultDirName={autopf}\LexGuard
DefaultGroupName=LexGuard
OutputDir=.
OutputBaseFilename=LexGuard_Setup_V2.2
Compression=lzma2/ultra
SolidCompression=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\LexGuard.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\LexGuard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LexGuard"; Filename: "{app}\LexGuard.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\{cm:UninstallProgram,LexGuard}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\LexGuard"; Filename: "{app}\LexGuard.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\LexGuard.exe"; Description: "{cm:LaunchProgram,LexGuard}"; Flags: nowait postinstall skipifsilent
