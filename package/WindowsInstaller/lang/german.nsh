/*
Buildable Installer Language File
Language: German
Author: Uwe Stöhr
*/

!insertmacro LANGFILE_EXT "German"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installiert für den aktuellen Benutzer)"

${LangFileString} TEXT_WELCOME "Dieser Assistent wird Sie durch die Installation von $(^NameDA) begleiten.$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Kompiliere Python Skripte..."

${LangFileString} TEXT_FINISH_DESKTOP "Ein Symbol auf der Arbeitsoberfläche erzeugen"
${LangFileString} TEXT_FINISH_WEBSITE "Besuchen Sie buildable.org für aktuelle Neuigkeiten"

#${LangFileString} FileTypeTitle "Buildable-Dokument"

#${LangFileString} SecAllUsersTitle "Für alle Nutzer installieren?"
${LangFileString} SecFileAssocTitle "Dateizuordnungen"
${LangFileString} SecDesktopTitle "Desktopsymbol"

${LangFileString} SecCoreDescription "Das Programm Buildable."
#${LangFileString} SecAllUsersDescription "Buildable für alle Nutzer oder nur für den aktuellen Nutzer installieren."
${LangFileString} SecFileAssocDescription "Vernüpfung zwischen Buildable und der .FCStd Dateiendung."
${LangFileString} SecDesktopDescription "Verknüpfung zu Buildable auf dem Desktop."
#${LangFileString} SecDictionaries "Wörterbücher"
#${LangFileString} SecDictionariesDescription "Rechtschreibprüfung- Wörterbucher die heruntergeladen und installiert werden können."

#${LangFileString} PathName 'Pfad zur Datei $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'Kann die Datei $\"xxx.exe$\" nicht finden.'

#${LangFileString} DictionariesFailed 'Herunterladen des Wörterbuchs für Sprache $\"$R3$\" fehlgeschlagen.'

#${LangFileString} ConfigInfo "Die folgende Konfiguration von Buildable wird eine Weile dauern."

#${LangFileString} RunConfigureFailed "Konnte das Konfigurationsskript nicht ausführen."
${LangFileString} InstallRunning "Der Installer läuft bereits!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} ist bereits installiert!$\r$\n\
				Das Installieren über bestehende Installationen ist nicht empfohlen, wenn die installierte Version$\r$\n\
				eine Testversion ist oder wenn es Probleme mit der bestehenden Buildable-Installation gibt.$\r$\n\
				Besser Sie deinstallieren in diesen Fällen Buildable zuerst.$\r$\n\
				Wollen Sie Buildable dennoch über die bestehende Version installieren?"
${LangFileString} NewerInstalled "Sie versuchen eine Vesion von Buildable zu installieren, die älter als die derzeit installierte ist.$\r$\n\
				  Wenn Sie das wirklich wollen, müssen Sie erst das existierende Buildable $OldVersionNumber deinstallieren."

#${LangFileString} FinishPageMessage "Glückwunsch! Buildable wurde erfolgreich installiert.$\r$\n\
#					$\r$\n\
#					(Der erste Start von Buildable kann etwas länger dauern.)"
${LangFileString} FinishPageRun "Buildable starten"

${LangFileString} UnNotInRegistryLabel "Kann Buildable nicht in der Registry finden.$\r$\n\
					Desktopsymbole und Einträge im Startmenü können nicht entfernt werden."
${LangFileString} UnInstallRunning "Sie müssen Buildable zuerst beenden!"
${LangFileString} UnNotAdminLabel "Sie benötigen Administratorrechte um Buildable zu deinstallieren!"
${LangFileString} UnReallyRemoveLabel "Sind Sie sicher, dass sie Buildable und all seine Komponenten deinstallieren möchten?"
${LangFileString} UnBuildablePreferencesTitle 'Buildables Benutzereinstellungen'

#${LangFileString} SecUnProgDescription "Deinstalliert xxx."
${LangFileString} SecUnPreferencesDescription 'Löscht Buildables Benutzereinstellungen$\r$\n\
						(Ordner $\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						für Sie oder für alle Benutzer (wenn Sie Admin sind).'
${LangFileString} DialogUnPreferences 'Sie haben ausgewählt, die Buildable-Benutzereinstellungen zu löschen.$\r$\n\
						Dies wird auch alle installierten Buildable-Addons löschen.$\r$\n\
						Sind Sie damit einverstanden?'
${LangFileString} SecUnProgramFilesDescription "Deinstalliert Buildable und all seine Komponenten."
