# Azure Deployment Fix Instructions

## Problem Summary
Your local web app works perfectly, but Azure shows "Offline" because:
1. WebSockets are disabled in Azure App Service
2. The frontend assumes offline when WebSocket fails
3. The app doesn't fallback gracefully to HTTP mode

## Step 1: Deploy Updated Code

Run this in your terminal:

```bash
git add .
git commit -m "Fix WebSocket issues - add HTTP fallback mode"
git push origin master
```

## Step 2: Enable WebSockets in Azure (CRITICAL)

### Option A: Azure Portal
1. Go to https://portal.azure.com
2. Find your App Service: `laserclouding-hva2gweudafvadcw`
3. Go to Settings → Configuration → General Settings
4. Set **"Web sockets"** to **ON**
5. Click **Save**
6. Click **Restart**

### Option B: Azure CLI
```bash
az webapp config set \
  --name laserclouding-hva2gweudafvadcw \
  --resource-group <your-resource-group> \
  --web-sockets-enabled true
```

## Step 3: Test After Deployment

1. **Web App**: https://laserclouding-hva2gweudafvadcw.canadacentral-01.azurewebsites.net
   - Should show "Online (HTTP)" or "Online (Real-time)"
   - Notes should add immediately without refresh

2. **Debug Page**: https://laserclouding-hva2gweudafvadcw.canadacentral-01.azurewebsites.net/debug
   - Shows detailed connection info

3. **Desktop App**: `python main.py`
   - Should show clearer connection status

## Expected Results

**Before Fix:**
- Web app: "Offline" (incorrect)
- Need refresh after adding notes
- Desktop: Confusing error messages

**After Fix:**
- Web app: "Online (HTTP)" or "Online (Real-time)"
- Notes add instantly
- Desktop: Clear status messages

## Troubleshooting

If still showing offline:
1. Check if WebSockets are truly enabled in Azure
2. Restart the App Service
3. Clear browser cache
4. Use debug page to see exact error messages

Your app **works fine without WebSockets** - it just won't have real-time sync between multiple users. All core functionality (add/delete notes) works perfectly via HTTP API.