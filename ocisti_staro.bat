@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Bice obrisano iz foldera "%cd%":
echo.
echo   backend\snimci\                 stari probni snimci (oko 2.7 GB)
echo   backend\modeli\model_gen.pt, model_novi2.pt, model_veci.pt   stari modeli
echo   backend\klinicki_sloj.py, backend\model_utils.py             stari kod
echo   backend\__pycache__\
echo   frontend\src\Analiza.jsx, Karton.jsx, Pacijenti.jsx, index.css, assets\
echo   frontend\public\favicon.svg, icons.svg
echo   frontend\README.md, frontend\.oxlintrc.json
echo.
echo Prezentacije i seminarski rad (pptx, pdf) se NE diraju.
echo.
set /p ODGOVOR=Upisi DA za brisanje: 
if /i not "%ODGOVOR%"=="DA" (
  echo Nista nije obrisano.
  pause
  exit /b
)
if exist "backend\snimci" rmdir /s /q "backend\snimci"
if exist "backend\__pycache__" rmdir /s /q "backend\__pycache__"
for %%F in (model_gen.pt model_novi2.pt model_veci.pt) do if exist "backend\modeli\%%F" del /q "backend\modeli\%%F"
for %%F in (klinicki_sloj.py model_utils.py) do if exist "backend\%%F" del /q "backend\%%F"
for %%F in (Analiza.jsx Karton.jsx Pacijenti.jsx index.css) do if exist "frontend\src\%%F" del /q "frontend\src\%%F"
if exist "frontend\src\assets" rmdir /s /q "frontend\src\assets"
for %%F in (favicon.svg icons.svg) do if exist "frontend\public\%%F" del /q "frontend\public\%%F"
for %%F in (README.md .oxlintrc.json) do if exist "frontend\%%F" del /q "frontend\%%F"
echo.
echo Obrisano.
pause
