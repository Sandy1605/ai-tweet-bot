@echo off
REM ─────────────────────────────────────────────
REM AI Tweet Bot - DRY RUN TEST (safe - won't post)
REM Double-click to test without posting anything
REM ─────────────────────────────────────────────

echo Starting AI Tweet Bot (DRY RUN - safe test mode)...
echo This will NOT post anything to Twitter.
echo.

REM Load .env file
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if not "%%a"=="" if not "%%a:~0,1%"=="#" set %%a=%%b
)

REM Run in dry-run mode
python src\tweet_bot.py --dry-run

pause
