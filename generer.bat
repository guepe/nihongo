@echo off
rem Genere les decks Anki (japonais_fr.apkg et japonais_conjugaison_fr.apkg).
rem Cree l'environnement Python au premier lancement. Double-cliquer ou lancer : generer.bat
cd /d "%~dp0"
rem Les fichiers TOML sont en UTF-8 ; Windows lit en cp1252 par defaut.
set PYTHONUTF8=1

if not exist python\Scripts\python.exe (
  echo Premier lancement : installation de l'environnement Python...
  py -3 -m venv python || python -m venv python || goto :erreur
  python\Scripts\python.exe -m pip install --quiet -r requirements.txt || goto :erreur
)

python\Scripts\python.exe cardgen\generate_vocabulary_deck.py || goto :erreur
python\Scripts\python.exe cardgen\generate_verb_deck.py || goto :erreur

echo.
echo Termine. Importez dans Anki (Fichier ^> Importer) :
echo   %CD%\japonais_fr.apkg
echo   %CD%\japonais_conjugaison_fr.apkg
pause
exit /b 0

:erreur
echo.
echo Erreur. Python 3 est-il installe ? https://www.python.org/downloads/
pause
exit /b 1
