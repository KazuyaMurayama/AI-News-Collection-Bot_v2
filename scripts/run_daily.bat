@echo off
REM Windows用 手動実行スクリプト

cd /d "%~dp0\.."

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo AI News Bot v2 を実行中...
python -m src.main %*
