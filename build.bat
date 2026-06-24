@echo off
echo ============================================================
echo  AIR POINTER — Build Script
echo ============================================================

echo Activating virtual environment...
call venv\Scripts\activate

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo Building executable...
pyinstaller air_pointer.spec --clean --noconfirm

echo.
if exist dist\AirPointer\AirPointer.exe (
    echo ============================================================
    echo  BUILD SUCCESSFUL!
    echo  Location: dist\AirPointer\AirPointer.exe
    echo ============================================================
) else (
    echo ============================================================
    echo  BUILD FAILED. Check errors above.
    echo ============================================================
)

pause