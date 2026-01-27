/*
Buildable Installer Language File
Language: Italian
*/

!insertmacro LANGFILE_EXT "Italian"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installed for Current User)"

${LangFileString} TEXT_WELCOME "Verrete guidati nell'installazione di $(^NameDA)$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compilazione degli script Python in corso..."

${LangFileString} TEXT_FINISH_DESKTOP "Crea icona sul desktop"
${LangFileString} TEXT_FINISH_WEBSITE "Visitate buildable.org per ultime novità, aiuto e suggerimenti"

#${LangFileString} FileTypeTitle "Documento di Buildable"

#${LangFileString} SecAllUsersTitle "Installare per tutti gli utenti?"
${LangFileString} SecFileAssocTitle "Associazioni dei file"
${LangFileString} SecDesktopTitle "Icona sul Desktop"

${LangFileString} SecCoreDescription "I file di Buildable."
#${LangFileString} SecAllUsersDescription "Installazione Buildable per tutti gli utenti o solo per l'utente attuale."
${LangFileString} SecFileAssocDescription "Associa i files con estensione .FCStd al programma Buildable."
${LangFileString} SecDesktopDescription "Icona Buildable sul desktop."
#${LangFileString} SecDictionaries "Dizionari"
#${LangFileString} SecDictionariesDescription "Dizionari per il controllo ortografico che possono essere scaricati e installati."

#${LangFileString} PathName 'Percorso del file $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'Il file $\"xxx.exe$\" non è nel percorso indicato.'

#${LangFileString} DictionariesFailed 'Lo scaricamento del dizionario per la lingua  $\"$R3$\" non e$\' andato a buon fine.'

#${LangFileString} ConfigInfo "La seguente configurazione di Buildable richiederà un po' di tempo."

#${LangFileString} RunConfigureFailed "Fallito tentativo di eseguire lo script di configurazione"
${LangFileString} InstallRunning "Il programma di installazione è già in esecuzione!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} è già installato!$\r$\n\
				Procedere con l'installazione su quella esistente non è raccomandabile se la versione version$\r$\n\
				è una release di test o se avete problemi con la vostra installazione corrente di Buildable.$\r$\n\
				In questi casi è preferibile installare nuovamente Buildable.$\r$\n\
				Volete procedere comunque con l'installazione di Buildable su quella esistente?"
${LangFileString} NewerInstalled "Si sta procedendo ad installare una versione di Buildable precedente a quella in uso.$\r$\n\
				  Se si vuole procedere, è necessario prima disinstallare la versione Buildable $OldVersionNumber."

#${LangFileString} FinishPageMessage "Congratulazioni! Buildable è stato installato con successo.$\r$\n\
#					$\r$\n\
#					(Il primo avvio di Buildable potrebbe richiedere qualche secondo in più.)"
${LangFileString} FinishPageRun "Lancia Buildable"

${LangFileString} UnNotInRegistryLabel "Non riesco a trovare Buildable nel registro.$\r$\n\
					I collegamenti sul desktop e nel menu Start non saranno rimossi."
${LangFileString} UnInstallRunning "È necessario chiudere Buildable!"
${LangFileString} UnNotAdminLabel "Occorrono i privilegi da amministratore per rimuovere Buildable!"
${LangFileString} UnReallyRemoveLabel "Siete sicuri di voler rimuovere completamente Buildable e tutti i suoi componenti?"
${LangFileString} UnBuildablePreferencesTitle 'Impostazioni personali di Buildable'

#${LangFileString} SecUnProgDescription "Rimuove xxx."
${LangFileString} SecUnPreferencesDescription 'Elimina la cartella con la configurazione di Buildable$\r$\n\
						$\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						per tutti gli utenti.'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Rimuove Buildable e tutti i suoi componenti."
