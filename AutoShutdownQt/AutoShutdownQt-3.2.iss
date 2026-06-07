#define MyAppName "定时关机助手"
#define MyAppVersion "3.2"
#define MyAppPublisher "tiandao"
#define MyAppExeName "定时关机助手.exe"

[Setup]
AppId={{4F62E2F8-0D3C-4CF1-9C32-7A2F3E8D3000}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=定时关机助手-3.2-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=app_icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加快捷方式："; Flags: unchecked
Name: "launchafterinstall"; Description: "安装后启动定时关机助手"; GroupDescription: "安装后操作："; Flags: unchecked

[Files]
Source: "..\dist\定时关机助手-3.2\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\定时关机助手"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载定时关机助手"; Filename: "{uninstallexe}"
Name: "{autodesktop}\定时关机助手"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "安装后启动定时关机助手"; Flags: nowait postinstall skipifsilent; Tasks: launchafterinstall
