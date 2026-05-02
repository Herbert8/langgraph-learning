# LangGraph 学习会话记录

## 用户目标
接手一个 LangGraph 0.x 编写的项目，需要快速学习 LangGraph。

## 学习进度 (2026-05-02)

### 已完成
1. ✅ 确认 LangGraph 1.x 是主流版本
2. ✅ 理解 0.x 和 1.x 基本向后兼容
3. ✅ 学习 LangGraph 核心概念：
   - State（状态）
   - Node（节点）
   - Edge（边）
   - 条件边
   - 循环控制
4. ✅ 理解 ReAct 模式与固定流程的区别

### 创建的演示项目
- 仓库：https://github.com/Herbert8/langgraph-learning
- 文件：
  - `demo_clean.py` - 核心概念
  - `demo_advanced.py` - 审批流程（多级分支+循环）
  - `demo_react.py` - ReAct 模式（LLM 动态决策）

## 环境配置
- LangGraph 版本：1.1.10
- Python：3.12
- LLM：Ollama + gemma4:26b-a4b-it-q4_K_M
- Claude Code 默认模型：glm-4.7

## 下一步建议

### 立即可做
1. 查看 0.x 项目代码，识别核心概念
2. 对照迁移指南：https://docs.langchain.com/oss/python/migrate/langgraph-v1
3. 注意 0.x 中可能用到的：
   - `create_react_agent` → 改用 `langchain.agents.create_agent`
   - `MessageGraph` → 改用 `StateGraph` with `messages` key

### 关键理解
- ReAct 的"动态" = LLM 决定调用哪个工具
- 循环 = 条件边指回之前的节点
- 固定流程 vs ReAct：代码决策 vs LLM 决策
