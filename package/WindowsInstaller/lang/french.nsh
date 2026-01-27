/*
Buildable Installer Language File
Language: French
*/

!insertmacro LANGFILE_EXT "French"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installation pour l'utilisateur courant)"

${LangFileString} TEXT_WELCOME "Cet assistant va vous guider tout au long de l'installation de $(^NameDA).$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compilation des scripts Python..."

${LangFileString} TEXT_FINISH_DESKTOP "Créer un raccourci sur le bureau"
${LangFileString} TEXT_FINISH_WEBSITE "Consulter les dernières nouvelles, trucs et astuces sur le site buildable.org"

#${LangFileString} FileTypeTitle "Document Buildable"

#${LangFileString} SecAllUsersTitle "Installer pour tous les utilisateurs ?"
${LangFileString} SecFileAssocTitle "Associations de fichiers"
${LangFileString} SecDesktopTitle "Icône du bureau"

${LangFileString} SecCoreDescription "Les fichiers Buildable"
#${LangFileString} SecAllUsersDescription "Installer Buildable pour tous les utilisateurs, ou seulement pour l$\'utilisateur courant ?"
${LangFileString} SecFileAssocDescription "Les fichiers de suffixe .FCStd seront automatiquement ouverts dans Buildable."
${LangFileString} SecDesktopDescription "Une icône Buildable sur le bureau."
#${LangFileString} SecDictionaries "Dictionnaires"
#${LangFileString} SecDictionariesDescription "Les dictionnaires pour correcteur orthographique qui peuvent être téléchargés et installés."

#${LangFileString} PathName 'Chemin vers le fichier $\"xxx.exe$\"'
#${LangFileString} InvalidFolder '$\"xxx.exe$\" introuvable dans le chemin d$\'accès spécifié.'

#${LangFileString} DictionariesFailed 'Le chargement du dictionnaire pour la langue $\"$R3$\" a échoué.'

#${LangFileString} ConfigInfo "La configuration de Buildable qui va suivre prendra un moment."

#${LangFileString} RunConfigureFailed "Échec de la tentative de configuration initiale de Buildable."
${LangFileString} InstallRunning "Le programme d$\'installation est toujours en cours !"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} est déjà installé !$\r$\n\
				L'installation par dessus les installations existantes n'est pas recommandée si la version installée$\r$\n\
				est une version de test ou si vous avez des problèmes avec votre installation Buildable existante.$\r$\n\
				Dans ces situations il vaut mieux réinstaller Buildable.$\r$\n\
				Voulez-vous néanmoins installer Buildable par dessus la version existante ?"
${LangFileString} NewerInstalled "Vous essayez d$\'installer une version de Buildable plus ancienne que celle qui est déjà installée.$\r$\n\
				  Si c$\'est ce qu vous voulez, vous devez d$\'abord désinstaller Buildable $OldVersionNumber."

#${LangFileString} FinishPageMessage "Félicitations ! Buildable est installé avec succès.$\r$\n\
#					$\r$\n\
#					(Le premier démarrage de Buildable peut demander quelques secondes.)"
${LangFileString} FinishPageRun "Démarrer Buildable"

${LangFileString} UnNotInRegistryLabel "Buildable introuvable dans la base des registres.$\r$\n\
					Les raccourcis sur le bureau et dans le menu de démarrage ne seront pas supprimés."
${LangFileString} UnInstallRunning "Vous devez fermer Buildable d$\'abord !"
${LangFileString} UnNotAdminLabel "Vous devez avoir les droits d$\'administration pour désinstaller Buildable !"
${LangFileString} UnReallyRemoveLabel "Êtes vous sûr(e) de vouloir supprimer complètement Buildable et tous ses composants ?"
${LangFileString} UnBuildablePreferencesTitle 'Préférences utilisateurs de Buildable'

#${LangFileString} SecUnProgDescription "Désinstalle le gestionnaire de bibliographie xxx."
${LangFileString} SecUnPreferencesDescription 'Supprime le répertoire de configuration de Buildable$\r$\n\
						$\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						pour tous les utilisateurs.'
${LangFileString} DialogUnPreferences 'Vous avez choisi de supprimer le répertoire de configuration de Buildables.$\r$\n\
						Cela supprimera également tous les addons Buildable installés.$\r$\n\
						Êtes-vous d$\'accord avec cela ?'
${LangFileString} SecUnProgramFilesDescription "Désinstaller Buildable et tous ses composants."
