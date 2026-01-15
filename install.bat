@echo off
echo Serial Monitor - Setup
echo.
python --version 2>nul
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Installa Python da https://python.org
    pause
    exit /b 1
)
echo Installazione pyserial...
pip install pyserial
echo.
echo Installazione completata!
pause
