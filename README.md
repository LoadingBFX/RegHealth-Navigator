# RegHealth Navigator

RegHealth Navigator 是一个智能监管文档分析工具，帮助用户快速理解和分析复杂的监管文档。该工具使用 AI 技术来解析、总结和比较监管文档，提供直观的可视化界面和交互式分析功能。

## 功能特点

- 📄 文档上传与解析：支持 XML 格式的监管文档上传和自动解析
- 🔍 智能分析：使用 AI 技术分析文档内容，提取关键信息
- 🗺️ 思维导图：自动生成文档结构的思维导图
- 💬 智能对话：支持与文档内容的自然语言交互
- 📊 文档比较：支持多文档对比分析
- 🎯 重点标记：自动识别和标记重要内容

## 技术栈

### 前端
- React 18
- TypeScript
- Tailwind CSS
- Vite
- React Query
- React Router

### 后端
- FastAPI
- Python 3.8+
- XML 处理库
- 向量数据库
- LLM 集成

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.8+
- npm 或 yarn

### 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/你的用户名/RegHealth-Navigator.git
cd RegHealth-Navigator
```

2. 安装后端依赖
```bash
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd front
npm install
```

### 运行开发环境

1. 启动后端服务
```bash
# 在项目根目录
uvicorn app.main:app --reload
```

2. 启动前端开发服务器
```bash
# 在 front 目录
npm run dev
```

访问 http://localhost:5173 查看应用。

## 部署指南

### GitHub Pages 部署

项目已配置 GitHub Actions 自动部署到 GitHub Pages。每次推送到 main 分支时，将自动触发部署流程。

1. 确保仓库设置中已启用 GitHub Pages
2. 在仓库设置中，找到 "Pages" 选项
3. 选择 "Deploy from a branch"
4. 选择 "gh-pages" 分支和 "/ (root)" 文件夹

### 后端部署

后端服务需要部署到支持 Python 的服务器。推荐使用以下平台之一：

- Heroku
- DigitalOcean
- AWS
- Google Cloud Platform

部署时需要注意：
1. 设置适当的环境变量
2. 配置 CORS 设置
3. 确保服务器有足够的内存和 CPU 资源

## 项目结构

```
RegHealth-Navigator/
├── app/                # FastAPI 后端应用
├── core/              # 核心业务逻辑
├── front/             # React 前端应用
│   ├── src/
│   │   ├── components/  # React 组件
│   │   ├── context/    # React Context
│   │   └── store/      # 状态管理
├── data/              # 数据文件
├── docs/              # 文档
└── scripts/           # 工具脚本
```

## 开发指南

### 代码规范

- 使用 ESLint 和 Prettier 进行代码格式化
- 遵循 TypeScript 严格模式
- 使用 Python 类型注解
- 编写单元测试

### 提交规范

提交信息格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目维护者：[你的名字]
- 邮箱：[你的邮箱]
- 项目链接：[GitHub 仓库链接] 