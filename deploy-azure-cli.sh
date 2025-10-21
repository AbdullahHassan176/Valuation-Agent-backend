#!/bin/bash
# Azure CLI Deployment Script
# Bypass GitHub Actions 409 error

echo "🚀 Azure CLI Deployment Script"
echo "=============================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI not found. Please install it first:"
    echo "   https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "🔑 Please login to Azure..."
    az login
fi

# Set variables
RESOURCE_GROUP="your-resource-group"  # Replace with your resource group
APP_NAME="valuation-backend"
SUBSCRIPTION_ID="your-subscription-id"  # Replace with your subscription

echo "📋 Configuration:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   App Name: $APP_NAME"
echo "   Subscription: $SUBSCRIPTION_ID"

# Set subscription
az account set --subscription "$SUBSCRIPTION_ID"

# Create deployment package
echo "📦 Creating deployment package..."
cd backend
zip -r ../deployment.zip . -x "*.git*" "*.pyc" "__pycache__/*" "*.log"

# Deploy to Azure
echo "🚀 Deploying to Azure App Service..."
az webapp deployment source config-zip \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --src ../deployment.zip

# Configure app settings
echo "⚙️ Configuring app settings..."
az webapp config appsettings set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --settings \
    WEBSITES_PORT=8000 \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE=true \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    PYTHONPATH=/home/site/wwwroot

# Set startup command
echo "🔧 Setting startup command..."
az webapp config set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --startup-file "python main.py"

# Restart app
echo "🔄 Restarting app..."
az webapp restart \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP"

echo "✅ Deployment completed!"
echo ""
echo "🧪 Test your deployment:"
echo "   Health check: https://$APP_NAME.azurewebsites.net/healthz"
echo "   XVA options: https://$APP_NAME.azurewebsites.net/api/valuation/xva-options"
echo ""
echo "📊 Monitor logs:"
echo "   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP"
