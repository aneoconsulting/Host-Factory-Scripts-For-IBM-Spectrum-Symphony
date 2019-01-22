@echo on
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
call terraform show
goto end

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1 