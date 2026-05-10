@echo off
title СтудПортфолио - Сайт
color 0B
echo.
echo  ================================
echo   СтудПортфолио - Открытие сайта
echo  ================================
echo.
cd /d "%~dp0frontend"
echo  Запускаем сайт на http://localhost:3000
echo  Не закрывайте это окно!
echo.
start "" http://localhost:3000
python -m http.server 3000
pause
