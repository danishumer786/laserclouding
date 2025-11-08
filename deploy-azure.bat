@echo off
echo ================================
echo  Notes App - Azure Deployment
echo ================================
echo.

echo Checking if Azure CLI is installed...
az --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Azure CLI is not installed.
    echo Please install it from: https://aka.ms/installazurecliwindows
    echo Then run this script again.
    pause
    exit /b 1
)

echo Azure CLI is installed!
echo.

echo Logging into Azure...
az login
if %errorlevel% neq 0 (
    echo ERROR: Failed to login to Azure
    pause
    exit /b 1
)

echo.
echo Please enter your app name (must be globally unique):
set /p APP_NAME="App Name (e.g., photonix-notes-app): "

echo.
echo Please enter your resource group name:
set /p RESOURCE_GROUP="Resource Group Name (e.g., photonix-resources): "

echo.
echo Deploying to Azure App Service...
echo This may take a few minutes...

az webapp up --sku F1 --name %APP_NAME% --resource-group %RESOURCE_GROUP% --runtime "PYTHON:3.9" --location "East US"

if %errorlevel% equ 0 (
    echo.
    echo ================================
    echo   DEPLOYMENT SUCCESSFUL!
    echo ================================
    echo.
    echo Your app is now available at:
    echo https://%APP_NAME%.azurewebsites.net
    echo.
    echo Next steps:
    echo 1. Open the URL above to test your web app
    echo 2. Update your main.py file to use the cloud URL
    echo 3. Test the desktop app with the cloud connection
    echo.
) else (
    echo.
    echo ERROR: Deployment failed
    echo Please check the error messages above
)

echo.
pause