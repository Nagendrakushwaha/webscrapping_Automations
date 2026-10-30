@echo off
title AI LEAD INTELLIGENCE - Tex Web Solutions
color 0b
echo ==============================================================
echo           AI LEAD INTELLIGENCE SYSTEM
echo           Tex Web Solutions Pvt. Ltd.
echo ==============================================================
echo.
echo Checking Python 3.13 Virtual Environment...

if exist ".\venv\Scripts\python.exe" (
    set PYTHON_EXE=.\venv\Scripts\python.exe
) else (
    set PYTHON_EXE="C:\Users\HP\AppData\Local\Programs\Python\Python313\python.exe"
)

echo Starting Backend Server on http://localhost:8000 ...
start "" http://localhost:8000
%PYTHON_EXE% -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
