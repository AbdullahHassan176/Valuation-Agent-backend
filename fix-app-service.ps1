# Fix Azure App Service Runtime to Python
Write-Host "🔧 Fixing App Service runtime to Python..."

# Set the runtime to Python 3.11
az webapp config set `
  --resource-group personal-sites `
  --name valuation-backend `
  --linux-fx-version "PYTHON|3.11"

Write-Host "✅ App Service runtime updated to Python 3.11"

# Set startup command
az webapp config set `
  --resource-group personal-sites `
  --name valuation-backend `
  --startup-file "startup.py"

Write-Host "✅ Startup file set to startup.py"

# Get the app URL
$appUrl = az webapp show --resource-group personal-sites --name valuation-backend --query defaultHostName --output tsv
Write-Host "App URL: $appUrl"
