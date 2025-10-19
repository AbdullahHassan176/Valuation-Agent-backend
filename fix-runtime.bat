@echo off
echo Fixing App Service runtime to Python...

az webapp config set --resource-group personal-sites --name valuation-backend --linux-fx-version "PYTHON|3.11"

echo Setting startup file...
az webapp config set --resource-group personal-sites --name valuation-backend --startup-file "startup.py"

echo Done!
