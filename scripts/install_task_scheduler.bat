@echo off
REM Windowsタスクスケジューラ設定

set PROJECT_DIR=%~dp0..
set PYTHON_PATH=%PROJECT_DIR%\venv\Scripts\python.exe
set TASK_NAME=AI-News-Bot-v2

echo タスクスケジューラに登録中...

schtasks /create /tn "%TASK_NAME%" /tr "\"%PYTHON_PATH%\" -m src.main" /sc daily /st 06:00 /sd %date% /f /rl highest

if %errorlevel% equ 0 (
    echo タスク "%TASK_NAME%" を登録しました
    echo スケジュール: 毎日 06:00
) else (
    echo エラー: タスクの登録に失敗しました
    echo 管理者権限で実行してください
)
pause
