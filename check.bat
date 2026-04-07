@echo off
:: Drag and drop any image or video onto this file to check it
:: Or double-click to enter interactive mode

if "%~1"=="" (
    echo.
    echo   AI Detector - Drag and drop a file onto this icon to check it
    echo   Or enter a file path below:
    echo.
    set /p "filepath=  File path: "
    python "%~dp0cli.py" -v "%filepath%"
) else (
    python "%~dp0cli.py" -v %*
)

echo.
pause
