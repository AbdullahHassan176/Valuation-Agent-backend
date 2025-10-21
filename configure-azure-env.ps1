# PowerShell script to configure Azure App Service environment variables
# Run this after setting up your Azure CLI and logging in

Write-Host "🔧 Configuring Azure App Service Environment Variables..." -ForegroundColor Green

# Set your Azure App Service name
$appName = "valuation-backend-ephph9gkdjcca0c0"
$resourceGroup = "personal-sites"  # Update this to your resource group

Write-Host "📝 Setting environment variables for app: $appName" -ForegroundColor Yellow

# Configure environment variables
az webapp config appsettings set --resource-group $resourceGroup --name $appName --settings `
    OPENAI_API_KEY="your_actual_openai_api_key_here" `
    OPENAI_MODEL="gpt-4o-mini" `
    OPENAI_EMBED_MODEL="text-embedding-3-large" `
    LLM_TEMPERATURE="0.1" `
    MAX_OUTPUT_TOKENS="1024" `
    POC_ENABLE_IFRS="true" `
    POC_ENABLE_PARSE="true" `
    POC_ENABLE_EXPLAIN="true" `
    PORT="8000" `
    FRONTEND_ORIGIN="https://your-frontend-app.azurestaticapps.net"

Write-Host "✅ Environment variables configured!" -ForegroundColor Green
Write-Host "⚠️  Remember to replace 'your_actual_openai_api_key_here' with your real OpenAI API key!" -ForegroundColor Red




