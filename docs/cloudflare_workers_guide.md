# Cloudflare Workers 完整指南

## 🎯 什么是 Cloudflare Workers？

Cloudflare Workers 是一个**边缘计算平台**，可以：
- 🌍 在全球 200+ 个数据中心运行你的代码
- 🔒 自动处理 SSL、CDN、DDoS 防护
- 💰 完全免费（每天 100,000 个请求）
- 🚀 无需管理服务器
- ⚡ 超低延迟（通常 < 10ms）

## 🚀 快速开始

### 1. 安装 Wrangler CLI
```bash
# 安装 Wrangler
npm install -g wrangler

# 登录到 Cloudflare
wrangler login
```

### 2. 部署 Workers
```bash
# 进入 workers 目录
cd workers

# 部署
./deploy.sh
```

### 3. 测试 API
```bash
# 测试简单聊天
curl https://reghealth-navigator-api.your-subdomain.workers.dev/api/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 测试主聊天
curl https://reghealth-navigator-api.your-subdomain.workers.dev/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Medicare?"}'
```

## 🔧 配置前端

### GitHub Pages
```bash
# 进入仓库 Settings → Secrets and variables → Actions
# 添加: VITE_API_BASE_URL = https://reghealth-navigator-api.your-subdomain.workers.dev
```

### Cloudflare Pages
```bash
# 在 Cloudflare Pages 仪表板中
# 环境变量: VITE_API_BASE_URL = https://reghealth-navigator-api.your-subdomain.workers.dev
```

## 📁 项目结构

```
workers/
├── worker.js          # 主要的 Worker 代码
├── wrangler.toml      # 配置文件
└── deploy.sh          # 部署脚本
```

## 🔍 Workers 代码详解

### 主要功能
1. **CORS 处理** - 允许前端跨域访问
2. **路由处理** - 根据路径分发请求
3. **JSON 解析** - 处理请求和响应
4. **错误处理** - 统一的错误响应

### API 端点
- `GET /` - 健康检查
- `POST /api/simple-chat` - 简单测试
- `POST /api/chat` - 主聊天功能

## 🛠️ 高级功能

### 1. 环境变量
```toml
# wrangler.toml
[vars]
ENVIRONMENT = "production"
API_VERSION = "1.0.0"
```

### 2. 密钥管理
```bash
# 设置 OpenAI API 密钥
wrangler secret put OPENAI_API_KEY

# 在代码中使用
const apiKey = env.OPENAI_API_KEY;
```

### 3. KV 存储
```toml
# wrangler.toml
[[kv_namespaces]]
binding = "REGHEALTH_DATA"
id = "your-kv-namespace-id"
```

```javascript
// 在代码中使用
await env.REGHEALTH_DATA.put("key", "value");
const value = await env.REGHEALTH_DATA.get("key");
```

### 4. R2 存储
```toml
# wrangler.toml
[[r2_buckets]]
binding = "REGHEALTH_FILES"
bucket_name = "reghealth-files"
```

```javascript
// 存储文件
await env.REGHEALTH_FILES.put("file.txt", "content");

// 读取文件
const file = await env.REGHEALTH_FILES.get("file.txt");
```

## 🔄 集成 OpenAI API

### 完整版本示例
```javascript
// 在 worker.js 中添加
async function callOpenAI(query, env) {
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: 'gpt-3.5-turbo',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful assistant for Medicare regulations.'
        },
        {
          role: 'user',
          content: query
        }
      ],
      max_tokens: 1000
    })
  });

  const data = await response.json();
  return data.choices[0].message.content;
}

// 更新 handleChat 函数
async function handleChat(request, env) {
  try {
    const data = await request.json();
    
    if (!data.query) {
      return new Response(JSON.stringify({ error: 'Missing query field' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    // 调用 OpenAI API
    const response = await callOpenAI(data.query, env);

    return new Response(JSON.stringify({ response }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
}
```

## 📊 监控和分析

### 1. Cloudflare 仪表板
- 访问 [Cloudflare Dashboard](https://dash.cloudflare.com)
- 查看 Workers 分析
- 监控请求数量、错误率、响应时间

### 2. 日志
```javascript
// 在代码中添加日志
console.log('Request received:', request.url);
console.log('Processing query:', data.query);
```

### 3. 错误追踪
```javascript
// 捕获和记录错误
try {
  // 你的代码
} catch (error) {
  console.error('Error:', error);
  // 返回错误响应
}
```

## 🔒 安全考虑

### 1. API 密钥保护
```bash
# 使用 wrangler secret 存储敏感信息
wrangler secret put OPENAI_API_KEY
wrangler secret put DATABASE_URL
```

### 2. 请求验证
```javascript
// 验证请求来源
const origin = request.headers.get('Origin');
const allowedOrigins = ['https://yourdomain.com', 'https://*.pages.dev'];

if (!allowedOrigins.some(allowed => origin?.includes(allowed))) {
  return new Response('Unauthorized', { status: 403 });
}
```

### 3. 速率限制
```javascript
// 简单的速率限制
const clientIP = request.headers.get('CF-Connecting-IP');
const rateLimitKey = `rate_limit:${clientIP}`;

// 检查速率限制
const requests = await env.KV.get(rateLimitKey) || 0;
if (requests > 100) { // 每分钟100次请求
  return new Response('Rate limit exceeded', { status: 429 });
}

// 更新计数器
await env.KV.put(rateLimitKey, requests + 1, { expirationTtl: 60 });
```

## 💰 成本分析

### 免费层限制
- **请求数**: 每天 100,000 个请求
- **CPU 时间**: 每天 10,000,000 CPU 毫秒
- **内存**: 128MB 内存
- **脚本大小**: 1MB

### 付费层
- **Workers Paid**: $5/月
- **额外请求**: $0.50/百万请求
- **额外 CPU**: $12.50/百万 CPU 毫秒

## 🚨 限制和注意事项

### 1. 执行时间限制
- 免费版: 10 秒
- 付费版: 30 秒

### 2. 内存限制
- 免费版: 128MB
- 付费版: 1GB

### 3. 网络请求
- 支持 fetch API
- 可以调用外部 API
- 有网络超时限制

### 4. 文件系统
- 无本地文件系统
- 使用 KV 或 R2 存储数据

## 🔄 从 Flask 迁移

### 主要差异
| Flask | Cloudflare Workers |
|-------|-------------------|
| Python | JavaScript |
| 本地文件系统 | KV/R2 存储 |
| 长时间运行 | 无状态 |
| 传统服务器 | 边缘计算 |

### 迁移步骤
1. **转换路由逻辑**
2. **替换文件操作**
3. **调整数据库连接**
4. **测试和部署**

## 🎯 最佳实践

### 1. 代码组织
```javascript
// 分离关注点
const handlers = {
  '/api/chat': handleChat,
  '/api/simple-chat': handleSimpleChat,
};

// 主处理函数
async function handleRequest(request, env) {
  const url = new URL(request.url);
  const handler = handlers[url.pathname];
  
  if (handler) {
    return handler(request, env);
  }
  
  return new Response('Not found', { status: 404 });
}
```

### 2. 错误处理
```javascript
// 统一的错误处理
function createErrorResponse(message, status = 500) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
}
```

### 3. 性能优化
```javascript
// 缓存响应
const cacheKey = `cache:${request.url}`;
const cached = await env.KV.get(cacheKey);

if (cached) {
  return new Response(cached, {
    headers: { ...corsHeaders, 'Content-Type': 'application/json' },
  });
}

// 处理请求并缓存
const response = await processRequest(request);
await env.KV.put(cacheKey, JSON.stringify(response), { expirationTtl: 3600 });
```

## 📞 支持和资源

### 官方文档
- [Cloudflare Workers 文档](https://developers.cloudflare.com/workers/)
- [Wrangler CLI 文档](https://developers.cloudflare.com/workers/wrangler/)
- [Workers 示例](https://developers.cloudflare.com/workers/examples/)

### 社区资源
- [Cloudflare Community](https://community.cloudflare.com/)
- [Workers Discord](https://discord.gg/cloudflare)

### 调试工具
```bash
# 本地开发
wrangler dev

# 查看日志
wrangler tail

# 测试部署
wrangler deploy --dry-run
``` 