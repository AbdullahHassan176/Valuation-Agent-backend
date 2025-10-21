# Azure App Service Environment Variables Setup

## 🎯 **Required Environment Variables**

Your Azure App Service needs these environment variables to work properly:

### **1. OpenAI Configuration**
```
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-large
LLM_TEMPERATURE=0.1
MAX_OUTPUT_TOKENS=1024
```

### **2. Feature Flags**
```
POC_ENABLE_IFRS=true
POC_ENABLE_PARSE=true
POC_ENABLE_EXPLAIN=true
```

### **3. Server Configuration**
```
PORT=8000
FRONTEND_ORIGIN=https://your-frontend-app.azurestaticapps.net
```

## 🔧 **How to Configure**

### **Option 1: Azure Portal (Recommended)**
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to your App Service: `valuation-backend-ephph9gkdjcca0c0`
3. Go to **Settings** → **Configuration**
4. Click **+ New application setting** for each variable
5. Add all the variables above
6. Click **Save**

### **Option 2: Azure CLI**
```bash
# Login to Azure
az login

# Set environment variables
az webapp config appsettings set \
  --resource-group personal-sites \
  --name valuation-backend-ephph9gkdjcca0c0 \
  --settings \
    OPENAI_API_KEY="sk-your-actual-openai-api-key-here" \
    OPENAI_MODEL="gpt-4o-mini" \
    POC_ENABLE_IFRS="true" \
    POC_ENABLE_PARSE="true" \
    POC_ENABLE_EXPLAIN="true" \
    PORT="8000"
```

### **Option 3: PowerShell Script**
```powershell
# Run the provided script
.\configure-azure-env.ps1
```

## ⚠️ **Important Notes**

1. **Replace the OpenAI API key** with your actual key
2. **Update FRONTEND_ORIGIN** with your frontend URL
3. **Restart the App Service** after setting variables
4. **Test the endpoints** to ensure they work

## 🧪 **Test After Configuration**

```bash
# Test health endpoint
curl https://valuation-backend-ephph9gkdjcca0c0.canadacentral-01.azurewebsites.net/healthz

# Test chat endpoint (should work with OpenAI key)
curl -X POST https://valuation-backend-ephph9gkdjcca0c0.canadacentral-01.azurewebsites.net/poc/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, test message"}'
```

## 🎯 **Next Steps**

1. Configure the environment variables above
2. Test the backend endpoints
3. Update your frontend to use the backend
4. Test the full application




