#!/bin/sh
# Met en ligne l'application (app/) sur l'hébergement OVH. Usage : ./deploy.sh
# Réglages dans deploy.env, non versionné (voir deploy.env.example).
set -e
cd "$(dirname "$0")"

if [ ! -f deploy.env ]; then
  echo "Il manque deploy.env : copiez deploy.env.example et complétez-le."
  exit 1
fi
. ./deploy.env
if [ -z "$HACHI_SSH" ] || [ -z "$HACHI_DIR" ]; then
  echo "deploy.env doit définir HACHI_SSH et HACHI_DIR."
  exit 1
fi

# rsync --delete efface ce qui n'est pas dans l'app : on vérifie d'abord que le dossier
# distant est vide ou contient déjà l'app (fichier .hachi).
if ! ssh "$HACHI_SSH" "mkdir -p '$HACHI_DIR' && cd '$HACHI_DIR' && { [ -f .hachi ] || [ -z \"\$(ls -A)\" ]; }"; then
  echo "Le dossier $HACHI_DIR n'est pas vide et ne contient pas l'app : rien n'a été envoyé."
  exit 1
fi

./generer.sh
(cd app && npm test && npm run build)

# api/ (phase D) et config.php sont gérés à part : rsync ne les touche pas.
rsync -rlptvz --delete --exclude /api/ --exclude /config.php app/dist/ "$HACHI_SSH:$HACHI_DIR/"
echo
echo "En ligne : https://hachi.guepe.com"
