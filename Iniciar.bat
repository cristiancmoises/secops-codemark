@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  python codemark.pyz gui
) else (
  py -3 codemark.pyz gui
)
if errorlevel 1 pause
