@echo off
:: This script:
::    - should be called as requestReturnMachines.bat -f input.json
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
:: out:
::-----
::{
::  "message" : "Delete VM success.",
::  "requestId" : "53ef32da-f4e0-424c-be56-5946922bb2cf"
::}
:: in:
::----
::{
::       "machines":[
::                   {"name": "hostskFVtVRMki"}
::                ]
::}
::::
setlocal EnableDelayedExpansion
set inJson=%2%
set scriptDir=%~dp0
set homeDir="%scriptDir%\.."
set computename=

:: fichier temporaire
set fileTemporaire=%scriptDir%\requestReturnMachines_%random%.txt

:: profile variable
set profile=%EGO_CONFDIR%\..\..\eservice\hostfactory\conf\providers\gcp_old_xavier\conf\gcpprov_templates.json

:: Recupération du nom de la machine à supprimer
if exist "%inJson%" (
	for /F "tokens=2 delims=:" %%i in ('findstr /i /C:"name" %inJson%') do set computename=%%i
	set computename=!computename:^"=!
) else (
	echo Pas de fichier de configuration definie
	goto enderror
)

:: Chargement des Variables
if exist "%profile%" (
	for /f "delims=" %%i in ('type %profile%') do %%i
) else (
	echo Pas de fichier de configuration definie
	goto enderror
)

:: Check des variables
:: project / zone / vmType / iproject / image / maxNumber
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

call gcloud compute instances stop %computename% --async --zone %zone% --quiet 2> %fileTemporaire%
for /F "tokens=2 delims=:" %%i in ('findstr /i /C:"operation" %fileTemporaire%') do set etape1=%%i
for /F "tokens=1 delims=]" %%i in ('echo !etape1!') do set etape1=%%i
for /F "tokens=9 delims=/" %%i in ('echo !etape1!') do set etape1=%%i
::set requestId=!etape1:operation-=!
set requestId=!etape1!
echo {
echo 		"message" : "Request Stop VM from GCP success.",
echo 		"requestId" : "%requestId%"
echo }
del %fileTemporaire%

call gcloud compute instances delete %computename% --project %project% --zone %zone% --quiet
set retourCommand=!errorlevel!
if %retourCommand%==0 (
	::	echo Suppression computes: OK
    goto end
) else (
	echo Suppression du compute %computename%: NOK
	goto enderror
)

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1