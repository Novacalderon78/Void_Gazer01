@echo off
setlocal
cd /d "%~dp0"
set PYTHONDONTWRITEBYTECODE=1
set PYGAME_HIDE_SUPPORT_PROMPT=1

py -3.12 -B -c "import pygame" >nul 2>&1
if not errorlevel 1 (
    py -3.12 -B main.py %*
    goto done
)

python -B -c "import pygame" >nul 2>&1
if not errorlevel 1 (
    python -B main.py %*
    goto done
)

set "GAME_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%GAME_PYTHON%" (
    "%GAME_PYTHON%" -B -c "import pygame" >nul 2>&1
    if not errorlevel 1 (
        "%GAME_PYTHON%" -B main.py %*
        goto done
    )
)

echo Install Python 3.12, then run: python -m pip install pygame
echo See README.md for help.
pause
exit /b 1

:done
set "GAME_RESULT=%errorlevel%"
if not "%GAME_RESULT%"=="0" pause
exit /b %GAME_RESULT%
