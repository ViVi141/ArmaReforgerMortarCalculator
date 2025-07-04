@echo off
echo ==================================================
echo      Arma Reforger Mortar Calculator Build
echo ==================================================

echo.
echo [1/4] Killing any existing application process...
taskkill /F /IM "Arma Reforger Mortar Calculator.exe" /T > nul 2>&1
echo     Done.

echo.
echo [2/4] Cleaning up old build artifacts...
if exist "dist" (
    echo     - Deleting 'dist' directory...
    rmdir /s /q "dist"
)
if exist "build" (
    echo     - Deleting 'build' directory...
    rmdir /s /q "build"
)
if exist "Arma Reforger Mortar Calculator.spec" (
    echo     - Deleting '.spec' file...
    del "Arma Reforger Mortar Calculator.spec"
)
echo     Done.

echo.
echo [3/4] Running PyInstaller to build the executable...
pyinstaller --onefile --windowed --icon=mortar_icon.ico --add-data "maps;maps" --add-data "maps_config.json;." --add-data "theme_config.json;." main.py --name "Arma Reforger Mortar Calculator"

echo.
echo [4/4] Build process finished.
echo The new executable is located in the 'dist' folder.
echo ==================================================
pause