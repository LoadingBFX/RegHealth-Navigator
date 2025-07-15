# 无公网 IP 部署解决方案

## 🚨 问题描述

你的情况：
- ✅ 本地后端运行正常
- ❌ 没有公网 IP
- ❌ 前端无法访问本地后端
- ✅ 前端部署在 GitHub Pages/Cloudflare Pages

## 🛠️ 解决方案

### 方案 1: ngrok (推荐用于开发)

#### 安装 ngrok
```bash
# macOS
brew install ngrok

# 或者访问 https://ngrok.com/download
```

#### 启动后端
```bash
# 1. 启动后端
./scripts/start_backend.sh

# 2. 在另一个终端启动 ngrok
ngrok http 8080
```

#### ngrok 输出示例
```
Session Status                online
Account                       your-email@example.com
Version                       3.5.0
Region                        United States (us)
Latency                       51ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8080
```

#### 配置前端
在 GitHub Pages 或 Cloudflare Pages 中设置环境变量：
```
VITE_API_BASE_URL = https://abc123.ngrok.io
```

### 方案 2: localtunnel (免费替代)

#### 安装 localtunnel
```bash
npm install -g localtunnel
```

#### 启动隧道
```bash
# 启动后端
./scripts/start_backend.sh

# 启动 localtunnel
lt --port 8080
```

#### 输出示例
```
your url is: https://abc123.loca.lt
```

#### 配置前端
```
VITE_API_BASE_URL = https://abc123.loca.lt
```

### 方案 3: 云服务器部署 (生产环境)

#### 选择云服务器
- **DigitalOcean**: $5/月
- **AWS EC2**: 免费层可用
- **Google Cloud**: 免费层可用
- **Vultr**: $2.5/月

#### 部署步骤
```bash
# 1. 在服务器上克隆代码
git clone https://github.com/your-username/RegHealth-Navigator.git
cd RegHealth-Navigator

# 2. 安装依赖
pip install -r requirements.txt

# 3. 设置环境变量
export OPENAI_API_KEY="your-api-key"

# 4. 启动后端
./scripts/start_backend.sh
```

#### 配置防火墙
```bash
# Ubuntu/Debian
sudo ufw allow 8080

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

#### 配置前端
```
VITE_API_BASE_URL = http://your-server-ip:8080
```

### 方案 4: Cloudflare Workers (全托管)

#### 优势
- 无需管理服务器
- 自动 SSL
- 全球 CDN
- 完全免费

#### 部署步骤
1. 将后端代码转换为 Cloudflare Workers
2. 部署到 Cloudflare Workers
3. 前端直接连接 Workers

## 🧪 测试连接

### 使用测试脚本
```bash
# 测试 ngrok 连接
python scripts/test_cloudflare_connection.py

# 测试 localtunnel 连接
curl https://abc123.loca.lt/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

### 手动测试
```bash
# 测试本地后端
curl http://localhost:8080/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 测试 ngrok 隧道
curl https://abc123.ngrok.io/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## 📋 推荐工作流程

### 开发阶段 (推荐 ngrok)
```bash
# 1. 启动后端
./scripts/start_backend.sh

# 2. 启动 ngrok (新终端)
ngrok http 8080

# 3. 复制 ngrok URL
# 例如: https://abc123.ngrok.io

# 4. 在 GitHub Pages/Cloudflare Pages 设置
VITE_API_BASE_URL = https://abc123.ngrok.io

# 5. 推送代码触发部署
git push origin dev
```

### 生产阶段 (推荐云服务器)
1. 部署后端到云服务器
2. 配置域名和 SSL
3. 设置环境变量指向服务器
4. 监控和维护

## 🔧 自动化脚本

### 启动开发环境
```bash
#!/bin/bash
# start_dev_with_ngrok.sh

echo "🚀 Starting development environment..."

# 启动后端
./scripts/start_backend.sh &

# 等待后端启动
sleep 5

# 启动 ngrok
echo "🌐 Starting ngrok tunnel..."
ngrok http 8080 --log=stdout
```

### 获取 ngrok URL
```bash
#!/bin/bash
# get_ngrok_url.sh

echo "🔍 Getting ngrok URL..."

# 获取 ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

if [ "$NGROK_URL" != "null" ]; then
    echo "✅ ngrok URL: $NGROK_URL"
    echo "📝 Use this URL in your frontend environment variables:"
    echo "   VITE_API_BASE_URL = $NGROK_URL"
else
    echo "❌ ngrok not running"
    echo "   Start ngrok with: ngrok http 8080"
fi
```

## 🚨 注意事项

### ngrok 限制
- **免费版**: 每次重启 URL 会变化
- **付费版**: 固定域名，更稳定
- **连接数**: 免费版有连接数限制

### 安全考虑
- ngrok 会暴露你的本地服务到公网
- 建议只在开发时使用
- 生产环境使用云服务器

### 性能考虑
- ngrok 会增加延迟
- 适合开发测试，不适合生产

## 💰 成本对比

| 方案 | 成本 | 适用场景 |
|------|------|----------|
| ngrok 免费版 | $0 | 开发测试 |
| ngrok 付费版 | $8/月 | 开发+演示 |
| localtunnel | $0 | 开发测试 |
| 云服务器 | $5-20/月 | 生产环境 |
| Cloudflare Workers | $0 | 全托管 |

## 🎯 推荐选择

### 立即开始 (今天)
**使用 ngrok** - 免费，快速，适合开发

### 长期方案 (生产)
**云服务器** - 稳定，可控，适合生产

### 全托管方案
**Cloudflare Workers** - 无需管理服务器 