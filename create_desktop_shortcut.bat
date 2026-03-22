@echo off
REM Create Desktop Shortcut for AI Employee Start All
echo Creating desktop shortcut...

set SCRIPT_DIR=%~dp0
set DESKTOP=%USERPROFILE%\Desktop

REM Create shortcut to start_all.bat
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP%\AI Employee - Start All.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%start_all.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.IconLocation = 'shell32.dll,13'; $Shortcut.Description = 'Start all AI Employee services'; $Shortcut.Save()"

if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Desktop shortcut created: %DESKTOP%\AI Employee - Start All.lnk
) else (
    echo [ERROR] Failed to create desktop shortcut
)

pause
