@echo off
REM ── Run this ONCE as Administrator to fix Task Scheduler ──

SET BOT_PATH=C:\Users\dell\OneDrive\Desktop\ai-tweet-bot\files\run_now.bat

echo Fixing Task Scheduler tasks...

REM Delete old broken tasks
schtasks /delete /tn "AI Tweet Bot - Morning"   /f 2>nul
schtasks /delete /tn "AI Tweet Bot - Afternoon" /f 2>nul
schtasks /delete /tn "AI Tweet Bot - Evening"   /f 2>nul

REM Recreate with correct path
REM IST times = Nordic CEST times
REM 11:30 AM IST = 8:00 AM CEST (morning)
REM 3:30 PM IST  = 12:00 PM CEST (lunch)
REM 10:30 PM IST = 7:00 PM CEST (evening)

schtasks /create /tn "AI Tweet Bot - Morning"   /tr "%BOT_PATH%" /sc daily /st 11:30 /f
schtasks /create /tn "AI Tweet Bot - Afternoon" /tr "%BOT_PATH%" /sc daily /st 15:30 /f
schtasks /create /tn "AI Tweet Bot - Evening"   /tr "%BOT_PATH%" /sc daily /st 22:30 /f

echo.
echo Done! Tasks recreated with correct paths.
echo.
echo Schedule (IST = Nordic CEST):
echo   11:30 AM IST = 8:00 AM Nordic
echo   3:30 PM IST  = 12:00 PM Nordic
echo   10:30 PM IST = 7:00 PM Nordic
echo.
pause
