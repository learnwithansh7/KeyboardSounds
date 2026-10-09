@echo off
echo Stopping Keyboard Sounds background process...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*klack_clone.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Done.
pause
