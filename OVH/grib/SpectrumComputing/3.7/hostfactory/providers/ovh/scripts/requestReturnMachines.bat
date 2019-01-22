@echo off
:: This script:
::    - should be called as requestReturnMachines.bat -f input.json
::    - exit with 0 if calling succeed and result will be in the stdOut
::    - exit with 1 if calling failed and error message will be in the stdOut
:: out:
::-----
::{
::  "message" : "Delete VM success.",
::  "requestId" : "XXXXX"
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

:: fichier temporaire
set fileTemporaire=C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\requestMachines_list.txt

for /f "tokens=*" %%a in (requestMachines_list.txt) do (
	call terraform destroy -auto-approve -target=openstack_compute_instance_v2.%%a C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf
	del C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%%a.tf
)

del %fileTemporaire%

goto end


:end
::pause
exit /b 0

:enderror
::pause
exit /b 1
