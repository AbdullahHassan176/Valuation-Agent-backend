#!/bin/bash

# Azure App Service + Database Deployment Script
# This script sets up Azure resources and deploys the backend

set -e

# Configuration
RESOURCE_GROUP="valuation-rg"
LOCATION="eastus"
APP_NAME="valuation-backend"
DB_NAME="valuation-db"
DB_ADMIN="dbadmin"
DB_PASSWORD="YourSecurePassword123!"
PLAN_NAME="valuation-plan"

echo "🚀 Starting Azure deployment..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    exit 1
fi

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure login status..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure..."
    az login
fi

# Create resource group
echo "📦 Creating resource group..."
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create PostgreSQL database
echo "🗄️ Creating PostgreSQL database..."
az postgres flexible-server create \
  --resource-group $RESOURCE_GROUP \
  --name $DB_NAME \
  --location $LOCATION \
  --admin-user $DB_ADMIN \
  --admin-password $DB_PASSWORD \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0-255.255.255.255 \
  --storage-size 32

# Create database
echo "📊 Creating database..."
az postgres flexible-server db create \
  --resource-group $RESOURCE_GROUP \
  --server-name $DB_NAME \
  --database-name valuation_db

# Create App Service Plan
echo "📋 Creating App Service Plan..."
az appservice plan create \
  --name $PLAN_NAME \
  --resource-group $RESOURCE_GROUP \
  --sku B1 \
  --is-linux

# Create App Service
echo "🌐 Creating App Service..."
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $PLAN_NAME \
  --name $APP_NAME \
  --runtime "PYTHON|3.11"

# Get database connection string
echo "🔗 Getting database connection string..."
DB_CONNECTION_STRING=$(az postgres flexible-server show-connection-string \
  --server-name $DB_NAME \
  --admin-user $DB_ADMIN \
  --admin-password $DB_PASSWORD \
  --database-name valuation_db \
  --query connectionStrings.psql \
  --output tsv)

# Configure App Service settings
echo "⚙️ Configuring App Service settings..."
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $APP_NAME \
  --settings \
    DATABASE_URL="$DB_CONNECTION_STRING" \
    OPENAI_API_KEY="your_openai_api_key_here" \
    OPENAI_MODEL="gpt-4o-mini" \
    POC_ENABLE_IFRS="true" \
    POC_ENABLE_PARSE="true" \
    POC_ENABLE_EXPLAIN="true" \
    PYTHONPATH="/home/site/wwwroot"

# Get App Service URL
APP_URL=$(az webapp show --resource-group $RESOURCE_GROUP --name $APP_NAME --query defaultHostName --output tsv)

echo "✅ Deployment completed!"
echo ""
echo "📋 Summary:"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  App Service: https://$APP_URL"
echo "  Database: $DB_NAME.postgres.database.azure.com"
echo ""
echo "🔧 Next steps:"
echo "  1. Update your OpenAI API key in Azure Portal"
echo "  2. Configure GitHub Secrets:"
echo "     - AZURE_WEBAPP_NAME: $APP_NAME"
echo "     - AZURE_RESOURCE_GROUP: $RESOURCE_GROUP"
echo "     - DATABASE_URL: $DB_CONNECTION_STRING"
echo "     - OPENAI_API_KEY: your_actual_openai_key"
echo "  3. Download publish profile from Azure Portal"
echo "  4. Add AZURE_WEBAPP_PUBLISH_PROFILE to GitHub Secrets"
echo ""
echo "🌐 Your backend will be available at: https://$APP_URL"
