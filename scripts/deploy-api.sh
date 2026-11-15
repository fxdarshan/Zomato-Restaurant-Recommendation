#!/bin/sh
# Deploys the API to its Vercel project, zomato-concierge-api, from this checkout.
# The upload is assembled in a temporary folder with only what the function needs: api/index.py,
# src/, the cleaned dataset, deploy/api/requirements.txt and deploy/api/vercel.json.
# Run from anywhere: sh scripts/deploy-api.sh (the first run links the project).
set -eu
cd "$(dirname "$0")/.."

if [ ! -f data/processed/zomato_cleaned.parquet ]; then
  echo "data/processed/zomato_cleaned.parquet is missing." >&2
  exit 1
fi

upload=$(mktemp -d)
trap 'rm -rf "$upload"' EXIT
mkdir -p "$upload/api" "$upload/data/processed" "$upload/.vercel"
cp api/index.py "$upload/api/"
cp -r src "$upload/"
find "$upload/src" -name __pycache__ -type d -prune -exec rm -rf {} +
cp data/processed/zomato_cleaned.parquet "$upload/data/processed/"
cp deploy/api/requirements.txt deploy/api/vercel.json "$upload/"
if [ -f .vercel/project.json ]; then
  cp .vercel/project.json "$upload/.vercel/"
fi

npx --yes vercel@65.16.0 deploy --prod --yes --cwd "$upload" ${VERCEL_TOKEN:+--token "$VERCEL_TOKEN"}
