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
set computename=compute_%random%

:: fichier temporaire
set fileTemporaire=C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\requestMachines_list.txt

echo resource "openstack_compute_instance_v2" "%computename%" { >> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
	
echo 	name = "%computename%" >> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 	image_id = "${var.image_id}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 	flavor_name = "${var.flavor}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf

echo 	network = [>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 		{ name = "${var.net_public}" },>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 		{ name = "${var.net_priv}" }>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 	]>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 	region = "${var.region}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo 	user_data = "${data.template_file.%computename%_gateway_user_data.rendered}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo }>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf

echo data "template_file" "%computename%_gateway_user_data" {>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo     template = "${file("gateway_install.ps1")}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo     vars {>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo       admin_password="${var.admin_password}">> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf
echo     }	>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf

echo }>> C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf\%computename%.tf

echo %computename%>> %fileTemporaire%

call terraform plan C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf
call terraform apply -auto-approve C:\grid\IBM\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf

goto end

:end
::pause
exit /b 0

:enderror
::pause
exit /b 1