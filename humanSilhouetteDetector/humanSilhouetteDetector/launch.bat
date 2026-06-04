@echo off
cd /d "%~dp0dist\HumanSilhouetteDetector"
start "" http://localhost:5000
HumanSilhouetteDetector.exe
