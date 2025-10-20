# Azure App Service Configuration Update

## Manual Steps Required

Since the GitHub Actions deployment is working but the startup command needs to be updated in Azure Portal:

### 1. Update Startup Command in Azure Portal

1. Go to your Azure App Service: `valuation-backend`
2. Navigate to **Configuration** → **General settings**
3. In the **Startup command** field, change from:
   ```
   startup.py
   ```
   to:
   ```
   python startup_immediate.py
   ```
4. Click **Save**

### 2. Alternative: Use Application Settings

You can also set the startup command via Application Settings:

1. Go to **Configuration** → **Application settings**
2. Add a new setting:
   - **Name**: `WEBSITE_STARTUP_COMMAND`
   - **Value**: `python startup_immediate.py`
3. Click **Save**

### 3. Verify Python Stack

Make sure your App Service is configured for:
- **Stack**: Python
- **Version**: Python 3.11

### 4. Test the Deployment

After updating the startup command, the deployment should work. The server will:
- Write startup logs to `/tmp/startup.log`
- Print immediate output to stdout
- Start the HTTP server on the configured port

### 5. Health Check

Once deployed, test with:
```bash
curl https://valuation-backend-ephph9gkdjcca0c0.canadacentral-01.azurewebsites.net/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "service": "valuation-backend",
  "version": "1.0.0",
  "timestamp": 1234567890.123
}
```



