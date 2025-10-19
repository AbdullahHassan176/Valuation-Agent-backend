# Backend Azure Deployment Guide

This guide explains how to deploy the backend to Azure using different approaches.

## Option 1: Azure Container Instances (Recommended)

### Prerequisites
1. Azure Container Registry (ACR)
2. Azure Resource Group
3. GitHub Secrets configured

### Required GitHub Secrets
- `AZURE_CONTAINER_REGISTRY`: Your ACR name (e.g., `myregistry`)
- `ACR_USERNAME`: ACR username
- `ACR_PASSWORD`: ACR password
- `AZURE_RESOURCE_GROUP`: Resource group name
- `AZURE_LOCATION`: Azure region (e.g., `eastus`)
- `OPENAI_API_KEY`: Your OpenAI API key

### Deployment Steps
1. The GitHub Actions workflow will automatically:
   - Build Docker image
   - Push to Azure Container Registry
   - Deploy to Azure Container Instances
   - Configure environment variables

### Accessing the Backend
After deployment, you'll get a public URL like:
`http://valuation-backend-123.eastus.azurecontainer.io:8000`

## Option 2: Azure App Service

### Prerequisites
1. Azure App Service (Python 3.11)
2. GitHub Secrets configured

### Required GitHub Secrets
- `AZURE_WEBAPP_NAME`: Your App Service name
- `AZURE_WEBAPP_PUBLISH_PROFILE`: Publish profile (download from Azure Portal)
- `OPENAI_API_KEY`: Your OpenAI API key

### Deployment Steps
1. Create an Azure App Service with Python 3.11
2. Download the publish profile
3. Add secrets to GitHub
4. Push to main branch to trigger deployment

## Option 3: Azure Static Web Apps (Limited)

Azure Static Web Apps is primarily for static sites, but can host simple Python APIs.

### Configuration
- App location: `/`
- API location: (empty)
- Output location: (empty)

### Limitations
- Limited Python support
- No persistent storage
- Cold start delays

## Environment Variables

All deployment options require these environment variables:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
POC_ENABLE_IFRS=true
POC_ENABLE_PARSE=true
POC_ENABLE_EXPLAIN=true
PORT=8000
```

## Testing the Deployment

After deployment, test these endpoints:

1. **Health Check**: `GET /healthz`
2. **Chat**: `POST /poc/chat`
3. **IFRS Ask**: `POST /poc/ifrs-ask`
4. **Parse Contract**: `POST /poc/parse-contract`
5. **Explain Run**: `POST /poc/explain-run`

## Troubleshooting

### Common Issues
1. **Module not found**: Ensure all dependencies are in `requirements-azure.txt`
2. **Port binding**: Check that the app binds to `0.0.0.0:8000`
3. **Environment variables**: Verify all required env vars are set
4. **CORS issues**: Ensure CORS is configured for your frontend domain

### Logs
- **Container Instances**: Use `az container logs`
- **App Service**: Check Application Insights or Log Stream
- **Static Web Apps**: Check Azure Portal logs

## Recommended Approach

For production use, **Azure Container Instances** is recommended because:
- Full control over the environment
- Easy scaling
- Cost-effective
- Simple deployment
- Good performance

For development/testing, **Azure App Service** is easier to set up.
