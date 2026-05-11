# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是马宁的计算机科学硕士小论文项目 —— **RDFS 本体学习与评估系统**。目标是撰写一篇7页左右的小论文，将毕业论文第四章的核心内容以符合《计算机科学》期刊格式的方式呈现。项目包含一个完整的前后端系统用于本体学习任务的执行与评测。

## 论文撰写

### 源材料
- **毕业论文**: `/Users/joer/小论文/马宁毕业论文v0508-2(1).docx` — 第四章相关内容是核心素材
- **模板**: `/Users/joer/小论文/模板.doc` — 《计算机科学》期刊模板
- **参考论文**: `/Users/joer/小论文/example/` — 两篇参考论文，比照其架构与写作方法：
  - `大语言模型驱动的多元关系知识图谱补全方法.pdf`
  - `基于大语言模型增强的零样本知识抽取方法.pdf`
- **任务要求**: `/Users/joer/小论文/任务要求.md`

### 写作约束
- 篇幅：不含参考文献约7页
- 参考 example 中两篇论文的结构与写作方法

## 系统项目 (chapter3v0323)

这是一个 RDFS 本体学习与评估的全栈管理系统，用于论文第四章的实验评估与可视化。

### 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3, FastAPI, SQLAlchemy (ORM), Pydantic v2 |
| 前端 | Next.js 15 (App Router), React 19, Tailwind CSS 3, TypeScript |
| 可视化 | ECharts (图表), Cytoscape.js (知识图谱) |
| 数据库 | SQLite (默认) 或 MySQL |
| UI 组件 | 自定义组件 + Radix UI |

### 后端架构 (`chapter3v0323/backend/`)

```
backend/
  app/
    main.py              # FastAPI 入口，CORS，启动事件，seed 数据
    core/config.py       # Settings (pydantic-settings)，从 .env 加载
    api/
      router.py          # 所有路由的聚合注册
      routes/            # 按领域拆分的路由模块
    models/              # SQLAlchemy ORM 模型 (每个表一个文件)
    schemas/             # Pydantic 数据校验/序列化 (请求/响应)
    services/            # 业务逻辑层 (每个域一个 service)
    db/
      base_class.py      # Base (DeclarativeBase) + TimestampMixin
      session.py         # SQLAlchemy session & engine
      init_*.py          # 内置种子数据初始化
      create_tables.py   # SQLite schema 兼容性修复
    utils/
    scripts/             # 一次性初始化脚本
  tests/                 # API 测试脚本
  requirements.txt
  .env / .env.example
```

- **API 前缀**: `/api/v1`
- **路由注册**: `app/api/router.py` 中统一注册所有子路由
- **数据模型层级**: SQLAlchemy Model (models/) → Pydantic Schema (schemas/) → API Route (routes/) → 调用 Service (services/)
- **启动时自动**: 创建表 → 确保 SQLite schema → seed 提示词模板、LLM 模型、模型配置、提示词模板配置

### 前端架构 (`chapter3v0323/frontend/`)

```
frontend/
  app/
    layout.tsx                       # 根布局
    globals.css
    (dashboard)/
      layout.tsx                     # 侧边栏 + 顶栏布局
      page.tsx                       # 首页仪表盘
      models/page.tsx                # 模型管理
      prompt-templates/page.tsx      # 提示词模板管理
      datasets/page.tsx              # 评测数据管理 (列表)
      datasets/[id]/page.tsx         # 数据集详情
      evaluations/page.tsx           # 评测任务列表
      evaluations/new/page.tsx       # 创建评测任务
      evaluations/[id]/page.tsx      # 评测详情/结果
      ontology/page.tsx              # 本体学习任务
      exports/page.tsx               # 导出中心
      annotations/page.tsx           # 标注工作台
      stability/page.tsx             # 稳定性评估
  components/
    layout/sidebar.tsx               # 左侧导航 (7 个路由)
    layout/topbar.tsx
    dashboard/                       # 仪表盘组件
    datasets/                        # 数据集表格/查看器
    evaluations/                     # 评测相关组件 (启动器/图表/结果/报告)
    annotations/                     # 标注工作区
    models/                          # 模型表格
    ontology/                        # 本体任务管理/结果面板/导出
    stability/                       # 稳定性评估面板
    prompt-templates/                # 模板管理器
    exports/                         # 导出面板
    ui/                              # 通用 UI 原子组件 (badge, button, card, page-title, placeholder-panel)
  lib/
    api.ts                           # 所有 API 调用的集中封装
    utils.ts                         # 工具函数 (cn 等)
    mock-data.ts                     # API 不可用时的 fallback 模拟数据
  next.config.ts
  tailwind.config.ts
  tsconfig.json
```

- **路由**: Next.js App Router，路由组 `(dashboard)` 共享侧边栏+顶栏布局
- **API 层**: `lib/api.ts` 包含所有 API 类型定义和函数 (~2900 行)，每个 API 调用失败时自动回退到 mock-data
- **API_BASE_URL**: 默认 `http://127.0.0.1:8000/api/v1`，通过 `NEXT_PUBLIC_API_BASE_URL` 环境变量覆盖

### 关键开发命令

**后端**:
```bash
# 安装依赖
pip install -r chapter3v0323/backend/requirements.txt

# 启动 API (开发模式)
uvicorn app.main:app --app-dir chapter3v0323/backend --reload --port 8000

# 或直接运行
python chapter3v0323/backend/app/main.py
```

**前端**:
```bash
cd chapter3v0323/frontend
npm install
npm run dev       # 开发服务器 http://localhost:3000
npm run build     # 生产构建
npm run lint      # ESLint 检查
```

### 数据库
- 默认使用 SQLite (`backend/app.db`)，自动创建
- 切换到 MySQL：修改 `.env` 中的 `DATABASE_URL` 为 `mysql+pymysql://root:password@127.0.0.1:3306/chapter3v0323?charset=utf8mb4`

### 系统功能模块

| 模块 | 路由前缀 | 说明 |
|---|---|---|
| 模型管理 | `/models` | LLM 模型和模型配置的 CRUD |
| 评测数据集 | `/eval-datasets` | 数据集上传（CSV）、记录浏览、筛选 |
| 常规数据集 | `/datasets` | 另一套数据集管理，含预览功能 |
| 评测任务 | `/eval-tasks` | 创建、启动、停止、查看分类评测结果 |
| 解释评估 | `/explanation-evals` | LLM 解释正确性 + 幻觉标注 |
| 稳定性评估 | `/stability-evals` | 扰动模板一致性测试 |
| 本体学习 | `/ontology-tasks` | Baseline 和三层分层学习，PDF 输入 |
| 本体结果 | `/ontology-results` | 公理/图谱查看、导出 |
| 提示词配置 | `/prompt-templates/configs` | 三层提示词模板配置管理 |
| 提示词模板 | `/prompt-templates` | 基础提示词模板 CRUD |
| 评估报告 | `/eval-reports` | 汇总分类+解释+稳定性三维报告 |
