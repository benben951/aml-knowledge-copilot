# AML/DD Knowledge Copilot

> 🏦 **金融风控知识问答Agent** — 反洗钱/尽调合规知识检索与问答系统

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-orange.svg)](https://www.langchain.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 项目简介

AML/DD Knowledge Copilot 是一个面向**反洗钱（AML）和尽职调查（DD）**场景的知识问答系统。解决审核人员真实痛点：

- 📚 **知识分散** — 制度文件、法规、案例散落在多个系统
- ❓ **口径不一致** — 同一问题不同人员回答不同
- 📅 **版本追踪难** — 法规更新后难以追溯历史版本
- 🔗 **证据链缺失** — 审核决策缺乏可追溯的依据

### 核心定位

> **不是通用聊天机器人，而是合规知识检索与解释助手**

重点解决：**可引用、可审计、可控风险**

---

## ✨ 核心功能

### MVP 功能（P0）

| 功能 | 描述 |
|------|------|
| 📄 **文档管理** | 上传 PDF/DOCX/TXT 文件，自动解析和切块 |
| 🔍 **智能检索** | 基于向量相似度的语义检索 |
| 💬 **RAG 问答** | 检索增强生成，返回答案 + 引用来源 |
| 📊 **引用追溯** | 显示答案来源（文档名 + 页码 + 段落） |
| 🖥️ **Web 界面** | Streamlit 构建的简单演示界面 |

### 增强功能（P1）

| 功能 | 描述 |
|------|------|
| 🏷️ **元数据过滤** | 按文档类型/国家/法规主题过滤检索范围 |
| ⚠️ **答案护栏** | 证据不足时提示人工复核 |
| 📝 **审计日志** | 记录问题、检索结果、回答、引用 |
| 📈 **评测脚本** | 准备 20-30 条 AML/DD 业务问答，测试命中率 |

---

## 🛠️ 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| **后端框架** | FastAPI | 标准 API 接口，清晰可扩展 |
| **RAG 编排** | LangChain | 生态成熟，方便展示检索链路 |
| **向量数据库** | Qdrant | 支持元数据过滤，适合面试讲解 |
| **关系数据库** | PostgreSQL | 文档元数据管理 |
| **前端界面** | Streamlit | 快速搭建演示界面 |
| **文档解析** | PyMuPDF + python-docx | PDF/Word 解析 |
| **LLM 接口** | OpenAI API（默认） | 可切换本地模型 |

---

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+
- Docker（用于 Qdrant）

### 2. 安装依赖

```bash
# 克隆项目
git clone https://github.com/benben951/aml-knowledge-copilot.git
cd aml-knowledge-copilot

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 3. 启动 Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的 OPENAI_API_KEY
```

### 5. 启动后端

```bash
cd backend
uvicorn app.main:app --reload
```

### 6. 启动前端

```bash
cd frontend
streamlit run streamlit_app.py
```

---

## 📁 项目结构

```
aml-knowledge-copilot/
├── backend/
│   └── app/
│       ├── api/routes/         # API 路由（文档管理、问答）
│       ├── core/               # 配置、日志、安全、Prompt
│       ├── domain/models/      # 领域模型
│       ├── services/
│       │   ├── document/       # 文档处理、解析、切块、入库
│       │   ├── retrieval/      # 检索、引用、组装
│       │   └── answer/         # 问答链、答案护栏
│       └── infra/
│       │   ├── vector/         # 向量数据库（Qdrant）
│       │   ├── db/             # 关系数据库（PostgreSQL）
│       │   └── llm/            # LLM 接口
│       └── main.py             # FastAPI 入口
├── frontend/
│   └── streamlit_app.py        # Streamlit 界面
├── data/
│   └── samples/                # 示例文档
├── scripts/
│   ├── ingest_demo_data.py     # 导入示例数据
│   └── eval_rag.py             # 评测脚本
├── tests/                      # 单元测试
├── requirements.txt            # Python 依赖
├── pyproject.toml              # 项目配置
└── README.md
```

---

## 💡 面试亮点

### 1. 业务理解

> "AML/DD 审核人员的真实痛点不是不会提问，而是知识分散、口径不一致、制度版本多、证据链难追溯。"

- 设计了元数据过滤（按国家/法规类型）
- 设计了答案护栏（证据不足时提示人工复核）
- 这些都是合规场景特有的设计

### 2. 技术选型

- **Qdrant 而非 Pinecone**：独立部署，支持元数据过滤
- **LangChain**：展示对 RAG 链路的理解（Retriever、Prompt、Citation）
- **FastAPI**：标准 API 设计，便于扩展

### 3. 可演示性

- 准备 20-30 条真实 AML/DD 问答示例
- 可现场演示：上传文档 → 提问 → 查看引用来源

### 4. 简历描述

```
AML/DD Knowledge Copilot（风控知识问答Agent）
GitHub: github.com/benben951/aml-knowledge-copilot

技术栈：Python、FastAPI、LangChain、Qdrant、Streamlit

核心功能：
• 反洗钱/尽调知识库构建（支持 PDF/Word/TXT 上传）
• RAG 检索增强问答，返回引用来源（文档 + 页码 + 段落）
• 合规场景特有设计：元数据过滤、答案护栏、审计日志
• 参考 Anthropic Claude Cookbooks 的 Skill 设计范式
```

---

## 📚 参考资料

- [Anthropic Claude Cookbooks](https://github.com/anthropics/claude-cookbooks) — Skill 开发范式
- [SkillHub](https://github.com/iFLYTEK-SkillHub/SkillHub) — Skill 注册中心架构
- [LangChain Documentation](https://python.langchain.com/) — RAG 编排
- [Qdrant Documentation](https://qdrant.tech/documentation/) — 向量数据库

---

## 📄 License

MIT License

---

## 🙋 作者

**苏轻** — 金融风控 / AI应用落地

- 💼 目标岗位：Risk Intelligence Analyst, Compliance Analytics
- 🎯 求职方向：金融风控/合规场景的数据分析 + AI应用

---

> 💡 **一句话总结**：这不是玩具项目，而是面向合规场景的垂直领域问答系统，重点是"可引用、可审计、可控风险"。