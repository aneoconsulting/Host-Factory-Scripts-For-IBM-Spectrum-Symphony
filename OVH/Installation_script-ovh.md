Installation du script IBM Spectrum Symphony sur les masters OVH
==============

#Prérequis 
- Terraform
- les id d'Ovh (user_name, tenant_name, password)

#Les scripts se trouvent dans le dossier
c:\grid\SpectrumComputing\3.7\hostfactory\providers\ovh\scripts

#Les fichiers de conf se trouvent dans 
c:\grid\SpectrumComputing\eservice\hostfactory\conf\providers\ovh\conf
c:\grid\SpectrumComputing\eservice\host
c:\grid\SpectrumComputing\eservice\hostfactory\work

- Récupération des ids d'OVH
- Remplacer public-cloud-ovh.auto.tfvars-example par public-cloud-ovh.auto.tfvars avec les données complétées

- Il faudra également faire "terraform init" dans le dossier pour permettre le bon fonctionnement des déploiements 
c:\grid\SpectrumComputing\eservice\hostfactory\work
