@echo off
echo Building PatientDisplay.exe ...

C:\Users\HugoMarques\anaconda3\envs\patient-display\Scripts\pyinstaller.exe ^
    --onefile ^
    --windowed ^
    --name PatientDisplay ^
    --collect-all PIL ^
    main.py

echo.
echo Done!  Find PatientDisplay.exe in the dist\ folder.
echo Copy only PatientDisplay.exe to the hospital computer.
echo config.json will be created next to the exe after first Setup.
pause
