# 小论文进度追踪

## 环境

- Python venv: `.venv/` (Python 3.9.6，待升级到 3.12)
- Git remote: `https://github.com/freshspf/small-paper.git`
- 后端依赖未安装，前端 `node_modules` 未安装

## 当前状态

- [x] 项目初始化（git、CLAUDE.md、Python venv、.gitignore）
- [x] 代码推送到 GitHub
- [ ] Python 升级到 3.12
- [ ] 从微信接收并解压 `chapter3_data.zip` (329MB)
- [ ] 安装后端依赖 + 启动验证
- [ ] 阅读毕业论文第四章内容
- [ ] 阅读两篇参考论文的架构与写作方法
- [ ] 撰写小论文
- [ ] 对照模板格式排版

## 数据文件

数据文件通过微信传输，不在 git 中：

| 文件 | 大小 | 内容 | 状态 |
|---|---|---|---|
| `chapter3_data.zip` | 329MB | 实验数据 (chapter3 + chapter4 data) | 待接收 |
| `chapter3v0323.zip` | 687MB | 原始项目包 | 已存在（gitignore） |

收到后解压：`cd chapter3v0323 && unzip ../chapter3_data.zip`

## 待办

1. Python 升级到 3.12，重建 venv
2. 从 `马宁毕业论文v0508-2(1).docx` 提取第四章核心内容
3. 参考 `example/` 中两篇论文的结构设计小论文大纲
4. 按《计算机科学》模板格式撰写，目标 7 页
