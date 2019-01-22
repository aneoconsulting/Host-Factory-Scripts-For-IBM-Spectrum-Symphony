@echo off
:: This script:
::    - should be called as getRequestMachines.bat -f input.json
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
:: IN:
::----
:: {
::        "requests":     [{
::                       "requestId":    "req-33e9ed03-62c0-4b46-b7cd-3c54fb497b72"
::                }]
::}
::
:: OUT:
::-----
::{
::  "requests" : [ {
::     "requestId" : "req-33e9ed03-62c0-4b46-b7cd-3c54fb497b72",
::     "status" : "complete/running",
::	   "message" : "optional"
::     "machines" : [ {
::       	"machineId" : "abcduKg",
::      	"name" : "hostskFVtVRMki",
::      	"result" : "‘executing’/‘fail’/‘succeed’",
::      	"status" : "RUNNING",
:: 	        "launchtime" : 1516131665,
::          "message" : ""
::    } ]
::  } ]
::}
::
:: URI:
::-----
:: https://www.googleapis.com/compute/v1/projects/psf-cacib/zones/europe-west1-b/operations/%requestId%
::

setlocal EnableDelayedExpansion
set inJson=%2%
set scriptDir=%~dp0
set homeDir="%scriptDir%\.."
set requestId=

:: fichier temporaire
set fileTemporaire=%scriptDir%\getRequestMachines_%random%.txt

:: profile variable
set profile=%EGO_CONFDIR%\..\..\eservice\hostfactory\conf\providers\gcp_old_xavier\conf\gcpprov_templates.json

:: Recupération du nom de la machine à supprimer
for /f "tokens=2 delims=:" %%i in ('findstr /i /C:"requestId" %inJson%') do set requestId=%%i
for /f "tokens=2,3,4,5 delims=-" %%i in ('echo !requestId!') do set requestId=%%i-%%j-%%k-%%l
set requestId=!requestId:^"=!
set requestId=operation-!requestId!

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
::echo Lancement des tests des variables specifiques pour creation de computes
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

set URI=https://www.googleapis.com/compute/v1/projects/%project%/zones/%zone%/operations/%requestId%

call gcloud compute operations describe %URI% > %fileTemporaire%
set codeRetour=!errorlevel!
for /F "tokens=2 delims=:" %%i in ('findstr /i /C:"status" %fileTemporaire%') do set status=%%i
set status=!status:^ =!
for /F "tokens=2 delims=:" %%i in ('findstr /i /C:"progress" %fileTemporaire%') do set progress=%%i
set progress=!progress:^ =!
for /F "tokens=2 delims=:" %%i in ('findstr /i /C:"targetId" %fileTemporaire%') do set targetId=%%i
set targetId=!targetId:^ =!
set targetId=!targetId:^'=!
for /F "tokens=3 delims=:" %%i in ('findstr /i /C:"targetLink" %fileTemporaire%') do set targetLinktemp=%%i
for /F "tokens=9 delims=/" %%i in ('echo %targetLinktemp%') do set targetLink=%%i

if "%status%"=="DONE" (
	set fstatus=complete
	set resultat=succeed
)
if "%status%"=="RUNNING" (
	set fstatus=running
	set resultat=executing
)
::set status=complete_with_error
::set result=fail

if !codeRetour!==0 (
	set finalcode=0
echo {
echo    "requests": [{
echo                     "requestId": "%requestId%",
echo                     "status": "%fstatus%",
echo                     "message": "",
echo                     "machines": [{
:: echo		                             "machineId": "%targetId%",
echo      	                             "name": "%targetLink%",
echo      	                             "result": "%resultat%",
echo		                             "launchtime": 1516131665,
echo		                             "message": "Create OK"
echo                     }]
echo    }]
echo }
) else (
	echo Check compute %%i: NOK
	set finalcode=1 
)

del %fileTemporaire%
exit /b %finalcode%

:enderror
::pause
exit /b 1 