# GitHub Secrets Setup for Azure App Service Deployment

## Required GitHub Secrets

You need to add these secrets to your GitHub repository:

### 1. Azure App Service Secrets
- **`AZURE_WEBAPP_NAME`**: Your App Service name (e.g., `valuation-backend`)
- **`AZURE_RESOURCE_GROUP`**: Your Azure resource group (e.g., `valuation-rg`)
- **`AZURE_WEBAPP_PUBLISH_PROFILE`**: Publish profile content (see below)

### 2. Database Secret
- **`DATABASE_URL`**: PostgreSQL connection string

### 3. API Keys
- **`OPENAI_API_KEY`**: Your OpenAI API key

## How to Get These Values

### 1. Get App Service Name and Resource Group
```bash
# Run the deployment script first, or check Azure Portal
az webapp list --output table
```

### 2. Get Publish Profile
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your App Service
3. Click "Get publish profile" in the Overview section
4. Download the `.PublishSettings` file
5. Open the file in a text editor
6. Copy the entire content (it's XML)

### 3. Get Database Connection String
```bash
az postgres flexible-server show-connection-string \
  --server-name your-db-name \
  --admin-user dbadmin \
  --admin-password your-password \
  --database-name valuation_db \
  --query connectionStrings.psql \
  --output tsv
```

### 4. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com)
2. Navigate to API Keys
3. Create a new secret key
4. Copy the key (starts with `sk-`)

## Adding Secrets to GitHub

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with the exact name and value

## Example Secret Values

```
AZURE_WEBAPP_NAME=valuation-backend
AZURE_RESOURCE_GROUP=valuation-rg
DATABASE_URL=postgresql://dbadmin:YourPassword@valuation-db.postgres.database.azure.com:5432/valuation_db
OPENAI_API_KEY=sk-your-actual-openai-key-here
AZURE_WEBAPP_PUBLISH_PROFILE=<XML content from .PublishSettings file>
```

## Testing the Setup

After adding all secrets:

1. Push to the `main` branch
2. Check the **Actions** tab in GitHub
3. The deployment should start automatically
4. Check the logs for any errors

## Troubleshooting

### Common Issues

1. **"Publish profile not found"**
   - Make sure you downloaded the correct publish profile
   - Check that the App Service exists

2. **"Database connection failed"**
   - Verify the DATABASE_URL is correct
   - Check that the database server is running

3. **"OpenAI API key invalid"**
   - Verify the API key is correct
   - Check that you have credits in your OpenAI account

### Checking Deployment Status

```bash
# Check App Service logs
az webapp log tail --resource-group valuation-rg --name valuation-backend

# Check App Service status
az webapp show --resource-group valuation-rg --name valuation-backend --query state
```

## Cost Management

- **App Service Plan (B1)**: ~$13/month
- **PostgreSQL Flexible Server (B1ms)**: ~$25/month
- **Total**: ~$38/month

To reduce costs:
- Use **F1** plan for development (free)
- Use **Basic** database tier
- Stop resources when not in use
