# 端口转发指南

## 为什么需要端口转发？

当你的前端部署在 Cloudflare Pages 上时，它需要能够访问你的后端 API。如果你的后端运行在本地机器上，Cloudflare Pages 无法直接访问 `localhost:8080`，因为：

1. **localhost** 只在你的本地机器上有效
2. **Cloudflare Pages** 运行在 Cloudflare 的服务器上
3. **跨域访问** 需要公网可访问的地址

## 解决方案

### 方案 1: ngrok (推荐用于开发)

#### 安装 ngrok
```bash
# macOS
brew install ngrok

# 或者下载安装
# 访问 https://ngrok.com/download
```

#### 启动隧道
```bash
# 启动 HTTP 隧道
ngrok http 8080

# 或者启动 HTTPS 隧道 (推荐)
ngrok http 8080 --scheme https
```

#### 输出示例
```
Session Status                online
Account                       your-email@example.com
Version                       3.5.0
Region                        United States (us)
Latency                       51ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok.io -> http://localhost:8080
```

#### 在 Cloudflare Pages 中使用
```
VITE_API_BASE_URL = https://abc123.ngrok.io
```

### 方案 2: localtunnel

#### 安装 localtunnel
```bash
npm install -g localtunnel
```

#### 启动隧道
```bash
lt --port 8080
```

#### 输出示例
```
your url is: https://abc123.loca.lt
```

#### 在 Cloudflare Pages 中使用
```
VITE_API_BASE_URL = https://abc123.loca.lt
```

### 方案 3: 配置防火墙 (生产环境)

#### macOS 防火墙配置
```bash
# 启用防火墙
sudo pfctl -e

# 添加规则允许 8080 端口
echo "pass in proto tcp from any to any port 8080" | sudo pfctl -f -

# 检查规则
sudo pfctl -s rules
```

#### Linux 防火墙配置
```bash
# Ubuntu/Debian
sudo ufw allow 8080

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

#### 获取公网 IP
```bash
curl ifconfig.me
```

#### 在 Cloudflare Pages 中使用
```
VITE_API_BASE_URL = http://your-public-ip:8080
```

## 测试连接

### 使用测试脚本
```bash
# 测试本地连接
python scripts/test_deployment.py

# 测试公网连接
python scripts/test_cloudflare_connection.py
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

## 安全考虑

### ngrok 安全设置
```bash
# 设置认证令牌
ngrok config add-authtoken YOUR_AUTH_TOKEN

# 限制访问
ngrok http 8080 --basic-auth "username:password"
```

### 生产环境建议
1. **使用 HTTPS** - 确保前端和后端都使用 HTTPS
2. **配置 CORS** - 只允许特定域名访问
3. **使用域名** - 不要直接暴露 IP 地址
4. **监控访问** - 设置访问日志和监控

## 故障排除

### 常见问题

#### 1. ngrok 连接失败
```bash
# 检查 ngrok 状态
ngrok status

# 重新启动隧道
ngrok http 8080 --log=stdout
```

#### 2. CORS 错误
确保后端 CORS 配置包含 ngrok 域名：
```yaml
# app/config/development.yml
cors:
  origins:
    - https://*.ngrok.io
    - https://*.loca.lt
    - https://*.pages.dev
```

#### 3. 端口被占用
```bash
# 检查端口占用
lsof -i :8080

# 杀死占用进程
kill -9 PID
```

## 推荐工作流程

### 开发阶段
1. 启动本地后端：`./scripts/start_backend.sh`
2. 启动 ngrok 隧道：`ngrok http 8080`
3. 在 Cloudflare Pages 设置环境变量
4. 推送代码到 `dev` 分支触发部署
5. 测试连接

### 生产阶段
1. 部署后端到服务器
2. 配置域名和 SSL 证书
3. 在 Cloudflare Pages 使用生产环境 URL
4. 监控和日志记录

## 自动化脚本

### 启动开发环境
```bash
#!/bin/bash
# start_dev.sh

echo "🚀 Starting development environment..."

# 启动后端
./scripts/start_backend.sh &

# 等待后端启动
sleep 5

# 启动 ngrok
ngrok http 8080 --log=stdout
```

### 测试连接
```bash
#!/bin/bash
# test_connection.sh

echo "🔍 Testing connection..."

# 获取 ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

if [ "$NGROK_URL" != "null" ]; then
    echo "✅ ngrok URL: $NGROK_URL"
    echo "🌐 Testing API connection..."
    
    curl -X POST "$NGROK_URL/api/simple-chat" \
      -H "Content-Type: application/json" \
      -d '{"message": "test"}'
else
    echo "❌ ngrok not running"
fi
``` 