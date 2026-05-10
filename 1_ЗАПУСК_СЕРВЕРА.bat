@echo off
title СтудПортфолио - Сервер
color 0A
echo.
echo  ================================
echo   СтудПортфолио - Запуск сервера
echo  ================================
echo.
cd /d "%~dp0backend"
echo  Устанавливаем зависимости...
python -m pip install fastapi uvicorn sqlalchemy passlib python-jose python-multipart aiofiles --quiet
python -m pip install bcrypt==4.0.1 --quiet --force-reinstall
echo.
echo  Сервер запускается на http://localhost:8000
echo  Не закрывайте это окно!
echo.
python -m uvicorn main:app --reload --port 8000
pause
