@echo off
setlocal
set "ROOT=%~dp0"
python "%ROOT%scripts\loop_cli.py" %*
