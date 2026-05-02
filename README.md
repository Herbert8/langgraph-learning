# LangGraph 学习演示

从基础到 ReAct 模式的 LangGraph 学习项目。

## 演示文件

| 文件 | 复杂度 | 说明 |
|------|--------|------|
| `demo_clean.py` | ⭐ | 核心概念：State、Node、Edge |
| `demo_advanced.py` | ⭐⭐⭐ | 审批流程：多级分支、循环、状态累积 |
| `demo_react.py` | ⭐⭐⭐⭐ | ReAct 模式：LLM 动态决策 + 工具调用 |

## 快速开始

```bash
# 安装依赖
uv sync

# 运行基础演示
uv run demo_clean.py

# 运行进阶演示
uv run demo_advanced.py

# 运行 ReAct 演示（需要 Ollama）
uv run demo_react.py

# 交互式 ReAct 模式
uv run demo_react.py interactive
```

## 环境要求

- Python >= 3.12
- Ollama (仅 ReAct 演示需要)
- 模型：gemma4:26b-a4b-it-q4_K_M

## 学习路径

1. 先看 `demo_clean.py` 理解核心概念
2. 再看 `demo_advanced.py` 理解复杂流程
3. 最后看 `demo_react.py` 理解 ReAct 模式

## 核心概念

- **State**: 数据在图中流动的载体
- **Node**: 处理状态的函数
- **Edge**: 连接节点，定义执行流程
- **ReAct**: LLM 动态决策 + 工具调用的循环模式
