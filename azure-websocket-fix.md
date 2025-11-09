# Azure WebSocket Configuration Fix

## Problem
WebSocket connections fail because Azure App Service doesn't enable WebSockets by default.

## Solution 1: Enable WebSockets in Azure Portal
1. Go to Azure Portal → Your App Service → Configuration → General Settings
2. Set "Web sockets" to "On" 
3. Click "Save" and restart the app

## Solution 2: Use Azure CLI
```bash
az webapp config set --name laserclouding-hva2gweudafvadcw --resource-group <your-resource-group> --web-sockets-enabled true
```

## Solution 3: Alternative - Use Polling Instead of WebSockets
If WebSockets continue to fail, modify the app to use HTTP polling for real-time updates.