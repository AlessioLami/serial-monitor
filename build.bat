@echo off
echo Building Serial Monitor...
echo.

pip install pyinstaller pyserial >nul 2>&1

pyinstaller --onefile --windowed --name "SerialMonitor" --icon=icon.ico serial_monitor.pyw 2>nul
if not exist icon.ico (
    pyinstaller --onefile --windowed --name "SerialMonitor" serial_monitor.pyw
)

echo.
if exist "dist\SerialMonitor.exe" (
    echo Build completato!
    echo Trovi SerialMonitor.exe in: dist\SerialMonitor.exe
    explorer dist
) else (
    echo Build fallito.
)
pause
