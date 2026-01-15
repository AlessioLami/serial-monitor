@echo off
cd /d "%~dp0"
python -c "import serial" 2>nul
if errorlevel 1 (
    echo Installazione pyserial...
    pip install pyserial
)
start "" pythonw serial_monitor.pyw
exit
