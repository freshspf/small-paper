# 基于大语言模型的 RDFS 本体学习与评估系统

## 1. 项目简介

本项目是一个面向硕士论文展示的原型系统，系统名称为“基于大语言模型的 RDFS 本体学习与评估系统”。

系统围绕 RDFS 本体公理评测任务展开，支持模型配置、数据集导入、提示词模板管理、评测任务发起、评测结果统计、解释标注与本体图谱可视化等功能。当前版本以第五章系统展示为目标，优先保证界面完整、流程清晰和截图效果。

## 2. 技术栈

### 前端

- Next.js（App Router）
- TypeScript
- Tailwind CSS
- ECharts
- Cytoscape.js

### 后端

- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

## 3. 项目目录结构

```text
chapter3v0323/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # 路由接口
│   │   ├── core/              # 配置项
│   │   ├── db/                # 数据库初始化与建表
│   │   ├── models/            # SQLAlchemy 模型
│   │   ├── schemas/           # Pydantic 数据结构
│   │   ├── scripts/           # 初始化脚本
│   │   ├── services/          # 业务逻辑
│   │   └── main.py            # 后端入口
│   ├── tests/                 # 最小接口测试脚本
│   └── requirements.txt       # 后端依赖
├── frontend/                  # Next.js 前端
│   ├── app/                   # 页面路由
│   ├── components/            # 页面组件
│   ├── lib/                   # 前端 API 与工具函数
│   └── package.json           # 前端依赖
├── chapter3/                  # 第三章实验资源目录
│   ├── prompts/               # 提示词模板文件
│   ├── results/               # 实验结果与可视化输出
│   ├── hard_case_scripts/     # hard case 实验脚本
│   ├── hard_case_stability_scripts/ # 稳定性实验脚本
│   └── visualization_scripts/ # 绘图脚本
└── README.md
```

## 4. 后端启动方式

### 4.1 安装依赖

```bash
pip install -r backend/requirements.txt
```

### 4.2 启动后端

```bash
python backend/app/main.py
```

启动后默认地址为：

```text
http://127.0.0.1:8000
```

健康检查接口：

```text
http://127.0.0.1:8000/api/v1/health
```

### 4.3 可选检查

可运行以下测试脚本检查后端主要功能：

```bash
python backend/tests/test_llm_models_api.py
python backend/tests/test_datasets_api.py
python backend/tests/test_prompt_templates_api.py
python backend/tests/test_live_evaluations_api.py
python backend/tests/test_evaluation_metrics_api.py
python backend/tests/test_annotations_api.py
python backend/tests/test_explanation_stats_api.py
```

## 5. 前端启动方式

### 5.1 安装依赖

```bash
cd frontend
npm install
```

### 5.2 启动前端

```bash
npm run dev
```

默认访问地址：

```text
http://localhost:3000
```

### 5.3 前端构建检查

```bash
npm run build
```

## 6. 主要功能说明

### 6.1 模型配置

支持新增、查看、编辑和删除大语言模型配置，主要字段包括：

- 模型名称
- 提供方
- Base URL
- API Key
- Model Name
- 默认模型标记

### 6.2 数据集管理

支持上传 CSV 数据集，系统会自动解析并写入数据库，可查看数据集列表及前 20 条样本预览。

CSV 字段包括：

- id
- axiom_type
- axiom_text
- subject
- predicate
- object
- label
- source
- context_info

### 6.3 提示词模板管理

系统内置三类提示词模板：

- 基础型提示词
- 指令增强型提示词
- 上下文引导型提示词

支持模板查看、编辑与默认模板设置。

### 6.4 评测任务

用户可选择：

- 模型
- 数据集
- 提示词模板

随后发起评测任务。系统会读取数据集样本，将公理文本和上下文信息填入提示词模板，调用大语言模型接口，并生成评测结果。

### 6.5 结果分析

系统支持对评测结果进行统计分析，主要指标包括：

- Accuracy
- Precision
- Recall
- F1

支持整体统计与按公理类型统计，并在前端页面中以图表和表格形式展示。

### 6.6 解释标注

系统支持对评测结果中的解释文本进行人工标注，标注类型包括：

- correct
- wrong
- hallucination

同时支持解释正确率与幻觉率统计。

### 6.7 本体图谱可视化

系统提供基于 Cytoscape.js 的本体图谱页面，当前使用静态演示数据展示类之间的 `subClassOf` 关系，适合论文截图展示。
