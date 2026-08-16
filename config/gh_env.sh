#!/usr/bin/env bash
set -euo pipefail

REPO="Jack-cky/Bet-Simulator"
ENVIRONMENT="prod-pipeline"
ENV_FILE="config/.env"

gh auth status >/dev/null || gh auth login

gh api \
  --method PUT \
  "repos/${REPO}/environments/${ENVIRONMENT}"

gh secret set \
  --repo "$REPO" \
  --env "$ENVIRONMENT" \
  --env-file "$ENV_FILE"

echo "Environment and secrets configured successfully."
