@echo off
setlocal
cd /d "%~dp0"
set "VENV=%LOCALAPPDATA%\CentralPropostas\venv"
set "PY=%VENV%\Scripts\python.exe"
if not exist "requirements.txt" goto arquivos
if not exist "app.py" goto arquivos
if exist "%PY%" goto instalar
where python >nul 2>nul
if errorlevel 1 goto sempython
echo Criando ambiente virtual fora do OneDrive...
python -m venv "%VENV%"
if errorlevel 1 goto erro
:instalar
echo Instalando dependencias em "%VENV%"...
"%PY%" -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 goto erro
echo Iniciando a Central de Propostas...
"%PY%" -m streamlit run "%~dp0app.py"
if errorlevel 1 goto erro
exit /b 0
:arquivos
echo Coloque este arquivo na mesma pasta de app.py e requirements.txt.
goto erro
:sempython
echo Python nao encontrado. Instale o Python e adicione ao PATH.
:erro
echo Falha ao iniciar a central. Confira a mensagem acima.
pause
exit /b 1
