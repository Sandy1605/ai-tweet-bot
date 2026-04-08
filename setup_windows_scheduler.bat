@echo off
REM ─────────────────────────────────────────────
REM AI Tweet Bot - Windows Task Scheduler Setup
REM Posts at Nordic-friendly times (CEST UTC+2)
REM 8:00 AM, 12:00 PM, 7:00 PM Nordic time
REM
REM Convert to YOUR local time (IST = UTC+5:30):
REM   8:00 AM Nordic  = 11:30 AM IST
REM   12:00 PM Nordic = 3:30 PM IST
REM   7:00 PM Nordic  = 10:30 PM IST
REM
REM Run this ONCE as Administrator
REM ─────────────────────────────────────────────

echo.
echo Setting up AI Tweet Bot for Nordic audience...
echo.
echo Schedule (Nordic CEST time):
echo   Morning   - 8:00 AM  Nordic = 11:30 AM India
echo   Afternoon - 12:00 PM Nordic = 3:30 PM  India  
echo   Evening   - 7:00 PM  Nordic = 10:30 PM India
echo.

SET SCRIPT_DIR=%~dp0
SET BOT_CMD=%SCRIPT_DIR%run_now.bat

REM Remove old tasks if they exist
schtasks /delete /tn "AI Tweet Bot - Morning" /f 2>nul
schtasks /delete /tn "AI Tweet Bot - Afternoon" /f 2>nul
schtasks /delete /tn "AI Tweet Bot - Evening" /f 2>nul

REM 8:00 AM Nordic = 11:30 AM IST
schtasks /create /tn "AI Tweet Bot - Morning" /tr "%BOT_CMD%" /sc daily /st 11:30 /f
echo Created: Morning tweet at 11:30 AM IST (8:00 AM Nordic)

REM 12:00 PM Nordic = 3:30 PM IST
schtasks /create /tn "AI Tweet Bot - Afternoon" /tr "%BOT_CMD%" /sc daily /st 15:30 /f
echo Created: Afternoon tweet at 3:30 PM IST (12:00 PM Nordic)

REM 7:00 PM Nordic = 10:30 PM IST
schtasks /create /tn "AI Tweet Bot - Evening" /tr "%BOT_CMD%" /sc daily /st 22:30 /f
echo Created: Evening tweet at 10:30 PM IST (7:00 PM Nordic)

echo.
echo ─────────────────────────────────────────────
echo Done! Bot will post 3x daily for Nordic audience.
echo To verify: Search "Task Scheduler" in Windows
echo            Look for "AI Tweet Bot" tasks
echo.
echo IMPORTANT: Keep your PC on at these times!
echo IMPORTANT: Ollama must be running (ollama serve)
echo ─────────────────────────────────────────────
echo.
pause
