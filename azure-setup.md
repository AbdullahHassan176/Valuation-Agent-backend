# Azure App Service + Database Setup

## Prerequisites
- Azure CLI installed
- GitHub repository with backend code
- OpenAI API key

## Step 1: Create Azure Resources

### 1.1 Create Resource Group
```bash
az group create --name valuation-rg --location eastus
```

### 1.2 Create PostgreSQL Database
```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group valuation-rg \
  --name valuation-db \
  --location eastus \
  --admin-user dbadmin \
  --admin-password YourSecurePassword123! \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --public-access 0.0.0.0-255.255.255.255 \
  --storage-size 32

# Create database
az postgres flexible-server db create \
  --resource-group valuation-rg \
  --server-name valuation-db \
  --database-name valuation_db
```

### 1.3 Create App Service Plan
```bash
az appservice plan create \
  --name valuation-plan \
  --resource-group valuation-rg \
  --sku B1 \
  --is-linux
```

### 1.4 Create App Service
```bash
az webapp create \
  --resource-group valuation-rg \
  --plan valuation-plan \
  --name valuation-backend \
  --runtime "PYTHON|3.11"
```

## Step 2: Configure Database Connection

### 2.1 Get Database Connection String
```bash
# Get connection string
az postgres flexible-server show-connection-string \
  --server-name valuation-db \
  --admin-user dbadmin \
  --admin-password YourSecurePassword123! \
  --database-name valuation_db
```

### 2.2 Set App Service Configuration
```bash
# Set environment variables
az webapp config appsettings set \
  --resource-group valuation-rg \
  --name valuation-backend \
  --settings \
    DATABASE_URL="postgresql://dbadmin:YourSecurePassword123!@valuation-db.postgres.database.azure.com:5432/valuation_db" \
    OPENAI_API_KEY="your_openai_api_key_here" \
    OPENAI_MODEL="gpt-4o-mini" \
    POC_ENABLE_IFRS="true" \
    POC_ENABLE_PARSE="true" \
    POC_ENABLE_EXPLAIN="true"
```

## Step 3: Deploy Code

### 3.1 Enable GitHub Actions
The GitHub Actions workflow will automatically deploy when you push to main branch.

### 3.2 Manual Deployment (Alternative)
```bash
# Deploy using Azure CLI
az webapp deployment source config \
  --resource-group valuation-rg \
  --name valuation-backend \
  --repo-url https://github.com/yourusername/your-backend-repo \
  --branch main \
  --manual-integration
```

## Step 4: Test Deployment

### 4.1 Check App Service Logs
```bash
az webapp log tail --resource-group valuation-rg --name valuation-backend
```

### 4.2 Test Endpoints
- Health: `https://valuation-backend.azurewebsites.net/healthz`
- Chat: `https://valuation-backend.azurewebsites.net/poc/chat`

## Step 5: Update Frontend Configuration

Update your frontend `api-config.ts`:
```typescript
// Production - use Azure App Service
if (window.location.hostname.includes('azurestaticapps.net')) {
  return 'https://valuation-backend.azurewebsites.net';
}
```

## Cost Estimation
- **App Service Plan (B1)**: ~$13/month
- **PostgreSQL Flexible Server (B1ms)**: ~$25/month
- **Total**: ~$38/month

## Security Notes
- Database is accessible only from Azure services
- App Service has managed identity
- Environment variables are encrypted
- HTTPS is enabled by default
