# Deployment Checklist

## Pre-Deployment Checklist

### Backend Setup
- [ ] **Environment Variables**
  - [ ] `OPENAI_API_KEY` is set
  - [ ] `FLASK_ENV=production` is set
  - [ ] Backend server is accessible from internet

- [ ] **Server Configuration**
  - [ ] Port 8080 is open in firewall
  - [ ] SSL certificate is installed (for HTTPS)
  - [ ] CORS is configured for frontend domains
  - [ ] Server is running on `0.0.0.0:8080`

- [ ] **Security**
  - [ ] API keys are not in version control
  - [ ] Server has proper access controls
  - [ ] Rate limiting is configured (optional)

### Frontend Setup
- [ ] **Environment Variables**
  - [ ] `VITE_API_BASE_URL` points to backend
  - [ ] Environment variables are set in deployment platform

- [ ] **Build Configuration**
  - [ ] Build command: `npm run build`
  - [ ] Output directory: `dist`
  - [ ] Root directory: `front`

### Repository Setup
- [ ] **GitHub Secrets** (for GitHub Pages)
  - [ ] `VITE_API_BASE_URL` is set in repository secrets
  - [ ] GitHub Pages is enabled
  - [ ] GitHub Actions workflow is configured

- [ ] **Cloudflare Pages** (alternative)
  - [ ] Repository is connected to Cloudflare Pages
  - [ ] Build settings are configured
  - [ ] Environment variables are set

## Deployment Steps

### 1. Backend Deployment
```bash
# Option A: Local server
./scripts/start_backend.sh

# Option B: Production server
# Follow the deployment guide for your chosen platform
```

### 2. Test Backend
```bash
# Test if backend is accessible
curl -X POST https://your-backend-domain.com:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 3. Frontend Deployment
- [ ] Push changes to `dev` branch (or `main` branch)
- [ ] Check GitHub Actions workflow (if using GitHub Pages)
- [ ] Verify deployment in Cloudflare Pages dashboard (if using Cloudflare)

### 4. Test Frontend
- [ ] Open deployed frontend URL
- [ ] Test chat functionality
- [ ] Check browser console for errors
- [ ] Verify API calls are working

## Post-Deployment Verification

### Backend Health Check
- [ ] API endpoints respond correctly
- [ ] CORS headers are present
- [ ] SSL certificate is valid
- [ ] Server logs show no errors

### Frontend Health Check
- [ ] Page loads without errors
- [ ] Chat interface is functional
- [ ] API calls succeed
- [ ] No CORS errors in console

### Integration Test
- [ ] Send a test message through the chat
- [ ] Verify response is received
- [ ] Check that citations work (if implemented)
- [ ] Test on different browsers

## Monitoring Setup

### Backend Monitoring
- [ ] Set up logging
- [ ] Configure error alerts
- [ ] Monitor API usage
- [ ] Track response times

### Frontend Monitoring
- [ ] Enable analytics
- [ ] Set up error tracking
- [ ] Monitor user interactions
- [ ] Track performance metrics

## Troubleshooting Common Issues

### CORS Errors
- [ ] Check if frontend domain is in CORS origins
- [ ] Verify backend is accessible
- [ ] Check SSL certificate validity

### Connection Issues
- [ ] Verify backend URL is correct
- [ ] Check firewall settings
- [ ] Test with curl or Postman

### Build Failures
- [ ] Check Node.js version
- [ ] Verify all dependencies are installed
- [ ] Check for TypeScript errors
- [ ] Verify environment variables

## Security Checklist

- [ ] API keys are secure
- [ ] HTTPS is enabled
- [ ] CORS is properly configured
- [ ] No sensitive data in logs
- [ ] Rate limiting is in place (optional)
- [ ] Input validation is working

## Performance Checklist

- [ ] Frontend loads quickly
- [ ] API responses are fast
- [ ] Images are optimized
- [ ] Bundle size is reasonable
- [ ] Caching is configured

## Documentation

- [ ] Update README with deployment instructions
- [ ] Document environment variables
- [ ] Create troubleshooting guide
- [ ] Update API documentation

## Final Steps

- [ ] Test with real users
- [ ] Monitor for issues
- [ ] Set up backup procedures
- [ ] Plan for scaling
- [ ] Document lessons learned 