@echo off
:: This script:
::    - should be called as getAvailableTemplates.bat -f input.json
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
::


setlocal EnableDelayedExpansion
set inJson=%2%
set scriptDir=%~dp0
set homeDir="%scriptDir%\.."


call terraform init C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf

call terraform plan C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf

goto end

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1


