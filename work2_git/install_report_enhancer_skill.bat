@echo off
set SRC=D:\codex\work2\skills\youtube-product-report-enhancer
set DST=%USERPROFILE%\.codex\skills\youtube-product-report-enhancer

if not exist "%USERPROFILE%\.codex\skills" mkdir "%USERPROFILE%\.codex\skills"
robocopy "%SRC%" "%DST%" /E

echo.
echo If robocopy reports files copied, the skill is installed.
echo Restart Codex or start a new thread for automatic skill discovery.
pause
