# Local Backend + ngrok + GitHub Pages Complete Startup Process

This document provides detailed instructions on how to set up the complete deployment process for Local Backend + ngrok + GitHub Pages.

## 🚀 Quick Startup Process

### **1. Backend Startup (Local)**
```bash
# Activate conda environment
conda activate capstone

# Start backend service
cd RegHealth-Navigator
export FLASK_ENV=development
python -m app.main
```
✅ **Backend running on**: `http://127.0.0.1:8080`

### **2. Setup Public Tunnel (ngrok)**
```bash
# New terminal window
ngrok http 8080
```
✅ **Get public URL**: `https://xxxxx.ngrok-free.app`

### **3. Configure GitHub Repository Secret**
1. Visit: `https://github.com/LoadingBFX/RegHealth-Navigator/settings/secrets/actions`
2. Edit the `VITE_API_BASE_URL` secret
3. Set value to ngrok URL: `https://xxxxx.ngrok-free.app`

### **4. Trigger Frontend Deployment**
```bash
# Any commit triggers GitHub Actions
git commit --allow-empty -m "Update API URL for deployment" && git push origin dev
```

### **5. Access Deployed Application**
- **Frontend**: `https://loadingbfx.github.io/RegHealth-Navigator/`
- **Backend API**: `https://xxxxx.ngrok-free.app`

---

## 🔧 System Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   GitHub Pages  │    │    ngrok     │    │  Local Backend  │
│   (Frontend)    │◄──►│   Tunnel     │◄──►│   Flask API     │
│                 │    │              │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
  loadingbfx.github.io   xxxxx.ngrok.app     127.0.0.1:8080
```

---

## 📝 Detailed Configuration

### **Backend Configuration**

#### CORS Settings (`app/config/development.yml`)
```yaml
cors:
  origins:
    - http://localhost:5173          # Local development
    - http://127.0.0.1:5173         # Local development
    - https://*.github.io           # GitHub Pages
    - https://loadingbfx.github.io/RegHealth-Navigator  # Specific project URL
    - https://*.ngrok.io            # ngrok tunnel
    - https://*.loca.lt             # localtunnel (backup)
```

#### Required Environment Variables
```bash
export OPENAI_API_KEY="your-openai-api-key"
export FLASK_ENV="development"
```

### **Frontend Configuration**

#### GitHub Actions Workflow (`.github/workflows/deploy.yml`)
```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ dev, main ]
  pull_request:
    branches: [ dev, main ]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: front/package-lock.json
    
    - name: Install dependencies
      run: |
        cd front
        npm ci
    
    - name: Build
      run: |
        cd front
        npm run build
      env:
        VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
    
    - name: Deploy to GitHub Pages
      if: github.ref == 'refs/heads/dev' || github.ref == 'refs/heads/main'
      uses: peaceiris/actions-gh-pages@v3
      with:
        github_token: ${{ secrets.GITHUB_TOKEN }}
        publish_dir: ./front/dist
```

#### Frontend API Configuration (`front/src/config/index.ts`)
```typescript
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8080',
    endpoints: {
      chat: '/api/chat'
    }
  }
};
```

---

## 🔄 Complete Startup Checklist

### **Initial Setup**
- [ ] conda environment created and activated
- [ ] Backend dependencies installed (`pip install -r requirements.txt`)
- [ ] OpenAI API Key configured
- [ ] ngrok installed and configured
- [ ] GitHub repository secrets configured

### **Every Startup**
- [ ] Backend service running on `http://127.0.0.1:8080`
- [ ] ngrok tunnel established
- [ ] GitHub secret `VITE_API_BASE_URL` updated to current ngrok URL
- [ ] Frontend redeployed
- [ ] Application accessible via GitHub Pages URL

---

## ⚠️ Notes and Limitations

### **ngrok Free Version Limitations**
- **Session Time**: Free version has session time limits
- **URL Changes**: Each restart gets a new random URL
- **Access Warning**: First visit may show ngrok warning page, need to click "Visit Site"

### **Backend Notes**
- **CORS Configuration**: Any new frontend domain needs to be added to CORS configuration
- **Restart Required**: Backend service needs restart after configuration changes
- **Log Monitoring**: Recommended to monitor backend logs for troubleshooting

### **Frontend Deployment**
- **Build Time**: GitHub Actions build typically takes 2-3 minutes
- **Cache Issues**: Browser may cache old version, need hard refresh (Ctrl+F5)
- **Environment Variables**: Ensure `VITE_API_BASE_URL` secret is correctly set

---

## 🛠️ Troubleshooting

### **Connection Issues**
```bash
# Test backend local connection
curl -X POST http://127.0.0.1:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Test ngrok connection
curl -X POST https://xxxxx.ngrok-free.app/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  -H "ngrok-skip-browser-warning: true"
```

### **Common Errors**

#### 1. "Unable to connect to the server"
**Cause**: ngrok URL expired or not updated
**Solution**: 
1. Check if ngrok is still running
2. Update GitHub repository secret
3. Redeploy frontend

#### 2. CORS Errors
**Cause**: Frontend domain not in CORS configuration
**Solution**: Add new domain to `app/config/development.yml` and restart backend

#### 3. Build Failures
**Cause**: Environment variables not set correctly
**Solution**: Check GitHub repository secrets and ensure `VITE_API_BASE_URL` is set

---

## 📊 Performance Monitoring

### **Backend Performance**
- Monitor response times for API calls
- Check memory usage during processing
- Monitor OpenAI API usage and costs

### **Frontend Performance**
- Monitor page load times
- Check for JavaScript errors in browser console
- Verify API calls are reaching the correct endpoint

---

## 🔄 Maintenance

### **Regular Tasks**
- Update ngrok URL in GitHub secrets when it changes
- Monitor backend logs for errors
- Check GitHub Actions for deployment status
- Update dependencies as needed

### **Backup and Recovery**
- Keep local copies of configuration files
- Document any custom settings
- Have backup deployment strategies ready