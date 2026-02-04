@echo off
echo ========================================
echo  Spotify Widget - Add to Startup
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXE_PATH=%SCRIPT_DIR%SpotifyWidget.exe"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

if not exist "%EXE_PATH%" (
    echo [ERROR] SpotifyWidget.exe not found!
    echo Please make sure SpotifyWidget.exe is in the same folder.
    echo.
    pause
    exit /b 1
)

echo Creating shortcut in Startup folder...
echo.

powershell "$s=(New-Object -COM WScript.Shell).CreateShortcut('%STARTUP%\SpotifyWidget.lnk');$s.TargetPath='%EXE_PATH%';$s.Save()"

if %errorlevel% equ 0 (
    echo [SUCCESS] Shortcut created successfully!
    echo.
    echo Spotify Widget will now launch on Windows startup.
    echo Location: %STARTUP%\SpotifyWidget.lnk
) else (
    echo [ERROR] Failed to create shortcut.
)

echo.
echo ========================================
pause
