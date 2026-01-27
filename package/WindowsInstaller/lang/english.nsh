/*
Buildable Installer Language File
Language: English
*/

!insertmacro LANGFILE_EXT "English"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installed for Current User)"

${LangFileString} TEXT_WELCOME "This wizard will guide you through the installation of $(^NameDA). $\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compiling Python scripts..."

${LangFileString} TEXT_FINISH_DESKTOP "Create desktop shortcut"
${LangFileString} TEXT_FINISH_WEBSITE "Visit buildable.org/ for the latest news, support and tips"

#${LangFileString} FileTypeTitle "Buildable-Document"

#${LangFileString} SecAllUsersTitle "Install for all users?"
${LangFileString} SecFileAssocTitle "File associations"
${LangFileString} SecDesktopTitle "Desktop icon"

${LangFileString} SecCoreDescription "The Buildable files."
#${LangFileString} SecAllUsersDescription "Install Buildable for all users or just the current user."
${LangFileString} SecFileAssocDescription "Files with a .FCStd extension will automatically open in Buildable."
${LangFileString} SecDesktopDescription "A Buildable icon on the desktop."
#${LangFileString} SecDictionaries "Dictionaries"
#${LangFileString} SecDictionariesDescription "Spell-checker dictionaries that can be downloaded and installed."

#${LangFileString} PathName 'Path to the file $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'The file $\"xxx.exe$\" is not in the specified path.'

#${LangFileString} DictionariesFailed 'Download of dictionary for language $\"$R3$\" failed.'

#${LangFileString} ConfigInfo "The following configuration of Buildable could take a while."

#${LangFileString} RunConfigureFailed "Could not run configure script."
${LangFileString} InstallRunning "The installer is already running!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} is already installed!$\r$\n\
				Installing over existing installations is not recommended if the installed version$\r$\n\
				is a test release or if you have problems with your existing Buildable installation.$\r$\n\
				In these cases better reinstall Buildable.$\r$\n\
				Do you nevertheless want to install Buildable over the existing version?"
${LangFileString} NewerInstalled "You are trying to install an older version of Buildable than what you have installed.$\r$\n\
				  If you really want this, you must uninstall the existing Buildable $OldVersionNumber before."

#${LangFileString} FinishPageMessage "Congratulations! Buildable has been installed successfully.$\r$\n\
#					$\r$\n\
#					(The first start of Buildable might take some seconds.)"
${LangFileString} FinishPageRun "Launch Buildable"

${LangFileString} UnNotInRegistryLabel "Unable to find Buildable in the registry.$\r$\n\
					Shortcuts on the desktop and in the Start Menu will not be removed."
${LangFileString} UnInstallRunning "You must close Buildable first!"
${LangFileString} UnNotAdminLabel "You must have administrator privileges to uninstall Buildable!"
${LangFileString} UnReallyRemoveLabel "Are you sure you want to completely remove Buildable and all of its components?"
${LangFileString} UnBuildablePreferencesTitle 'Buildable$\'s user preferences'

#${LangFileString} SecUnProgDescription "Uninstalls xxx."
${LangFileString} SecUnPreferencesDescription 'Deletes Buildable$\'s configuration$\r$\n\
						(folder $\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						for you or for all users (if you are admin).'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Uninstall Buildable and all of its components."
