/*
Buildable Installer Language File
Language: Swedish
*/

!insertmacro LANGFILE_EXT "Swedish"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installerad för aktuell användare)"

${LangFileString} TEXT_WELCOME "Denna guide tar dig igenom installationen av $(^NameDA), $\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Kompilerar Pythonskript..."

${LangFileString} TEXT_FINISH_DESKTOP "Skapa skrivbordsgenväg"
${LangFileString} TEXT_FINISH_WEBSITE "Besök buildable.org för de senaste nyheterna, support och tips"

#${LangFileString} FileTypeTitle "Buildable-dokument"

#${LangFileString} SecAllUsersTitle "Installera för alla användare?"
${LangFileString} SecFileAssocTitle "Filassociationer"
${LangFileString} SecDesktopTitle "Skrivbordsikon"

${LangFileString} SecCoreDescription "Buildable-filerna."
#${LangFileString} SecAllUsersDescription "Installera Buildable för alla användare, eller enbart för den aktuella användaren."
${LangFileString} SecFileAssocDescription "Filer med ändelsen .FCStd kommer att automatiskt öppnas i Buildable."
${LangFileString} SecDesktopDescription "En Buildable-ikon på skrivbordet."
#${LangFileString} SecDictionaries "Ordböcker"
#${LangFileString} SecDictionariesDescription "Stavningskontrollens ordböcker som kan laddas ned och installeras."

#${LangFileString} PathName 'Sökväg till filen $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'Filen $\"xxx.exe$\" finns inte i den angivna sökvägen.'

#${LangFileString} DictionariesFailed 'Nedladdning av ordbok för språk $\"$R3$\" misslyckades.'

#${LangFileString} ConfigInfo "Följande konfigurering av Buildable kommer att ta en stund."

#${LangFileString} RunConfigureFailed "Kunde inte köra konfigurationsskriptet"
${LangFileString} InstallRunning "Installationsprogrammet körs redan!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} är redan installerad!$\r$\n\
				Att installera över en nuvarande installation är inte rekommenderat om den installerade$\r$\n\
				versionen är en testutgåva eller om du har problem med din nuvarande Buildable-installation.$\r$\n\
				I dessa fall är det bättre att ominstallera Buildable.$\r$\n\
				Vill du ändå installera Buildable över den nuvarande versionen?"
${LangFileString} NewerInstalled "Du försöker att installera en äldre version av Buildable än vad du har installerad.$\r$\n\
				  Om du verkligen vill detta måste du avinstallera den befintliga Buildable $OldVersionNumber innan."

#${LangFileString} FinishPageMessage "Gratulerar! Buildable har installerats framgångsrikt.$\r$\n\
#					$\r$\n\
#					(Den första starten av Buildable kan ta en stund.)"
${LangFileString} FinishPageRun "Kör Buildable"

${LangFileString} UnNotInRegistryLabel "Kan inte hitta Buildable i registret.$\r$\n\
					Genvägar på skrivbordet och i startmenyn kommer inte att tas bort."
${LangFileString} UnInstallRunning "Du måste stänga Buildable först!"
${LangFileString} UnNotAdminLabel "Du måste ha administratörsbehörighet för att avinstallera Buildable!"
${LangFileString} UnReallyRemoveLabel "Är du säker på att du verkligen vill fullständigt ta bort Buildable och alla dess komponenter?"
${LangFileString} UnBuildablePreferencesTitle 'Buildable-användarinställningar'

#${LangFileString} SecUnProgDescription "Avinstallerar xxx."
${LangFileString} SecUnPreferencesDescription 'Raderar Buildable-konfiguration$\r$\n\
						(katalog $\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						för dig eller för alla användare (om du är admin).'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Avinstallera Buildable och alla dess komponenter."
