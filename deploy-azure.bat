@echo off
REM Azure App Service + Database Deployment Script for Windows
REM This script sets up Azure resources and deploys the backend

echo 🚀 Starting Azure deployment...

REM Check if Azure CLI is installed
az --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Azure CLI is not installed. Please install it first.
    exit /b 1
)

REM Configuration
set RESOURCE_GROUP=valuation-rg
set LOCATION=eastus
set APP_NAME=valuation-backend
set DB_NAME=valuation-db
set DB_ADMIN=dbadmin
set DB_PASSWORD=YourSecurePassword123!
set PLAN_NAME=valuation-plan

REM Login to Azure (if not already logged in)
echo 🔐 Checking Azure login status...
az account show >nul 2>&1
if %errorlevel% neq 0 (
    echo Please login to Azure...
    az login
)

REM Create resource group
echo 📦 Creating resource group...
az group create --name %RESOURCE_GROUP% --location %LOCATION%

REM Create PostgreSQL database
echo 🗄️ Creating PostgreSQL database...
az postgres flexible-server create ^
  --resource-group %RESOURCE_GROUP% ^
  --name %DB_NAME% ^
  --location %LOCATION% ^
  --admin-user %DB_ADMIN% ^
  --admin-password %DB_PASSWORD% ^
  --sku-name Standard_B1ms ^
  --tier Burstable ^
  --public-access 0.0.0.0-255.255.255.255 ^
  --storage-size 32

REM Create database
echo 📊 Creating database...
az postgres flexible-server db create ^
  --resource-group %RESOURCE_GROUP% ^
  --server-name %DB_NAME% ^
  --database-name valuation_db

REM Create App Service Plan
echo 📋 Creating App Service Plan...
az appservice plan create ^
  --name %PLAN_NAME% ^
  --resource-group %RESOURCE_GROUP% ^
  --sku B1 ^
  --is-linux

REM Create App Service
echo 🌐 Creating App Service...
az webapp create ^
  --resource-group %RESOURCE_GROUP% ^
  --plan %PLAN_NAME% ^
  --name %APP_NAME% ^
  --runtime "PYTHON|3.11"

REM Get database connection string
echo 🔗 Getting database connection string...
for /f "tokens=*" %%i in ('az postgres flexible-server show-connection-string --server-name %DB_NAME% --admin-user %DB_ADMIN% --admin-password %DB_PASSWORD% --database-name valuation_db --query connectionStrings.psql --output tsv') do set DB_CONNECTION_STRING=%%i

REM Configure App Service settings
echo ⚙️ Configuring App Service settings...
az webapp config appsettings set ^
  --resource-group %RESOURCE_GROUP% ^
  --name %APP_NAME% ^
  --settings ^
    DATABASE_URL="%DB_CONNECTION_STRING%" ^
    OPENAI_API_KEY="your_openai_api_key_here" ^
    OPENAI_MODEL="gpt-4o-mini" ^
    POC_ENABLE_IFRS="true" ^
    POC_ENABLE_PARSE="true" ^
    POC_ENABLE_EXPLAIN="true" ^
    PYTHONPATH="/home/site/wwwroot"

REM Get App Service URL
for /f "tokens=*" %%i in ('az webapp show --resource-group %RESOURCE_GROUP% --name %APP_NAME% --query defaultHostName --output tsv') do set APP_URL=%%i

echo ✅ Deployment completed!
echo.
echo 📋 Summary:
echo   Resource Group: %RESOURCE_GROUP%
echo   App Service: https://%APP_URL%
echo   Database: %DB_NAME%.postgres.database.azure.com
echo.
echo 🔧 Next steps:
echo   1. Update your OpenAI API key in Azure Portal
echo   2. Configure GitHub Secrets:
echo      - AZURE_WEBAPP_NAME: %APP_NAME%
echo      - AZURE_RESOURCE_GROUP: %RESOURCE_GROUP%
echo      - DATABASE_URL: %DB_CONNECTION_STRING%
echo      - OPENAI_API_KEY: your_actual_openai_key
echo   3. Download publish profile from Azure Portal
echo   4. Add AZURE_WEBAPP_PUBLISH_PROFILE to GitHub Secrets
echo.
echo 🌐 Your backend will be available at: https://%APP_URL%

pause
