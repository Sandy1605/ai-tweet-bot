@echo off
REM ── AI Tweet Bot - Task Scheduler Runner ──
REM This file is called by Windows Task Scheduler

REM Go to the folder where tweet_bot.py lives
set PYTHONIOENCODING=utf-8
cd /d C:\Users\dell\OneDrive\Desktop\ai-tweet-bot\files

REM Start Ollama if not already running
tasklist /fi "imagename eq ollama.exe" 2>nul | find /i "ollama.exe" >nul
if errorlevel 1 (
    echo Starting Ollama...
    start /min "" ollama serve
    REM Wait 10 seconds for Ollama to fully load
    timeout /t 10 /nobreak >nul
)

REM Load .env variables line by line
for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    echo %%A | findstr /r "^#" >nul 2>&1
    if errorlevel 1 (
        if not "%%A"=="" if not "%%B"=="" set "%%A=%%B"
    )
)

REM Run the bot and save output to log
echo. >> cron.log
echo ===== %DATE% %TIME% ===== >> cron.log
python tweet_bot.py >> cron.log 2>&1

