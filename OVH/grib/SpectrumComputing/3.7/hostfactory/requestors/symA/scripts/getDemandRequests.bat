@echo off
:: This script:
::    - should be called as getDemandRequest.sh
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
::
set scriptDir=%~dp0
set homeDir=%scriptDir%\..

where python >nul 2>nul
if %errorlevel%==1 (
    echo "Python not installed. HostFactory: Requestor plug-in requires Python version higher than or equal to 2.7 but lower than 3.0"
    goto end
)

set hour=%time:~0,2%
if "%hour:~0,1%" == " " set hour=0%hour:~1,1%
set min=%time:~3,2%
if "%min:~0,1%" == " " set min=0%min:~1,1%
set secs=%time:~6,2%
if "%secs:~0,1%" == " " set secs=0%secs:~1,1%

set tempfile=%HF_WORKDIR%\D%hour%%min%%secs%%RANDOM%.txt
if not exist "%HF_WORKDIR%" (
    set tempfile=%scriptDir%\D%hour%%min%%secs%%RANDOM%.txt
)

python -c "import sys; print(sys.version_info[:])[0]" >"%tempfile%"

for /f "usebackq" %%x in ("%tempfile%") do set PYVER=%%x
del "%tempfile%"

if NOT "%PYVER%"=="2" (
    echo "Python version error. Requestor plug-in requires Python version higher than or equal to 2.7 but lower than 3.0"
    goto end
)

python -c "import sys; print(sys.version_info[:])[1]" >"%tempfile%"

for /f "usebackq" %%x in ("%tempfile%") do set PYVER2=%%x
del "%tempfile%"

if "%PYVER2%" lss "7" (
    echo "Python version error. Requestor plug-in requires Python version higher than or equal to 2.7 but lower than 3.0"
    goto end
)


set _python=python

%_python% "%homeDir%\scripts\Main.py" --getDemandRequests "%homeDir%" "%2%"


exit /b

:end
exit /b 1
