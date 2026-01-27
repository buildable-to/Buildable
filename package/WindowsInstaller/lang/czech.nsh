/*
Buildable Installer Language File
Language: Czech
*/

!insertmacro LANGFILE_EXT "Czech"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installed for Current User)"

${LangFileString} TEXT_WELCOME "Tento pomocník vás provede instalací Buildableu.$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compiling Python scripts..."

${LangFileString} TEXT_FINISH_DESKTOP "Create desktop shortcut"
${LangFileString} TEXT_FINISH_WEBSITE "Visit buildable.org for the latest news, support and tips"

#${LangFileString} FileTypeTitle "Buildable-dokumentů"

#${LangFileString} SecAllUsersTitle "Instalovat pro všechny uživatele?"
${LangFileString} SecFileAssocTitle "Asociovat soubory"
${LangFileString} SecDesktopTitle "Ikonu na plochu"

${LangFileString} SecCoreDescription "Soubory Buildableu."
#${LangFileString} SecAllUsersDescription "Instalovat Buildable pro všechny uživatele nebo pouze pro současného uživatele."
${LangFileString} SecFileAssocDescription "Soubory s příponou .FCStd se automaticky otevřou v Buildableu."
${LangFileString} SecDesktopDescription "Ikonu Buildableu na plochu."
#${LangFileString} SecDictionaries "Slovníky"
#${LangFileString} SecDictionariesDescription "Spell-checker dictionaries that can be downloaded and installed."

#${LangFileString} PathName 'Cesta k souboru $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'Soubor $\"xxx.exe$\" není v zadané cestě.'

#${LangFileString} DictionariesFailed 'Download of dictionary for language $\"$R3$\" failed.'

#${LangFileString} ConfigInfo "The following configuration of Buildable could take a while."

#${LangFileString} RunConfigureFailed "Nelze spustit konfigurační skript"
${LangFileString} InstallRunning "Instalátor je již spuštěn!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} je již nainstalován!$\r$\n\
				Installing over existing installations is not recommended if the installed version$\r$\n\
				is a test release or if you have problems with your existing Buildable installation.$\r$\n\
				In these cases better reinstall Buildable.$\r$\n\
				Dou you nevertheles want to install Buildable over the existing version?"
${LangFileString} NewerInstalled "You are trying to install an older version of Buildable than what you have installed.$\r$\n\
				  If you really want this, you must uninstall the existing Buildable $OldVersionNumber before."

#${LangFileString} FinishPageMessage "Blahopřejeme! Buildable byl úspěšně nainstalován.$\r$\n\
#					$\r$\n\
#					(První spuštění Buildableu může trvat delší dobu.)"
${LangFileString} FinishPageRun "Spustit Buildable"

${LangFileString} UnNotInRegistryLabel "Nelze nalézt Buildable v registrech.$\r$\n\
					Zástupce na ploše a ve Start menu nebude smazán."
${LangFileString} UnInstallRunning "Nejprve musíte zavřít Buildable!"
${LangFileString} UnNotAdminLabel "Musíte mít administrátorská práva pro odinstalování Buildableu!"
${LangFileString} UnReallyRemoveLabel "Chcete opravdu smazat Buildable a všechny jeho komponenty?"
${LangFileString} UnBuildablePreferencesTitle 'Uživatelská nastavení Buildableu'

#${LangFileString} SecUnProgDescription "Odinstalovat xxx."
${LangFileString} SecUnPreferencesDescription 'Smazat konfigurační adresář Buildableu$\r$\n\
						$\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						pro všechny uživatele.'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Odinstalovat Buildable a všechny jeho komponenty."
