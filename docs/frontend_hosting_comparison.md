# 前端托管平台对比

## 🎯 重要说明

**你可以选择任意一个平台，不需要同时使用！**

- ✅ **GitHub Pages** - 完全免费，适合大多数项目
- ✅ **Cloudflare Pages** - 免费，性能更好，功能更丰富
- ❌ **不需要同时使用两者**

## 📊 平台对比

| 特性 | GitHub Pages | Cloudflare Pages |
|------|-------------|------------------|
| **免费额度** | 完全免费 | 完全免费 |
| **自定义域名** | ✅ 支持 | ✅ 支持 |
| **SSL 证书** | ✅ 自动 | ✅ 自动 |
| **CDN** | ✅ 基础 | ✅ 全球 CDN |
| **构建速度** | 较慢 | 很快 |
| **环境变量** | ✅ GitHub Secrets | ✅ 内置支持 |
| **分支部署** | ✅ 支持 | ✅ 支持 |
| **预览部署** | ✅ PR 预览 | ✅ PR 预览 |
| **分析工具** | ❌ 无 | ✅ 内置 |
| **边缘函数** | ❌ 无 | ✅ Workers |

## 🚀 GitHub Pages 部署

### 优势
- **完全免费** - 无任何限制
- **简单易用** - 配置简单
- **GitHub 集成** - 与代码仓库完美集成
- **自动部署** - 推送代码自动部署

### 配置步骤
1. **启用 GitHub Pages**
   ```bash
   # 进入仓库 Settings → Pages
   # Source: "GitHub Actions"
   # Branch: 选择你的分支 (dev/main)
   ```

2. **设置环境变量**
   ```bash
   # 进入 Settings → Secrets and variables → Actions
   # 添加: VITE_API_BASE_URL = https://your-backend-domain.com:8080
   ```

3. **推送代码**
   ```bash
   git push origin dev
   # 自动触发部署
   ```

### 访问地址
```
https://your-username.github.io/your-repo-name
```

## ⚡ Cloudflare Pages 部署

### 优势
- **性能更好** - 全球 CDN 加速
- **功能丰富** - 更多高级功能
- **分析工具** - 内置访问分析
- **边缘计算** - 支持 Workers

### 配置步骤
1. **连接仓库**
   ```bash
   # 访问 https://pages.cloudflare.com/
   # 点击 "Create a project"
   # 选择 "Connect to Git"
   # 选择你的 GitHub 仓库
   ```

2. **构建设置**
   ```
   Project name: reghealth-navigator
   Production branch: dev
   Framework preset: None
   Build command: npm run build
   Build output directory: dist
   Root directory: front
   ```

3. **环境变量**
   ```
   VITE_API_BASE_URL = https://your-backend-domain.com:8080
   ```

### 访问地址
```
https://reghealth-navigator.pages.dev
```

## 🔧 后端配置

无论选择哪个平台，后端配置都是一样的：

### CORS 配置
```yaml
# app/config/development.yml
cors:
  origins:
    - https://*.github.io      # GitHub Pages
    - https://*.pages.dev      # Cloudflare Pages
    - https://your-domain.com  # 自定义域名
```

### 环境变量
```bash
# 后端启动
export OPENAI_API_KEY="your-api-key"
./scripts/start_backend.sh
```

## 📋 推荐选择

### 选择 GitHub Pages 如果你：
- ✅ 想要最简单的配置
- ✅ 预算有限（完全免费）
- ✅ 项目规模较小
- ✅ 主要使用 GitHub 生态系统

### 选择 Cloudflare Pages 如果你：
- ✅ 需要更好的性能
- ✅ 想要更多高级功能
- ✅ 计划使用边缘计算
- ✅ 需要详细的分析数据

## 🎯 我的建议

### 开发阶段
**推荐 GitHub Pages** - 配置简单，完全免费

### 生产阶段
**推荐 Cloudflare Pages** - 性能更好，功能更丰富

## 🔄 迁移指南

### 从 GitHub Pages 迁移到 Cloudflare Pages
1. 在 Cloudflare Pages 创建新项目
2. 连接相同的 GitHub 仓库
3. 配置相同的环境变量
4. 更新 DNS 记录（如果需要自定义域名）
5. 删除 GitHub Pages 配置

### 从 Cloudflare Pages 迁移到 GitHub Pages
1. 在 GitHub 启用 Pages
2. 配置 GitHub Actions 工作流
3. 设置 GitHub Secrets
4. 更新 DNS 记录
5. 删除 Cloudflare Pages 项目

## ❓ 常见问题

### Q: 必须使用 Cloudflare 吗？
**A: 不是！** GitHub Pages 完全可以满足需求。

### Q: 哪个平台更好？
**A: 取决于你的需求** - GitHub Pages 更简单，Cloudflare Pages 功能更丰富。

### Q: 可以同时使用两个平台吗？
**A: 技术上可以，但不推荐** - 会增加维护复杂度。

### Q: 如何选择？
**A: 建议从 GitHub Pages 开始** - 简单易用，完全免费。 