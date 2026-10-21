@echo off
chcp 65001 > nul
title GitHub'ga Yuklash (Push to GitHub)
echo ==============================================================
echo    🚀 GitHub'ga Loyihani Yuklash (MrLutfulla/Dataset)
echo ==============================================================
echo.
echo Hozir GitHub tizimiga kirish oynasi (brauzer) ochiladi.
echo Akkauntingizga kiring va "Authorize" tugmasini bosing.
echo.

cd /d "%~dp0"
set GIT_PATH=C:\Users\murod\PortableGit\bin\git.exe

if not exist "%GIT_PATH%" (
    set GIT_PATH=git
)

"%GIT_PATH%" push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ==============================================================
    echo    ✅ MUVAFFAQIYATLI YUKLANDI!
    echo    Havola: https://github.com/MrLutfulla/Dataset
    echo ==============================================================
) else (
    echo.
    echo [DIQQAT] Agar brauzer ochilmasa, GitHub Personal Access Token (PAT) kerak bo'ladi.
)

echo.
pause
