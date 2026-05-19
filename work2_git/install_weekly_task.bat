@echo off
schtasks /Create /TN "YouTube Pet Product Scout" /TR "powershell -ExecutionPolicy Bypass -File D:\codex\work2\run_youtube_report.ps1" /SC WEEKLY /D FRI /ST 17:00 /F
echo.
echo If you see SUCCESS, the weekly task is installed.
echo It will run every Friday at 17:00.
pause
