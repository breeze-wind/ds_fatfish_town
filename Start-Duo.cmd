@echo off
setlocal
cd /d "%~dp0"
set "PYTHONPATH=src"
set "PYTHONUTF8=1"
python -u -m cyber_habitat.duo %*
pause
