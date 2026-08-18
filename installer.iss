[Setup]
AppName=OpenDataLoader PDF Pro
AppVersion=2.1
DefaultDirName={autopf}\OpenDataLoader
DefaultGroupName=OpenDataLoader
OutputDir=.
OutputBaseFilename=OpenDataLoader_Setup_V2.1
Compression=lzma2/ultra
SolidCompression=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\OpenDataLoader_PDF_V2.1.exe

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\OpenDataLoader_PDF_V2.1\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\OpenDataLoader PDF Pro"; Filename: "{app}\OpenDataLoader_PDF_V2.1.exe"; IconFilename: "{app}\logo.ico"
Name: "{group}\{cm:UninstallProgram,OpenDataLoader PDF Pro}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OpenDataLoader PDF Pro"; Filename: "{app}\OpenDataLoader_PDF_V2.1.exe"; Tasks: desktopicon; IconFilename: "{app}\logo.ico"

[Run]
Filename: "{app}\OpenDataLoader_PDF_V2.1.exe"; Description: "{cm:LaunchProgram,OpenDataLoader PDF Pro}"; Flags: nowait postinstall skipifsilent
