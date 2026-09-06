#!/usr/bin/env bash
set -euo pipefail

# Replace every value below with your real account credentials before running.
# Do not commit this file with real secrets.

export AZURE_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
export AZURE_LOCATION="eastus"
export RESOURCE_GROUP="creovanta-rg"
export APP_PLAN="creovanta-plan"
export WEBAPP_NAME="creovanta-your-unique-name"
export APP_URL="https://creovanta-your-unique-name.azurewebsites.net"

export SECRET_KEY="replace-with-64-char-random-secret"
export OPENAI_API_KEY="sk-proj-..."
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_PUBLISHABLE_KEY="pk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."

az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

az group create --name "$RESOURCE_GROUP" --location "$AZURE_LOCATION"
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
    APP_URL="$APP_URL" \
    SECRET_KEY="$SECRET_KEY" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    STRIPE_SECRET_KEY="$STRIPE_SECRET_KEY" \
    STRIPE_PUBLISHABLE_KEY="$STRIPE_PUBLISHABLE_KEY" \
    STRIPE_WEBHOOK_SECRET="$STRIPE_WEBHOOK_SECRET" \
    SESSION_COOKIE_SECURE=True \
    PREFERRED_URL_SCHEME=https

echo "Azure app created: https://$WEBAPP_NAME.azurewebsites.net"
echo "Set your Stripe webhook to: https://$WEBAPP_NAME.azurewebsites.net/api/stripe/webhook"
