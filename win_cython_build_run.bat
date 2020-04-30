@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Auxiliary\Build\vcvarsx86_amd64.bat"
python setup.py build_ext --inplace
IF %ERRORLEVEL% NEQ 0 (
  exit /b %ERRORLEVEL%
)
set PYTHONUNBUFFERED=1
"C:\Program Files\Python38\python.exe" octodeco\test.py
