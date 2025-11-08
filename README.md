# Notes Application - Cloud Deployment Guide

## 📋 Overview
This is a real-time notes application with both web and desktop interfaces that sync in real-time using WebSockets.

## 🚀 Cloud Deployment Options

### Option 1: Azure App Service (Recommended - Free with Microsoft 365)

Since you have Microsoft 365, you can use Azure App Service for free:

#### Step 1: Access Azure Portal
1. Go to [portal.azure.com](https://portal.azure.com)
2. Sign in with your @photonix.com Microsoft account
3. You should have access to Azure services through your M365 subscription

#### Step 2: Create App Service
1. Click "Create a resource" → "Web App"
2. Fill in the details:
   - **Resource Group**: Create new or use existing
   - **Name**: `photonix-notes-app` (must be globally unique)
   - **Runtime Stack**: Python 3.9 or 3.10
   - **Region**: Choose closest to your location
   - **Pricing Plan**: F1 (Free tier) - good for testing
3. Click "Review + Create" → "Create"

#### Step 3: Deploy Code
**Method A: Using Azure CLI (Recommended)**
```bash
# Install Azure CLI if not installed
# Windows: Download from https://aka.ms/installazurecliwindows

# Login to Azure
az login

# Navigate to your project folder
cd "c:\Users\danis\OneDrive\Desktop\laserclouding"

# Deploy to Azure
az webapp up --sku F1 --name photonix-notes-app --resource-group your-resource-group --runtime "PYTHON:3.9"
```

**Method B: Using GitHub (Alternative)**
1. Create a GitHub repository and push your code
2. In Azure Portal → Your App Service → Deployment Center
3. Connect to GitHub and select your repository
4. Azure will automatically deploy when you push changes

#### Step 4: Configure Environment Variables
In Azure Portal → Your App Service → Configuration → Application Settings:
- `FLASK_ENV`: `production`
- `SCM_DO_BUILD_DURING_DEPLOYMENT`: `true`

### Option 2: Heroku (Free Alternative)

#### Step 1: Create Heroku Account
1. Go to [heroku.com](https://heroku.com) and sign up
2. Install Heroku CLI

#### Step 2: Deploy
```bash
# Navigate to project folder
cd "c:\Users\danis\OneDrive\Desktop\laserclouding"

# Login to Heroku
heroku login

# Create Heroku app
heroku create photonix-notes-app

# Create Procfile
echo "web: python app.py" > Procfile

# Deploy
git init
git add .
git commit -m "Initial deployment"
git push heroku main
```

### Option 3: Railway (Easiest Free Option)

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Create a new project from GitHub repository
4. Railway will automatically detect Python and deploy

## 🔧 Local Testing Before Deployment

Test your app locally first:
```bash
cd "c:\Users\danis\OneDrive\Desktop\laserclouding"
pip install -r requirements.txt
python app.py
```

## 🌐 Updating Tkinter App for Cloud

Once deployed, update your `main.py` to use the cloud URL:

```python
# Replace this line in main.py
self.api_base_url = "http://localhost:5000"

# With your cloud URL (example):
self.api_base_url = "https://photonix-notes-app.azurewebsites.net"
```

## 📊 Database Notes

- **For testing**: SQLite works fine and will be stored in the cloud instance
- **For production**: Consider upgrading to Azure SQL Database or PostgreSQL for better reliability
- **Current setup**: Database file is created automatically and persists with the app

## 🔍 Troubleshooting

### Common Issues:
1. **App won't start**: Check logs in Azure Portal → Log Stream
2. **Database issues**: Ensure write permissions are set correctly
3. **WebSocket connection fails**: Make sure your cloud provider supports WebSockets (Azure App Service does)

### Azure Logs:
```bash
az webapp log tail --name photonix-notes-app --resource-group your-resource-group
```

## 🎯 Next Steps After Deployment

1. **Test the cloud deployment** - Access your app URL
2. **Update desktop app** - Change API URL to cloud URL  
3. **Add authentication** - Integrate with Microsoft 365/Azure AD
4. **Custom domain** - Add your company domain (optional)
5. **SSL certificate** - Azure provides free SSL automatically

## 📞 Support

If you encounter issues:
- Azure: Check the Azure Portal logs
- General: Review the console output and error messages
- WebSocket issues: Ensure your hosting provider supports WebSockets

## 🔐 Security Notes

- Current deployment is open to everyone with the URL
- After deployment, we'll add Microsoft 365 authentication
- Use HTTPS in production (automatically provided by cloud services)