@echo off
chcp 65001 > nul
title O'zbek Tili Ovozli Dataset Boti
echo ======================================================
echo    🎙 O'zbek tili Ovozli Dataset Yig'ish Telegram Boti
echo ======================================================
echo.

cd /d "%~dp0"

:: 1. Python tekshirish
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [XATO] Python topilmadi! Iltimos, Python o'rnating va PATH ga qo'shing.
    pause
    exit /b
)

:: 2. .env fayli mavjudligini tekshirish
if not exist .env (
    if exist .env.example (
        echo [.env] fayli topilmadi. .env.example dan nusxa olinmoqda...
        copy .env.example .env
        echo [DIQQAT] .env fayliga BOT_TOKEN ni kiriting va qaytadan ishga tushiring!
        notepad .env
        pause
        exit /b
    )
)

:: 3. FFmpeg tekshirish
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [OGOHLANTIRISH] FFmpeg topilmadi. Ovozni WAV formatga o'tkazishda muammo bo'lishi mumkin.
    echo FFmpeg o'rnatilganligini va PATH ga qo'shilganligini tekshiring.
    echo.
)

:: 4. Kerakli kutubxonalarni tekshirish / o'rnatish
echo [1/2] Kutubxonalar tekshirilmoqda...
python -c "import aiogram, aiosqlite, dotenv, aiofiles" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Kerakli kutubxonalar o'rnatilmoqda...
    pip install -r requirements.txt
)

:: 5. Botni ishga tushirish
echo [2/2] Bot ishga tushirilmoqda...
echo.
python main.py

echo.
echo Bot to'xtatildi.
pause
