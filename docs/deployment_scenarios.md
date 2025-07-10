# 部署方案详解

## 方案 A: 本地后端 + Cloudflare Pages 前端

### 架构图
```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────────┐
│   本地后端       │ ◄──────────────► │  Cloudflare Pages   │
│ localhost:8080  │                  │  前端 (React App)   │
│ 或服务器IP:8080  │                  │                     │
└─────────────────┘                  └─────────────────────┘
```

### 配置步骤

#### 1. 本地后端配置
```bash
# 启动后端服务器
./scripts/start_backend.sh

# 或者手动启动
cd app
export OPENAI_API_KEY="your-api-key"
export FLASK_ENV="production"
python main.py
```

#### 2. Cloudflare Pages 配置
1. **连接 GitHub 仓库**
   - 访问 [Cloudflare Pages](https://pages.cloudflare.com/)
   - 点击 "Create a project"
   - 选择 "Connect to Git"
   - 选择你的 GitHub 仓库

2. **构建设置**
   ```
   Project name: reghealth-navigator
   Production branch: dev
   Framework preset: None
   Build command: npm run build
   Build output directory: dist
   Root directory: front
   ```

3. **环境变量设置**
   ```
   VITE_API_BASE_URL = http://your-public-ip:8080
   ```
   *注意：这里需要你的公网IP，不是 localhost*

#### 3. 网络配置
```bash
# 检查你的公网IP
curl ifconfig.me

# 配置防火墙开放8080端口
# macOS:
sudo pfctl -e
echo "pass in proto tcp from any to any port 8080" | sudo pfctl -f -

# Linux:
sudo ufw allow 8080
```

### 测试连接
```bash
# 测试后端是否可以从外网访问
curl http://your-public-ip:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## 方案 B: 服务器后端 + Cloudflare Pages 前端

### 架构图
```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────────┐
│   服务器后端     │ ◄──────────────► │  Cloudflare Pages   │
│ your-domain.com │                  │  前端 (React App)   │
│ 或服务器IP:8080  │                  │                     │
└─────────────────┘                  └─────────────────────┘
```

### 配置步骤

#### 1. 服务器部署
```bash
# 在服务器上部署后端
git clone your-repo
cd RegHealth-Navigator
./scripts/start_backend.sh
```

#### 2. 域名配置
```bash
# 设置域名解析
# 在域名提供商处添加 A 记录：
# your-domain.com -> 服务器IP

# 配置 SSL 证书
sudo certbot --nginx -d your-domain.com
```

#### 3. Cloudflare Pages 环境变量
```
VITE_API_BASE_URL = https://your-domain.com:8080
```

---

## 方案 C: GitHub Pages + 自定义域名

### 架构图
```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────────┐
│   本地/服务器    │ ◄──────────────► │   GitHub Pages      │
│   后端          │                  │  前端 (React App)   │
└─────────────────┘                  └─────────────────────┘
```

### 配置步骤

#### 1. GitHub Pages 设置
- 进入仓库 Settings → Pages
- Source: "GitHub Actions"
- 自定义域名: `your-domain.com`

#### 2. 域名解析
```bash
# 在域名提供商处添加 CNAME 记录：
# your-domain.com -> username.github.io
```

#### 3. GitHub Secrets
- 进入 Settings → Secrets and variables → Actions
- 添加: `VITE_API_BASE_URL = https://your-backend-domain.com:8080`

---

## 方案 D: Cloudflare Pages + Cloudflare Workers (推荐)

### 架构图
```
┌─────────────────┐    HTTP/HTTPS    ┌─────────────────────┐
│ Cloudflare      │ ◄──────────────► │  Cloudflare Pages   │
│ Workers (后端)   │                  │  前端 (React App)   │
└─────────────────┘                  └─────────────────────┘
```

### 优势
- 全托管在 Cloudflare
- 自动 SSL
- 全球 CDN
- 无需管理服务器

---

## 🔧 网络配置详解

### 本地开发测试
```bash
# 1. 启动后端
./scripts/start_backend.sh

# 2. 测试本地连接
curl http://localhost:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 3. 获取公网IP
curl ifconfig.me

# 4. 测试公网访问
curl http://your-public-ip:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 端口转发 (如果在内网)
```bash
# 使用 ngrok 进行端口转发
ngrok http 8080

# 或者使用 localtunnel
npx localtunnel --port 8080
```

### CORS 配置检查
```yaml
# app/config/development.yml
cors:
  origins:
    - https://*.pages.dev      # Cloudflare Pages
    - https://*.github.io      # GitHub Pages
    - https://your-domain.com  # 你的自定义域名
```

---

## 🚨 常见问题

### 1. CORS 错误
**问题**: 前端无法连接到后端
**解决**: 
- 检查后端 CORS 配置
- 确保前端域名在后端允许列表中
- 验证后端 URL 是否正确

### 2. 连接被拒绝
**问题**: 无法从外网访问本地后端
**解决**:
- 检查防火墙设置
- 使用端口转发工具 (ngrok, localtunnel)
- 部署到服务器

### 3. SSL 证书问题
**问题**: HTTPS 前端无法连接 HTTP 后端
**解决**:
- 为后端配置 SSL 证书
- 使用端口转发工具的 HTTPS 版本
- 部署到支持 HTTPS 的平台

---

## 📋 推荐方案

### 开发阶段
- **本地后端** + **Cloudflare Pages 前端**
- 使用 ngrok 进行端口转发

### 生产阶段
- **服务器后端** + **Cloudflare Pages 前端**
- 配置 SSL 证书和域名

### 全托管方案
- **Cloudflare Workers 后端** + **Cloudflare Pages 前端**
- 无需管理服务器 