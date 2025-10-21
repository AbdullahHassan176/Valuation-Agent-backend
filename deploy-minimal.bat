@echo off
echo 🚀 Minimal Azure Deployment Script
echo ================================

echo 📦 Creating minimal deployment package...
cd backend

echo 📁 Creating deployment directory...
if exist deploy-temp rmdir /s /q deploy-temp
mkdir deploy-temp

echo 📋 Copying essential files...
copy simple_app.py deploy-temp\
copy main.py deploy-temp\
copy startup_minimal.py deploy-temp\
copy requirements-ultra-minimal.txt deploy-temp\requirements.txt
copy mongodb_client.py deploy-temp\
copy quantlib_valuation.py deploy-temp\

echo 📦 Creating deployment ZIP...
cd deploy-temp
powershell Compress-Archive -Path * -DestinationPath ..\deployment-minimal.zip -Force
cd ..

echo ✅ Minimal deployment package created: deployment-minimal.zip
echo.
echo 📋 Next steps:
echo 1. Go to Azure Portal → App Services → valuation-backend
echo 2. Deployment Center → Manual deployment
echo 3. Upload deployment-minimal.zip
echo 4. Set startup command: python startup_minimal.py
echo 5. Restart the app
echo.
echo 🧪 Test endpoints after deployment:
echo - GET /healthz
echo - GET /api/valuation/xva-options
echo - POST /api/valuation/runs
echo.
pause
