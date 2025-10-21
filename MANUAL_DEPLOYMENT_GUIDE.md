# Manual Azure Deployment Guide

## 🚨 Bypass GitHub Actions 409 Error

### **Method 1: Azure Portal ZIP Deploy**

#### **Step 1: Prepare Deployment Package**
1. **Download latest code** from GitHub repository
2. **Extract ZIP file** to local directory
3. **Navigate to backend folder**
4. **Create new ZIP** with backend contents only

#### **Step 2: Azure Portal Deployment**
1. **Azure Portal** → **App Services** → **valuation-backend**
2. **Deployment Center** → **Manual deployment**
3. **Choose "ZIP Deploy"**
4. **Upload your ZIP file**
5. **Wait for deployment** (2-3 minutes)

#### **Step 3: Configure App Settings**
1. **Configuration** → **Application settings**
2. **Add/Update these settings:**
   ```
   WEBSITES_PORT=8000
   WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
   SCM_DO_BUILD_DURING_DEPLOYMENT=true
   PYTHONPATH=/home/site/wwwroot
   ```
3. **Save** and **Restart** app

### **Method 2: Azure CLI Deployment**

#### **Prerequisites:**
```bash
# Install Azure CLI
az login
az account set --subscription "your-subscription-id"
```

#### **Deploy Command:**
```bash
# Create deployment package
cd backend
zip -r deployment.zip .

# Deploy to Azure
az webapp deployment source config-zip \
  --name valuation-backend \
  --resource-group your-resource-group \
  --src deployment.zip
```

### **Method 3: Local Git Deployment**

#### **Setup Local Git:**
```bash
# Initialize local git
git init
git add .
git commit -m "Initial deployment"

# Add Azure remote
git remote add azure https://valuation-backend.scm.azurewebsites.net:443/valuation-backend.git

# Deploy
git push azure main
```

### **Method 4: FTP Deployment**

#### **Get FTP Credentials:**
1. **Azure Portal** → **App Service** → **Deployment Center**
2. **Local Git** → **Show deployment credentials**
3. **Note FTP hostname, username, password**

#### **Upload Files:**
1. **Use FTP client** (FileZilla, WinSCP)
2. **Connect to FTP hostname**
3. **Upload all backend files** to `/site/wwwroot/`
4. **Restart app** in Azure Portal

### **🔧 Configuration After Manual Deployment**

#### **Required App Settings:**
```
WEBSITES_PORT=8000
WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
SCM_DO_BUILD_DURING_DEPLOYMENT=true
PYTHONPATH=/home/site/wwwroot
```

#### **Optional Environment Variables:**
```
MONGODB_CONNECTION_STRING=your-connection-string
MONGODB_DATABASE=valuation-backend-server
GROQ_API_KEY=your-groq-key
OPENAI_API_KEY=your-openai-key
```

#### **Startup Command:**
```
python main.py
```

### **🧪 Testing After Manual Deployment**

#### **Health Checks:**
1. **Root endpoint**: `GET /`
2. **Health endpoint**: `GET /healthz`
3. **Runs endpoint**: `GET /api/valuation/runs`

#### **XVA Testing:**
1. **XVA options**: `GET /api/valuation/xva-options`
2. **Create run with XVA**: `POST /api/valuation/runs`

#### **Expected Responses:**
- **200 OK** for all endpoints
- **JSON responses** with proper data
- **No 500 errors** in logs

### **🚀 Troubleshooting Manual Deployment**

#### **If Still Failing:**
1. **Check Azure logs** for specific errors
2. **Verify Python version** (3.9 or 3.10)
3. **Check requirements.txt** compatibility
4. **Try minimal requirements** first

#### **Fallback Options:**
1. **Use startup_minimal.py** as startup command
2. **Use requirements-ultra-minimal.txt**
3. **Deploy basic functionality first**
4. **Add features incrementally**

### **✅ Success Indicators**

- **App Service status**: "Running"
- **Health endpoint**: Returns 200 OK
- **No errors** in log stream
- **XVA endpoints** respond correctly
- **Database operations** work (if MongoDB configured)

### **📞 Support Escalation**

If manual deployment still fails:
1. **Azure Support Ticket**: Create support case
2. **Check Azure Status**: https://status.azure.com/
3. **Community Forums**: Azure App Service troubleshooting
4. **Alternative Platform**: Consider Azure Container Instances
