# 🚀 Azure Manual Configuration - FINAL FIX

## Problem
The backend keeps timing out because Azure is running the server as a **deployment command** instead of a **startup command**.

## Solution
Manually configure the Azure App Service startup command in the Azure Portal.

---

## Step-by-Step Instructions

### 1. Go to Azure Portal
Navigate to: https://portal.azure.com

### 2. Find Your App Service
- Search for "valuation-backend" (or your app service name)
- Click on your App Service

### 3. Configure Startup Command
1. In the left menu, go to **Settings** → **Configuration**
2. Click on the **General settings** tab
3. In the **Startup Command** field, enter:
   ```
   python3 startup_working.py
   ```
4. Click **Save** at the top
5. Click **Continue** when prompted about restarting the app

### 4. Restart the App Service
1. Go back to the **Overview** page
2. Click **Restart** at the top
3. Wait 30-60 seconds for the restart

### 5. Test the Backend
Open your browser or use curl to test:
```
https://valuation-backend.azurewebsites.net/healthz
```

You should see:
```json
{
  "status": "healthy",
  "service": "valuation-backend",
  "version": "1.0.0"
}
```

---

## What This Does

The `startup_working.py` file creates a simple HTTP server with:

- **GET /** - API info
- **GET /healthz** - Health check
- **GET /api/valuation/runs** - List valuation runs (mock data)
- **GET /api/valuation/curves** - List curves (mock data)
- **POST /poc/chat** - Chat endpoint for AI agent

---

## Why This Works

1. **No external dependencies** - Uses only Python standard library
2. **Immediate output** - Prints logs immediately, preventing timeout
3. **Simple HTTP server** - No complex frameworks like FastAPI/uvicorn
4. **CORS enabled** - Frontend can connect from Azure Static Web Apps

---

## After This Works

Once the backend is running, the AI agent in your frontend will automatically connect and work properly!
