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
set computename=compute
set listecompute=

:: special tests
set inJson=%EGO_CONFDIR%\..\..\eservice\hostfactory\conf\providers\gcp_old_xavier\conf\gcpprov_templates.json
:: Chargement des Variables
if exist "%inJson%" (
	for /f "delims=" %%i in ('type %inJson%') do %%i
) else (
	::echo Pas de fichier de configuration definie
	goto enderror
) 

:: Check des variables
:: project / zone / vmType / iproject / image / maxNumber
::
:: echo Lancement des tests des variables specifiques pour creation de computes
if not defined project (
    ::echo Attention variable project non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined zone (
    ::echo Attention variable zone non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined vmType (
    ::echo Attention variable vmType non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined iproject (
    ::echo Attention variable iproject non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined image (
    ::echo Attention variable image non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)
if not defined maxNumber (
    ::echo Attention variable maxNumber non definie: Voir l'instanciation des variables dans fichier de configuration
    goto enderror
)

::echo Check des variables: OK
echo {
echo  "templates" : [ {
echo    "templateId" : "Template-VM-SYMA",
echo    "maxNumber" : %maxNumber%,
echo	"allocated":	0,
echo	"available":	%maxNumber%,
echo	"reserved":	0,
echo    "attributes" : {
echo      "nram" : [ "Numeric", "%nram%" ],
echo      "ncpus" : [ "Numeric", "%ncpu%" ],
echo      "ncores" : [ "Numeric", "1" ],
echo      "type" : [ "String", "X86_64" ]
echo    },
echo    "pgrpName" : null
echo  } ],
echo  "message" : "Get available templates success."
echo }
goto end

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1


