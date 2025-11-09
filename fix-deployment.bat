@echo off
echo ========================================
echo   Azure WebSocket Fix Deployment
echo ========================================

echo.
echo 1. Uploading updated files to Azure...
echo   - Fixed web.config (WebSocket enabled)
echo   - Improved desktop app error handling  
echo   - Better web app fallback to HTTP API

echo.
echo 2. After deployment, you need to enable WebSockets in Azure:
echo   a) Go to Azure Portal
echo   b) Navigate to your App Service: laserclouding-hva2gweudafvadcw
echo   c) Go to Configuration > General Settings
echo   d) Set "Web sockets" to ON
echo   e) Click Save and restart the app

echo.
echo 3. Alternative using Azure CLI:
echo   az webapp config set --name laserclouding-hva2gweudafvadcw --resource-group [your-resource-group] --web-sockets-enabled true

echo.
echo 4. Testing after deployment:
echo   - Desktop app: python main.py
echo   - Web app: https://laserclouding-hva2gweudafvadcw.canadacentral-01.azurewebsites.net
echo   - Health check: https://laserclouding-hva2gweudafvadcw.canadacentral-01.azurewebsites.net/health

echo.
echo Press any key to continue with Git deployment...
pause

echo.
echo Deploying to Azure...
git add .
git commit -m "Fix WebSocket issues and improve connection handling"
git push origin master

echo.
echo ========================================
echo Deployment completed!
echo.
echo Next steps:
echo 1. Enable WebSockets in Azure Portal (see instructions above)
echo 2. Restart your App Service
echo 3. Test both desktop and web apps
echo ========================================
pause