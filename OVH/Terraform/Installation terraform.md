Installation et configuration de Terraform
============
https://www.terraform.io/
https://blog.xebia.fr/2015/01/26/introduction-a-terraform/

#Récupération de l'executable de terraform
https://www.terraform.io/downloads.html

- Télécharger la version 64-bit pour windows
- Décompresser le fichier zip dans le dossier C:\Terraform 
- Ajouter l'executable dans les variables d'environnement Path à la fin de la liste "C:\Terraform;"
- Redemarrer le Windows 2012 R2 server

#Editions des fichiers de déploiement d'environnement.
dans un dossier de déploiement, on trouvera plusieurs fichiers de configuration,. Etant de simple fichiers textes, ils peuvent être ecrits soit au format propre à Terraform (.tf) soit en JSON (.tf.json). Il est préferable d'utiliser format .tf qui permet entre autre l'ajout de commentaire et une syntaxe plus simple, bien que le format JSON offre la flexibilité de la technologie JSON et est interprétable par une grandes majoité d'outils.
l est possible d’exporter toutes les valeurs de son infrastructure dans des fichiers texte en utilsant la commande output. Nous pouvons donc, par exemple générer un fichier d’inventaire pour une utilisation ultérieure.

 #Utilisation de terraform
- Pour pouvoir utiliser Terraform il faut se rendre, en ligne de commande, dans le dossier où se trouve les fichiers de configuration de déploiement de l'environnement.

Chaque fichier .tf présent dans le dossier sera scanné en effectuant les commandes suivantes. 

- Initialiser la configuration "terraform init" (cette manipulation est conseiller à l'ajout d'une nouvelle ressources)
- Vérification de notre cofiguration avec "Terraform plan"
- déploiement de l'environnement avec "terraform apply" 

- "terraform plan" et "terraform apply" doivent etre faits à chaque ajout, suppresion ou modification d'une ressources; 
    - pour une modification "terraform ne modifie pas vraiment la ressource mais la supprime et recré une autre avec la nouvelle configutation.

- Si on souhaite détruite l'environnement "terraform destroy"

En tapant "terraform", toutes les commandes disponibles s'afficheront.
Si on désir plus d'information sur une commande on tape "terraform <command> -h" (exemple: terraform apply -h)

