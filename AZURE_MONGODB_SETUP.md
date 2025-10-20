# Azure Cosmos DB for MongoDB Setup Guide

## Prerequisites
- Azure Cosmos DB for MongoDB account
- Connection string from Azure portal

## Step 1: Create Azure Cosmos DB for MongoDB Account

1. Go to Azure Portal
2. Create a new resource
3. Search for "Azure Cosmos DB"
4. Select "Azure Cosmos DB for MongoDB"
5. Choose your subscription and resource group
6. Create the account

## Step 2: Get Connection String

1. Go to your Cosmos DB account
2. Navigate to "Connection String" in the left menu
3. Copy the "Primary Connection String"
4. It should look like:
   ```
   mongodb://your-account:your-key@your-account.mongo.cosmos.azure.com:10255/?ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000&appName=@your-account@
   ```

## Step 3: Configure Azure App Service

### Option A: Using Azure Portal
1. Go to your App Service (valuation-backend-ephph9gkdjcca0c0)
2. Navigate to "Configuration" > "Application settings"
3. Add new setting:
   - **Name**: `MONGODB_CONNECTION_STRING`
   - **Value**: Your connection string from Step 2
4. Add another setting:
   - **Name**: `MONGODB_DATABASE`
   - **Value**: `valuation_db`
5. Click "Save"

### Option B: Using Azure CLI
```bash
az webapp config appsettings set --name valuation-backend-ephph9gkdjcca0c0 --resource-group your-resource-group --settings MONGODB_CONNECTION_STRING="your-connection-string"
az webapp config appsettings set --name valuation-backend-ephph9gkdjcca0c0 --resource-group your-resource-group --settings MONGODB_DATABASE="valuation_db"
```

## Step 4: Restart App Service

1. Go to your App Service
2. Click "Restart" to apply the new environment variables
3. Wait for the restart to complete

## Step 5: Verify Connection

1. Go to your test page: https://www.irshadsucks.com/test-backend-connection.html
2. Click "🗄️ Test Database Status"
3. You should see:
   - Database Type: MongoDB (Azure Cosmos DB)
   - Database Name: valuation_db
   - Total Runs: 0 (initially)
   - Message: "Data is stored in Azure Cosmos DB and visible in Data Explorer"

## Step 6: View Data in Azure Data Explorer

1. Go to your Cosmos DB account in Azure Portal
2. Click "Data Explorer" in the left menu
3. You should see:
   - Database: `valuation_db`
   - Collections: `runs`, `curves`
4. Click on `runs` collection to see your valuation runs
5. Click on `curves` collection to see yield curve data

## Troubleshooting

### Connection Issues
- Verify the connection string is correct
- Check that the App Service has been restarted
- Ensure the Cosmos DB account is accessible

### Data Not Appearing
- Check the database name matches (`valuation_db`)
- Verify the collections are created (`runs`, `curves`)
- Check the App Service logs for errors

### Performance Issues
- Consider increasing the RU (Request Units) for your Cosmos DB account
- Monitor the usage in Azure Portal

## Environment Variables Summary

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGODB_CONNECTION_STRING` | Cosmos DB connection string | `mongodb://account:key@account.mongo.cosmos.azure.com:10255/?ssl=true` |
| `MONGODB_DATABASE` | Database name | `valuation_db` |

## Next Steps

Once configured, all valuation runs will be stored in Azure Cosmos DB and visible in the Data Explorer. The runs page will automatically display data from MongoDB instead of localStorage.
