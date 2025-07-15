# Deployment Guide: Local Backend with Cloudflare/GitHub Pages Frontend

## Overview
This guide explains how to deploy the RegHealth Navigator with a local backend server and a frontend hosted on Cloudflare Pages or GitHub Pages.

> **💡 Quick Start**: For a complete step-by-step setup guide using ngrok + GitHub Pages, see [Local Backend + GitHub Pages Setup](./local_backend_github_pages_setup.md)

## Architecture
- **Backend**: Flask API running locally (or on a server)
- **Frontend**: React app deployed on Cloudflare Pages or GitHub Pages
- **Connection**: Frontend communicates with backend via HTTPS

## Step 1: Backend Deployment

### Option A: Local Development Server
```bash
# Navigate to the backend directory
cd app

# Install dependencies
pip install -r ../requirements.txt

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key"
export FLASK_ENV="production"

# Run the server
python main.py
```

### Option B: Production Server (Recommended)
1. **Deploy to a VPS or cloud server** (DigitalOcean, AWS EC2, etc.)
2. **Configure firewall** to allow port 8080
3. **Set up SSL certificate** (Let's Encrypt)
4. **Use a reverse proxy** (Nginx) for better security

### Backend Configuration
The backend is configured to accept connections from:
- `https://*.pages.dev` (Cloudflare Pages)
- `https://*.github.io` (GitHub Pages)
- `https://*.cloudflare.com` (Cloudflare Workers)

## Step 2: Frontend Configuration

### Environment Variables
Create a `.env.production` file in the `front/` directory:
```bash
# Replace with your actual backend URL
VITE_API_BASE_URL=https://your-backend-domain.com:8080
```

### Build Configuration
The frontend is already configured to use environment variables for the API base URL.

## Step 3: Frontend Deployment

### Option A: Cloudflare Pages
1. **Connect your GitHub repository** to Cloudflare Pages
2. **Configure build settings**:
   - Build command: `npm run build`
   - Build output directory: `dist`
   - Root directory: `front`
3. **Set environment variables** in Cloudflare Pages dashboard:
   - `VITE_API_BASE_URL`: Your backend URL

### Option B: GitHub Pages
1. **Enable GitHub Pages** in your repository settings
2. **Set source** to GitHub Actions
3. **Create GitHub Actions workflow** (see below)

## Step 4: GitHub Actions Workflow (for GitHub Pages)

The workflow file `.github/workflows/deploy.yml` is already configured to deploy from both `dev` and `main` branches:

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
    
    steps:
    - uses: actions/checkout@v4
    
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

## Step 5: Security Considerations

### CORS Configuration
The backend is configured to accept requests from:
- Cloudflare Pages domains
- GitHub Pages domains
- Your specific domains

### SSL/TLS
- **Backend**: Use Let's Encrypt for free SSL certificates
- **Frontend**: Cloudflare Pages and GitHub Pages provide SSL automatically

### API Key Security
- Store `OPENAI_API_KEY` as environment variable
- Never commit API keys to version control
- Use secrets management in deployment platforms

## Step 6: Testing

### Test Backend
```bash
# Test if backend is accessible
curl -X POST https://your-backend-domain.com:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### Test Frontend
1. Deploy frontend to Cloudflare Pages or GitHub Pages
2. Open the deployed URL
3. Test the chat functionality
4. Check browser console for any CORS errors

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check if your frontend domain is in the CORS origins list
   - Ensure backend is running and accessible

2. **Connection Refused**
   - Check if backend is running on the correct port
   - Verify firewall settings
   - Check if the backend URL is correct in frontend config

3. **SSL Certificate Issues**
   - Ensure backend has valid SSL certificate
   - Check if frontend is using HTTPS

### Debug Steps
1. Check backend logs for errors
2. Check browser console for frontend errors
3. Test API endpoints directly with curl
4. Verify environment variables are set correctly

## Monitoring and Maintenance

### Backend Monitoring
- Set up logging to track API usage
- Monitor server resources
- Set up alerts for downtime

### Frontend Monitoring
- Use Cloudflare Analytics or GitHub Pages analytics
- Monitor for JavaScript errors
- Track user interactions

## Cost Considerations

### Backend Hosting
- VPS: $5-20/month
- Cloud hosting: Varies by provider
- SSL certificates: Free with Let's Encrypt

### Frontend Hosting
- Cloudflare Pages: Free tier available
- GitHub Pages: Free for public repositories

### API Costs
- OpenAI API: Pay per use
- Monitor usage to control costs

## Next Steps

1. **Set up monitoring** and alerting
2. **Implement rate limiting** on the backend
3. **Add authentication** if needed
4. **Set up CI/CD** for automated deployments
5. **Implement caching** for better performance 