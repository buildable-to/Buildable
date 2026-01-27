/*
Buildable Installer Language File
Language: Turkish
*/

!insertmacro LANGFILE_EXT "Turkish"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Installed for Current User)"

${LangFileString} TEXT_WELCOME "Bu sihirbaz size Buildable programını kuracak.$\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Compiling Python scripts..."

${LangFileString} TEXT_FINISH_DESKTOP "Create desktop shortcut"
${LangFileString} TEXT_FINISH_WEBSITE "Visit buildable.org for the latest news, support and tips"

#${LangFileString} FileTypeTitle "Buildable-Document"

#${LangFileString} SecAllUsersTitle "Tüm kullanıcılar için kur?"
${LangFileString} SecFileAssocTitle "Dosya eşleşmeleri"
${LangFileString} SecDesktopTitle "Masaüstü ikonu"

${LangFileString} SecCoreDescription "Buildable dosyaları."
#${LangFileString} SecAllUsersDescription "Buildable tüm kullanıcılar için mi yoksa yalnızca bu kullanıcıya mı kurulacak."
${LangFileString} SecFileAssocDescription "Uzantısı .FCStd olan dosyalar otomatik olarak Buildable ile açılsın."
${LangFileString} SecDesktopDescription "Masaüstüne bir Buildable ikonu koy."
#${LangFileString} SecDictionaries "Sözlükleri"
#${LangFileString} SecDictionariesDescription "Spell-checker dictionaries that can be downloaded and installed."

#${LangFileString} PathName 'Path to the file $\"xxx.exe$\"'
#${LangFileString} InvalidFolder '$\"xxx.exe$\" dosyası belirttiğiniz dizinde bulunamadı.'

#${LangFileString} DictionariesFailed 'Download of dictionary for language $\"$R3$\" failed.'

#${LangFileString} ConfigInfo "Sıradaki Buildable yapılandırması biraz zaman alacak."

#${LangFileString} RunConfigureFailed "Yapılandırma programı çalıştırılamadı"
${LangFileString} InstallRunning "Kurulum programı zaten çalışıyor!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} kurulu zaten!$\r$\n\
				Installing over existing installations is not recommended if the installed version$\r$\n\
				is a test release or if you have problems with your existing Buildable installation.$\r$\n\
				In these cases better reinstall Buildable.$\r$\n\
				Dou you nevertheles want to install Buildable over the existing version?"
${LangFileString} NewerInstalled "You are trying to install an older version of Buildable than what you have installed.$\r$\n\
				  If you really want this, you must uninstall the existing Buildable $OldVersionNumber before."

#${LangFileString} FinishPageMessage "Tebrikler! Buildable başarıyla kuruldu.$\r$\n\
#					$\r$\n\
#					(Buildable in ilk açılışı birkaç saniye alabilir.)"
${LangFileString} FinishPageRun "Buildable Başlat"

${LangFileString} UnNotInRegistryLabel "Sistem kütüğünde Buildable bulunamadı.$\r$\n\
					Başlat menüsü ve masaüstünüzdeki kısayollar silinemeyecek."
${LangFileString} UnInstallRunning "Önce Buildable i kapatmalısınız!"
${LangFileString} UnNotAdminLabel "Buildable kaldırabilmek için yönetici yetkileri gerekiyor!"
${LangFileString} UnReallyRemoveLabel "Buildable ve tüm bileşenlerini kaldırmak istediğinize emin misiniz?"
${LangFileString} UnBuildablePreferencesTitle 'Buildable$\'s user preferences'

#${LangFileString} SecUnProgDescription "Uninstalls xxx."
${LangFileString} SecUnPreferencesDescription 'Deletes Buildable$\'s configuration folder$\r$\n\
						$\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						for all users.'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Uninstall Buildable and all of its components."
