@echo off
:: This script:
::    - should be called as requestMachines.bat -f input.json
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
:: out:
::-----
::{
::"message":"Request VM from AWS successful.",
::"requestId":"req-f0d97275-dce2-4f22-94a4-44717e802b97"
::}
::
::
setlocal EnableDelayedExpansion
set inJson=%2%
set scriptDir=%~dp0
set homeDir="%scriptDir%\.."
set computename=compute%random%

:: fichier temporaire
set fileTemporaire=%scriptDir%\requestMachines_%random%.txt

:: profile variable
set profile=%EGO_CONFDIR%\..\..\eservice\hostfactory\conf\providers\gcp_old_xavier\conf\gcpprov_templates.json

:: Chargement des Variables
if exist "%profile%" (
	for /f "delims=" %%i in ('type %profile%') do %%i
) else (
	echo Pas de fichier de configuration definie
	goto enderror
) 

:: Check des variables
:: project / zone / vmType / iproject / image / maxNumber / nram / ncpu
::
:: echo Lancement des tests des variables specifiques pour creation de computes
if not defined project (
    echo Attention variable project non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined zone (
    echo Attention variable zone non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined vmType (
    echo Attention variable vmType non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined iproject (
    echo Attention variable iproject non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined image (
    echo Attention variable image non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined maxNumber (
    echo Attention variable maxNumber non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined nram (
    echo Attention variable nram non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined ncpu (
    echo Attention variable ncpu non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)

call gcloud compute instances create %computename% --async --project %project% --zone %zone% --image-project %iproject% --image %image% --custom-cpu=%ncpu% --custom-memory=%nram% 2> %fileTemporaire%
set retourCommand=!errorlevel!
for /F "tokens=3 delims=:" %%i in ('findstr /i /C:"https" %fileTemporaire%') do set etape1=%%i
for /F "tokens=1 delims=]" %%i in ('echo !etape1!') do set etape1=%%i
for /F "tokens=9 delims=/" %%i in ('echo !etape1!') do set etape1=%%i
::set requestId=!etape1:operation-=!
set requestId=!etape1!

if %retourCommand%==0 (
	echo {
	echo 		"message" : "Request Create VM from GCP successful.",
	echo 		"requestId" : "%requestId%"
	echo }
	del %fileTemporaire%
    goto end
) else (
	echo Create compute %computename% : NOK
	del %fileTemporaire%
	goto enderror
)

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1