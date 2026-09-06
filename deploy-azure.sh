#!/usr/bin/env bash
set -euo pipefail

# Usage:
# 1) export your real values before running
#    export AZURE_SUBSCRIPTION_ID="..."
#    export AZURE_LOCATION="eastus"
#    export RESOURCE_GROUP="creovanta-rg"
#    export APP_PLAN="creovanta-plan"
#    export WEBAPP_NAME="creovanta-<unique-name>"
#    export SECRET_KEY="<random-64-char-secret>"
#    export OPENAI_API_KEY="<sk-...>"
#    export STRIPE_SECRET_KEY="<sk_live_... or sk_test_...>"
#    export STRIPE_WEBHOOK_SECRET="<whsec_...>"
#
# 2) run: bash deploy-azure.sh

az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

az group create \
  --name "$RESOURCE_GROUP" \
  --location "$AZURE_LOCATION"

az appservice plan create \
  --name "$APP_PLAN" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$AZURE_LOCATION" \
  --is-linux \
  --sku B1

az webapp create \
  --resource-group "$RESOURCE_GROUP" \
  --plan "$APP_PLAN" \
  --name "$WEBAPP_NAME" \
  --runtime "PYTHON|3.12"

az webapp config set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --startup-file "gunicorn --bind=0.0.0.0:8000 app:app"

az webapp config appsettings set \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --settings \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    ENABLE_ORYX_BUILD=true \
    WEBSITES_PORT=8000 \
    PORT=8000 \
    FLASK_ENV=production \
    SECRET_KEY="$SECRET_KEY" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" \
    STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET" \
    SESSION_COOKIE_SECURE=True \
    PREFERRED_URL_SCHEME=https

git add .
git commit -m "Prepare Creovanta production deployment" || true

git remote -v | grep -q "azure" || git remote add azure "https://$WEBAPP_NAME.scm.azurewebsites.net:443/$WEBAPP_NAME.git"

git push azure HEAD:main

echo "Deployment started. Once the push is complete, browse: https://$WEBAPP_NAME.azurewebsites.net"
