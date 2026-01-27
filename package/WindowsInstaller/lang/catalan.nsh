/*
Buildable Installer Language File
Language: Catalan
*/

!insertmacro LANGFILE_EXT "Catalan"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installed for Current User)"

${LangFileString} TEXT_WELCOME "Aquest assistent us guiarà en la instal·lació del Buildable.$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compiling Python scripts..."

${LangFileString} TEXT_FINISH_DESKTOP "Create desktop shortcut"
${LangFileString} TEXT_FINISH_WEBSITE "Visit buildable.org for the latest news, support and tips"

#${LangFileString} FileTypeTitle "Document Buildable"

#${LangFileString} SecAllUsersTitle "Voleu instal·lar-ho per a tots els usuaris?"
${LangFileString} SecFileAssocTitle "Associació de fitxers"
${LangFileString} SecDesktopTitle "Icona a l'escriptori"

${LangFileString} SecCoreDescription "Els fitxers del Buildable."
#${LangFileString} SecAllUsersDescription "Instal·la el Buildable per a tots els usuaris o només per a l'usuari actual."
${LangFileString} SecFileAssocDescription "Els fitxers amb extensió .FCStd s'obriran automàticament amb el Buildable."
${LangFileString} SecDesktopDescription "Una icona del Buildable a l'escriptori."
#${LangFileString} SecDictionaries "Diccionaris"
#${LangFileString} SecDictionariesDescription "Spell-checker dictionaries that can be downloaded and installed."

#${LangFileString} PathName 'Camí al fitxer $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'El fitxer $\"xxx.exe$\" no es troba al camí indicat.'

#${LangFileString} DictionariesFailed 'Download of dictionary for language $\"$R3$\" failed.'

#${LangFileString} ConfigInfo "La configuració següent del Buildable pot trigar una mica."

#${LangFileString} RunConfigureFailed "No es pot executar el programa de configuració"
${LangFileString} InstallRunning "L'instal·lador ja s'està executant!"
${LangFileString} AlreadyInstalled "El Buildable ${APP_SERIES_KEY2} ja es troba instal·lat!$\r$\n\
				Installing over existing installations is not recommended if the installed version$\r$\n\
				is a test release or if you have problems with your existing Buildable installation.$\r$\n\
				In these cases better reinstall Buildable.$\r$\n\
				Dou you nevertheles want to install Buildable over the existing version?"
${LangFileString} NewerInstalled "You are trying to install an older version of Buildable than what you have installed.$\r$\n\
				  If you really want this, you must uninstall the existing Buildable $OldVersionNumber before."

#${LangFileString} FinishPageMessage "Felicitats! Heu instal·lat correctament el Buildable.$\r$\n\
#					$\r$\n\
#					(La primera execució del Buildable pot trigar alguns segons.)"
${LangFileString} FinishPageRun "Executa el Buildable"

${LangFileString} UnNotInRegistryLabel "No es possible trobar el Buildable al registre.$\r$\n\
					No se suprimiran les dreceres de l'escriptori i del menú inici."
${LangFileString} UnInstallRunning "Primer heu de tancar el Buildable!"
${LangFileString} UnNotAdminLabel "Necessiteu drets d'administrador per desinstal·lar el Buildable!"
${LangFileString} UnReallyRemoveLabel "Esteu segur de voler suprimir completament el Buildable i tots els seus components?"
${LangFileString} UnBuildablePreferencesTitle 'Preferències d$\'usuari del Buildable'

#${LangFileString} SecUnProgDescription "Desinstal·xxx."
${LangFileString} SecUnPreferencesDescription 'Suprimeix les carptes de configuració del Buildable$\r$\n\
						$\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						de tots els usuaris.'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Desinstal·la el Buildable i tots els seus components."
