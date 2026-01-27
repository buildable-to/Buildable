/*
Buildable Installer Language File
Language: Basque
*/

!insertmacro LANGFILE_EXT "Basque"

${LangFileString} TEXT_INSTALL_CURRENTUSER "(Instalatu uneko erabiltzailearentzat)"

${LangFileString} TEXT_WELCOME "Morroi honek $(^NameDA) aplikazioaren instalazio urratsetan zehar lagunduko dizu, $\r$\n\
				$\r$\n\
				$_CLICK"

#${LangFileString} TEXT_CONFIGURE_PYTHON "Python script-ak konpilatzen..."

${LangFileString} TEXT_FINISH_DESKTOP "Sortu mahaigaineko lasterbidea"
${LangFileString} TEXT_FINISH_WEBSITE "Bisitatu buildable.org azken berriak, aholkuak eta laguntza lortzeko"

#${LangFileString} FileTypeTitle "Buildable-dokumentua"

#${LangFileString} SecAllUsersTitle "Instalatu erabiltzaile guztientzako?"
${LangFileString} SecFileAssocTitle "Fitxategiaren esleipenak"
${LangFileString} SecDesktopTitle "Mahaigaineko ikonoa"

${LangFileString} SecCoreDescription "Buildable fitxategiak."
#${LangFileString} SecAllUsersDescription "Instalatu Buildable erabiltzaile guztientzako, edo soilik uneko erabiltzailearentzako."
${LangFileString} SecFileAssocDescription ".FCStd luzapeneko fitxategiak Buildable-ekin irekiko dira automatikoki."
${LangFileString} SecDesktopDescription "Buildable ikonoa mahaigainean."
#${LangFileString} SecDictionaries "Hiztegia"
#${LangFileString} SecDictionariesDescription "Zuzentzaile ortografikoen hiztegiak deskarga eta instala daitezke."

#${LangFileString} PathName '$\"xxx.exe$\" fitxategiaren bide-izena'
#${LangFileString} InvalidFolder '$\"xxx.exe$\" fitxategia ez dago zehaztutako bide-izenean.'

#${LangFileString} DictionariesFailed 'Huts egin du  $\"$R3$\" hizkuntzaren hiztegia deskargatzean.'

#${LangFileString} ConfigInfo "Buildable-en hurrengo konfigurazioak denbora piskat beharko du."

#${LangFileString} RunConfigureFailed "Ezin izan da konfigurazioaren script-a exekutatu"
${LangFileString} InstallRunning "Instalatzailea jadanik exekutatzen ari da."
${LangFileString} AlreadyInstalled "Buildable ${APP_SERIES_KEY2} jadanik instalatuta dago!$\r$\n\
				Installing over existing installations is not recommended if the installed version$\r$\n\
				is a test release or if you have problems with your existing Buildable installation.$\r$\n\
				In these cases better reinstall Buildable.$\r$\n\
				Dou you nevertheles want to install Buildable over the existing version?"
${LangFileString} NewerInstalled "Instalatuta dagoen Buildable baino bertsio zaharragoa instalatzen saiatzen ari zara.$\r$\n\
				  Hori egitea nahi baduzu, lehenbizi existitzen den Buildable $OldVersionNumber desinstalatu beharko duzu."

#${LangFileString} FinishPageMessage "Zorionak! Buildable ongi instalatu da.$\r$\n\
#					$\r$\n\
#					(Buildable aurreneko aldiz abiatzean denbora piskat beharko du.)"
${LangFileString} FinishPageRun "Abiarazi Buildable"

${LangFileString} UnNotInRegistryLabel "Ezin da Buildable aurkitu erregistroan.$\r$\n\
					Mahaigaineko eta Hasiera menuko lasterbideak ez dira kenduko."
${LangFileString} UnInstallRunning "Aurrenik Buildable itxi behar duzu."
${LangFileString} UnNotAdminLabel "Administratzailearen baimenak behar dituzu Buildable desinstalatzeko."
${LangFileString} UnReallyRemoveLabel "Ziur zaude Buildable eta bere osagai guztiak kentzea nahi dituzula??"
${LangFileString} UnBuildablePreferencesTitle 'Buildable-eko erabiltzailearen hobespenak'

#${LangFileString} SecUnProgDescription "xxx kudeatzailea desinstalatzen du."
${LangFileString} SecUnPreferencesDescription 'Buildable-en konfigurazioa ezabatzen du$\r$\n\
						($\"$AppPre\erabiltzailea\$\r$\n\
						$AppSuff\$\r$\n\
						\${APP_DIR_USERDATA}$\"$\r$\n\
						zuretzako edo erabiltzaile guztientzako (administratzailea bazara).'
${LangFileString} DialogUnPreferences 'You chose to delete the Buildables user configuration.$\r$\n\
						This will also delete all installed Buildable addons.$\r$\n\
						Do you agree with this?'
${LangFileString} SecUnProgramFilesDescription "Desinstalatu Buildable eta bere osagai guztiak."
