# Local Backend + ngrok + GitHub Pages 完整启动流程

本文档详细说明如何设置 Local Backend + ngrok + GitHub Pages 的完整部署流程。

## 🚀 快速启动流程

### **1. 后端启动 (Local)**
```bash
# 激活conda环境
conda activate capstone

# 启动后端服务
cd RegHealth-Navigator
export FLASK_ENV=development
python -m app.main
```
✅ **后端运行在**: `http://127.0.0.1:8080`

### **2. 设置公网隧道 (ngrok)**
```bash
# 新终端窗口
ngrok http 8080
```
✅ **获得公网URL**: `https://xxxxx.ngrok-free.app`

### **3. 配置 GitHub Repository Secret**
1. 访问: `https://github.com/LoadingBFX/RegHealth-Navigator/settings/secrets/actions`
2. 编辑 `VITE_API_BASE_URL` secret
3. 设置值为 ngrok URL: `https://xxxxx.ngrok-free.app`

### **4. 触发前端部署**
```bash
# 任意提交触发 GitHub Actions
git commit --allow-empty -m "Update API URL for deployment" && git push origin dev
```

### **5. 访问部署的应用**
- **前端**: `https://loadingbfx.github.io/RegHealth-Navigator/`
- **后端API**: `https://xxxxx.ngrok-free.app`

---

## 🔧 系统架构

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   GitHub Pages  │    │    ngrok     │    │  Local Backend  │
│   (Frontend)    │◄──►│   Tunnel     │◄──►│   Flask API     │
│                 │    │              │    │                 │
└─────────────────┘    └──────────────┘    └─────────────────┘
  loadingbfx.github.io   xxxxx.ngrok.app     127.0.0.1:8080
```

---

## 📝 详细配置

### **后端配置**

#### CORS 设置 (`app/config/development.yml`)
```yaml
cors:
  origins:
    - http://localhost:5173          # 本地开发
    - http://127.0.0.1:5173         # 本地开发
    - https://*.github.io           # GitHub Pages
    - https://loadingbfx.github.io/RegHealth-Navigator  # 具体项目URL
    - https://*.ngrok.io            # ngrok 隧道
    - https://*.loca.lt             # localtunnel (备用)
```

#### 必需的环境变量
```bash
export OPENAI_API_KEY="your-openai-api-key"
export FLASK_ENV="development"
```

### **前端配置**

#### GitHub Actions 工作流 (`.github/workflows/deploy.yml`)
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

#### 前端 API 配置 (`front/src/config/index.ts`)
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

## 🔄 完整启动检查清单

### **初次设置**
- [ ] conda 环境已创建并激活
- [ ] 后端依赖已安装 (`pip install -r requirements.txt`)
- [ ] OpenAI API Key 已设置
- [ ] ngrok 已安装并配置
- [ ] GitHub repository secrets 已配置

### **每次启动**
- [ ] 后端服务运行在 `http://127.0.0.1:8080`
- [ ] ngrok 隧道已建立
- [ ] GitHub secret `VITE_API_BASE_URL` 已更新为当前 ngrok URL
- [ ] 前端已重新部署
- [ ] 应用可通过 GitHub Pages URL 访问

---

## ⚠️ 注意事项与限制

### **ngrok 免费版限制**
- **会话时间**: 免费版有会话时间限制
- **URL 变化**: 每次重启都会获得新的随机 URL
- **访问警告**: 首次访问可能显示 ngrok 警告页面，需点击 "Visit Site"

### **后端注意事项**
- **CORS 配置**: 任何新的前端域名都需要添加到 CORS 配置中
- **重启需求**: 修改配置文件后需要重启后端服务
- **日志监控**: 建议监控后端日志以排查问题

### **前端部署**
- **构建时间**: GitHub Actions 构建通常需要 2-3 分钟
- **缓存问题**: 浏览器可能缓存旧版本，需要硬刷新 (Ctrl+F5)
- **环境变量**: 确保 `VITE_API_BASE_URL` secret 正确设置

---

## 🛠️ 故障排除

### **连接问题**
```bash
# 测试后端本地连接
curl -X POST http://127.0.0.1:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 测试 ngrok 连接
curl -X POST https://xxxxx.ngrok-free.app/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' \
  -H "ngrok-skip-browser-warning: true"
```

### **常见错误**

#### 1. "Unable to connect to the server"
**原因**: ngrok URL 过期或未更新
**解决**: 
1. 检查 ngrok 是否还在运行
2. 更新 GitHub repository secret
3. 重新触发部署

#### 2. CORS 错误
**原因**: 前端域名不在 CORS 允许列表中
**解决**: 
1. 检查 `app/config/development.yml` 中的 CORS 配置
2. 重启后端服务

#### 3. 前端白屏
**原因**: JavaScript 错误或 API 响应格式问题
**解决**: 
1. 检查浏览器控制台错误
2. 验证 API 响应格式
3. 检查网络请求状态

#### 4. GitHub Actions 部署失败
**原因**: 环境变量未设置或构建错误
**解决**: 
1. 检查 GitHub Actions 日志
2. 验证 `VITE_API_BASE_URL` secret 设置
3. 确认 Node.js 依赖完整

---

## 📊 性能优化建议

### **后端优化**
- 使用生产级 WSGI 服务器 (如 Gunicorn)
- 配置请求日志和监控
- 实现 API 响应缓存

### **前端优化**
- 启用 Vite 构建优化
- 配置 CDN 加速
- 实现前端缓存策略

### **网络优化**
- 使用 ngrok 付费版获得固定 URL
- 考虑使用 Cloudflare Tunnel 作为替代
- 配置请求压缩和优化

---

## 🔗 相关文档

- [Deployment Guide](./deployment_guide.md) - 通用部署指南
- [GitHub Actions 说明](./github_action_instruction.md) - GitHub Actions 详细说明
- [Frontend Guide](./frontend_guide.md) - 前端开发指南
- [Troubleshooting](../README.md#troubleshooting) - 问题排除指南

---

## 📝 更新日志

- **2025-07-08**: 初始版本，包含完整的 Local Backend + ngrok + GitHub Pages 流程
- **修复问题**: 解决了 `ask_question` 方法返回值格式问题
- **CORS 配置**: 完善了跨域访问配置
- **部署优化**: 改进了 GitHub Actions 工作流配置