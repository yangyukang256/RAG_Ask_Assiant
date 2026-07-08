# 🧠 RAG 智能知识库问答系统

> 把你的文档变成 AI 知识库，像聊天一样提问，AI 自动从文档中找到答案！

## ✨ 这是什么？

这是一个**基于 RAG（检索增强生成）技术的智能问答系统**。简单来说就是：

1. 📄 **上传文档** — 把你的 PDF、Word、Excel、TXT 文件上传到系统
2. 🧩 **AI 自动处理** — 系统会自动读取、拆分、索引文档内容
3. 💬 **像聊天一样提问** — 用自然语言问问题，AI 会从你的文档中找到并回答
4. 📑 **附带引用来源** — 每个答案都会告诉你参考了文档的哪一部分，可信度一目了然

### 适合谁用？

- 公司内部知识库（员工手册、产品文档、培训资料）
- 个人学习笔记库
- 电商商品知识问答
- 任何想把文档变成"能聊天"的场景

---

## 🖼️ 系统预览

| 功能 | 说明 |
|------|------|
| 💬 智能对话 | 基于文档内容回答你的问题，答案附带引用来源 |
| 📚 知识库管理 | 上传/删除文档，查看文档状态和处理进度 |
| 🔍 知识检索 | 搜索文档内容，查看文档被切分后的片段 |
| 🔐 用户认证 | 登录/登出、修改密码 |

---

## 🛠️ 技术栈

| 部分 | 技术 |
|------|------|
| **前端** | React 19 + TypeScript + Vite + Ant Design 6 |
| **后端** | Python + FastAPI |
| **AI 模型** | 阿里云百炼（通义千问 qwen-plus + text-embedding-v2） |
| **向量数据库** | ChromaDB（存储文档向量） |
| **数据库** | SQLite（存储用户、会话、消息记录） |
| **文档处理** | LangChain（文档拆分、向量化、检索） |

---

## 🚀 快速上手（5 分钟搞定）

### 准备工作

你需要一个 **阿里云百炼的 API Key**（免费的就行）：
1. 打开 [阿里云百炼平台](https://bailian.aliyun.com/)
2. 注册登录后，在控制台创建一个 API Key
3. 复制保存好，后面要用

### 第一步：下载项目

```bash
git clone https://github.com/yangyukang256/RAG_Ask_Assiant.git
cd RAG_Ask_Assiant
```

### 第二步：启动后端

```bash
# 进入后端目录
cd backend

# 创建虚拟环境（第一次运行）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Mac / Linux:
# source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量（复制并编辑）
cp .env.example .env
```

📝 **编辑 `.env` 文件**，把你刚才申请的 API Key 填进去：

```env
DASHSCOPE_API_KEY=sk-你的API-KEY在这里
```

然后启动后端服务：

```bash
python -m app.main
```

看到 `[启动] RAG 知识库问答系统启动中...` 就说明成功了！🎉

> 后端默认运行在 http://localhost:8000，API 文档在 http://localhost:8000/docs

### 第三步：启动前端

**新开一个终端窗口**，不要关掉后端：

```bash
# 回到项目根目录，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

看到 `Local: http://localhost:5173/` 就说明成功了！🎉

### 第四步：开始使用

1. 打开浏览器访问 **http://localhost:5173**
2. 使用默认账号登录：用户名 `admin`，密码 `123456`
3. 在知识库页面上传你的文档（支持 PDF、Word、Excel、TXT）
4. 等待文档处理完成（状态变成"已完成"）
5. 进入对话页面，开始提问吧！💬

---

## 📂 项目结构

```
RAG_Ask_Assiant/
├── backend/                  # 后端（Python + FastAPI）
│   ├── app/
│   │   ├── main.py          # 启动入口
│   │   ├── config.py        # 配置文件（读取 .env）
│   │   ├── database.py      # 数据库初始化
│   │   ├── models/          # 数据模型
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── session.py   # 会话模型
│   │   │   ├── message.py   # 消息模型
│   │   │   ├── document.py  # 文档模型
│   │   │   └── chunk.py     # 文档片段模型
│   │   ├── routers/         # API 路由
│   │   │   ├── auth.py      # 登录注册接口
│   │   │   ├── chat.py      # 对话接口
│   │   │   └── knowledge_base.py  # 知识库接口
│   │   ├── services/        # 业务逻辑
│   │   │   ├── auth_service.py    # 用户认证服务
│   │   │   ├── chat_service.py    # 对话服务
│   │   │   ├── document_service.py # 文档处理服务
│   │   │   ├── llm_service.py     # AI 模型调用
│   │   │   └── rag_service.py     # RAG 检索增强生成
│   │   ├── schemas/         # 数据校验
│   │   └── core/            # 核心工具
│   ├── .env.example         # 环境变量模板
│   ├── requirements.txt     # Python 依赖列表
│   └── uploads/             # 上传文件存放目录
│
├── frontend/                # 前端（React + TypeScript）
│   ├── src/
│   │   ├── App.tsx          # 应用入口
│   │   ├── main.tsx         # 渲染入口
│   │   ├── pages/
│   │   │   ├── Login.tsx         # 登录页
│   │   │   ├── Chat.tsx          # 对话页
│   │   │   ├── KnowledgeBase.tsx # 知识库管理页
│   │   │   └── ChangePassword.tsx # 修改密码页
│   │   ├── stores/          # 状态管理（zustand）
│   │   ├── api/             # API 调用
│   │   ├── components/      # 公共组件
│   │   └── types/           # TypeScript 类型定义
│   ├── package.json
│   └── vite.config.ts
│
├── chroma_db/               # 向量数据库文件（自动生成）
├── .gitignore
└── README.md                # 就是本文件
```

---

## ❓ 常见问题

### Q：启动报错 "请配置 DASHSCOPE_API_KEY"？
A：你忘了配置 API Key！把 `.env.example` 复制成 `.env`，然后把你的阿里云百炼 API Key 填进去。

### Q：支持哪些文件格式？
A：支持 PDF（.pdf）、Word（.docx）、Excel（.xlsx）、纯文本（.txt）。文件最大 50MB。

### Q：API Key 怎么申请？要钱吗？
A：阿里云百炼有免费额度，个人使用完全够用。去 [bailian.aliyun.com](https://bailian.aliyun.com/) 注册就能申请。

### Q：前端端口被占用了怎么办？
A：Vite 会自动尝试下一个端口（比如 5174）。或者修改 `frontend/vite.config.ts` 中的端口配置。

### Q：上传文档后一直显示"处理中"？
A：检查后端终端有没有报错。常见原因：API Key 配置错误、文档格式不支持、文档太大。

---

## 📜 开源协议

本项目使用 MIT 协议开源。

---

## 💡 给开发者的提示

- 后端 API 文档地址：启动后端后访问 http://localhost:8000/docs（Swagger 界面）
- 如需修改 AI 模型，编辑 `backend/.env` 中的 `LLM_MODEL_NAME` 和 `EMBEDDING_MODEL_NAME`
- 要支持更多文档格式，可以在 `backend/requirements.txt` 中添加对应的解析库
- 生产环境部署时，请修改 `JWT_SECRET_KEY` 和默认密码

---

**如果这个项目对你有帮助，欢迎给个 ⭐ Star！**