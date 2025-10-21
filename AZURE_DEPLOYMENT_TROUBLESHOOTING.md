# Azure Deployment Troubleshooting Guide

## 🚨 Current Issue: 409 Conflict Error

### **Immediate Actions Required:**

#### **Step 1: Azure Portal Actions**
1. **Go to Azure Portal** → App Services → `valuation-backend`
2. **Check Status**: Look for "Unhealthy", "Stopped", or error states
3. **Restart App Service**: Click "Restart" button
4. **Wait 3-5 minutes** for complete restart
5. **Check Logs**: Go to Monitoring → Log stream for errors

#### **Step 2: GitHub Actions Cleanup**
1. **Go to GitHub** → Repository → Actions tab
2. **Cancel any running workflows** (if any)
3. **Wait 5 minutes** before retrying deployment
4. **Check for stuck deployments** in the queue

#### **Step 3: Alternative Deployment Methods**

**Option A: Manual Deployment**
1. Download latest code from GitHub
2. Azure Portal → App Service → Deployment Center
3. Choose "Local Git" or "ZIP Deploy"
4. Upload code directly

**Option B: Azure CLI Deployment**
```bash
# If you have Azure CLI installed
az webapp deployment source config-zip --name valuation-backend --resource-group your-resource-group --src your-code.zip
```

**Option C: Minimal Dependencies**
1. Use `requirements-ultra-minimal.txt` instead of `requirements.txt`
2. Use `startup_minimal.py` as startup command
3. This removes MongoDB and QuantLib dependencies

### **🔧 Configuration Changes:**

#### **App Service Settings to Update:**
1. **Startup Command**: `python startup_minimal.py`
2. **Python Version**: 3.9 or 3.10
3. **Always On**: Enable
4. **SCM_DO_BUILD_DURING_DEPLOYMENT**: True

#### **Environment Variables:**
```
WEBSITES_PORT=8000
WEBSITES_ENABLE_APP_SERVICE_STORAGE=true
SCM_DO_BUILD_DURING_DEPLOYMENT=true
```

### **📊 Testing After Fix:**

#### **Health Check Endpoints:**
- `GET /healthz` - Basic health check
- `GET /` - Root endpoint
- `GET /api/valuation/runs` - Test runs endpoint

#### **XVA Testing:**
- `GET /api/valuation/xva-options` - XVA options
- `POST /api/valuation/runs` - Create run with XVA

### **🚀 Deployment Strategies:**

#### **Strategy 1: Minimal Dependencies (Recommended)**
- Use `requirements-ultra-minimal.txt`
- Use `startup_minimal.py`
- Gradual feature enablement

#### **Strategy 2: Staged Deployment**
- Deploy basic functionality first
- Add MongoDB integration after basic deployment works
- Add QuantLib after MongoDB is stable

#### **Strategy 3: Alternative Platform**
- Consider Azure Container Instances
- Use Docker deployment
- More control over dependencies

### **📞 Support Actions:**

1. **Check Azure Status Page**: https://status.azure.com/
2. **Azure Support**: Create support ticket if issue persists
3. **GitHub Issues**: Check for known deployment issues
4. **Community Forums**: Azure App Service troubleshooting

### **🔍 Common 409 Error Causes:**

1. **App Service Stuck**: Restart usually fixes
2. **Resource Locks**: Check for locks in Resource Group
3. **Concurrent Deployments**: Cancel other deployments
4. **Dependency Conflicts**: Use minimal requirements
5. **Network Issues**: Check Azure connectivity

### **✅ Success Indicators:**

- App Service status: "Running"
- Health endpoint returns 200
- No errors in log stream
- Deployment completes without 409 error
- XVA endpoints respond correctly

### **🔄 Next Steps After Fix:**

1. **Verify Basic Functionality**: Test health endpoints
2. **Test XVA Features**: Create runs with XVA selection
3. **Monitor Performance**: Check logs for any issues
4. **Gradual Enhancement**: Add features incrementally
5. **Documentation**: Update deployment procedures

