/*
Buildable Installer Language File
Language: Russian
*/

!insertmacro LANGFILE_EXT "Russian"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Установлено для текущего пользователя)"

${LangFileString} TEXT_WELCOME "Этот мастер проведет вас через процесс установки $(^NameDA). $\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Компиляция скриптов Python..."

${LangFileString} TEXT_FINISH_DESKTOP "Создать ярлык на рабочем столе"
${LangFileString} TEXT_FINISH_WEBSITE "Перейти на buildable.org за новостями, поддержкой и советами"

#${LangFileString} FileTypeTitle "Buildable-Document"

#${LangFileString} SecAllUsersTitle "Установить для всех пользователей?"
${LangFileString} SecFileAssocTitle "Ассоциации файлов"
${LangFileString} SecDesktopTitle "Значок на рабочем столе"

${LangFileString} SecCoreDescription "Файлы Buildable."
#${LangFileString} SecAllUsersDescription "Установить Buildable для всех пользователей или только для текущего пользователя."
${LangFileString} SecFileAssocDescription "Файлы с расширением .FCStd будут автоматически открываться в Buildable."
${LangFileString} SecDesktopDescription "Значок Buildable на рабочем столе."
#${LangFileString} SecDictionaries "Словари"
#${LangFileString} SecDictionariesDescription "Словари для проверки орфографии, которые можно скачать и установить."

#${LangFileString} PathName 'Путь к файлу $\"xxx.exe$\"'
#${LangFileString} InvalidFolder 'Файл $\"xxx.exe$\" отсутствует по этому пути.'

#${LangFileString} DictionariesFailed 'Не удалось загрузить словарь для языка $\"$R3$\".'

#${LangFileString} ConfigInfo "Следующая конфигурация Buildable займет некоторое время."

#${LangFileString} RunConfigureFailed "Не удалось выполнить сценарий настройки"
${LangFileString} InstallRunning "Установщик уже запущен!"
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} уже установлен!$\r$\n\
				Установка поверх существующих установок не рекомендуется, если установленная версия$\r$\n\
				является тестовым выпуском или у вас возникли проблемы с существующей установкой Buildable.$\r$\n\
				В этих случаях лучше переустановить Buildable.$\r$\n\
				Вы все равно хотите установить Buildable поверх существующей версии?"
${LangFileString} NewerInstalled "Вы пытаетесь установить более старую версию Buildable, чем уже установленная.$\r$\n\
				  Если вы действительно хотите этого, то сначала необходимо удалить существующий Buildable $OldVersionNumber."

#${LangFileString} FinishPageMessage "Поздравляем! Buildable был успешно установлен.$\r$\n\
#					$\r$\n\
#					(Первый запуск Buildable может занять несколько секунд.)"
${LangFileString} FinishPageRun "Запустить Buildable"

${LangFileString} UnNotInRegistryLabel "Не удалось найти Buildable в реестре.$\r$\n\
					Ярлыки на рабочем столе и в меню Пуск не будут удалены."
${LangFileString} UnInstallRunning "Вы должны сначала закрыть Buildable!"
${LangFileString} UnNotAdminLabel "Необходимо иметь права администратора для удаления Buildable!"
${LangFileString} UnReallyRemoveLabel "Вы действительно хотите полностью удалить Buildable и все его компоненты?"
${LangFileString} UnBuildablePreferencesTitle 'Пользовательские настройки Buildable'

#${LangFileString} SecUnProgDescription "Удалить менеджер xxx."
${LangFileString} SecUnPreferencesDescription 'Удалить настройки Buildable$\r$\n\
						(каталог $\"$AppPre\username\$\r$\n\
						$AppSuff\$\r$\n\
						${APP_DIR_USERDATA}$\")$\r$\n\
						для вас или для всех пользователей (если вы администратор).'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Удалить Buildable и все его компоненты."
