@echo off
echo ========================================
echo  Spotify Widget - Remove from Startup
echo ========================================
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP%\SpotifyWidget.lnk"

if exist "%SHORTCUT%" (
    echo Removing shortcut from Startup folder...
    del "%SHORTCUT%"
    
    if %errorlevel% equ 0 (
        echo.
        echo [SUCCESS] Shortcut removed successfully!
        echo.
        echo Spotify Widget will no longer launch on Windows startup.
    ) else (
        echo.
        echo [ERROR] Failed to remove shortcut.
    )
) else (
    echo [INFO] Shortcut not found in Startup folder.
    echo Spotify Widget is not configured to launch on startup.
)

echo.
echo ========================================
pause
