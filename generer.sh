#!/bin/sh
# Génère les decks Anki (japonais_fr.apkg et japonais_conjugaison_fr.apkg).
# Crée l'environnement Python au premier lancement. Usage : ./generer.sh
set -e
cd "$(dirname "$0")"

if [ ! -x python/bin/python ]; then
  echo "Premier lancement : installation de l'environnement Python..."
  python3 -m venv python
  python/bin/pip install --quiet -r requirements.txt
fi

python/bin/python cardgen/generate_vocabulary_deck.py | tail -n 2
python/bin/python cardgen/generate_verb_deck.py | grep -v '^Loading' || true
python/bin/python cardgen/export_json.py | grep -E '^(Version|Output)'

echo
echo "Terminé. Importez dans Anki (Fichier > Importer) :"
echo "  $(pwd)/japonais_fr.apkg"
echo "  $(pwd)/japonais_conjugaison_fr.apkg"
