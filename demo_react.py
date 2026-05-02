"""
LangGraph ReAct 模式演示

ReAct = Reasoning + Acting
- Thought（思考）：分析情况，决定下一步
- Action（行动）：执行具体操作
- Observation（观察）：获取结果
- 循环直到完成任务

使用本地 Ollama (gemma4:26b) 运行
"""

from typing import TypedDict, Annotated, Literal
from operator import add
import math
import random

from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode


# ============================================================
# 1. 定义 ReAct 状态
# ============================================================

class ReActState(TypedDict):
    """ReAct 循环状态"""
    messages: Annotated[list, add]  # 对话历史（Thought + Action + Observation）
    iteration: int                   # 迭代次数（防止无限循环）


# ============================================================
# 2. 定义工具（Tools）
# ============================================================

@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式
    支持基本运算：+, -, *, /, 以及 math 模块的函数

    例如：
    - "2 + 3"
    - "math.sqrt(16)"
    - "100 * 0.8"
    """
    try:
        # 安全检查：只允许特定字符
        allowed_chars = set("0123456789+-*/.() sqrt ")
        if any(c not in allowed_chars and not c.startswith("math.") for c in expression):
            return "错误：表达式包含不允许的字符"

        result = eval(expression, {"__builtins__": {}}, {"math": math})
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气（模拟数据）"""
    weather_data = {
        "北京": "晴天，温度 25°C",
        "上海": "多云，温度 28°C",
        "深圳": "阵雨，温度 30°C",
        "杭州": "晴天，温度 26°C",
    }
    return weather_data.get(city, f"抱歉，没有 {city} 的天气数据")


@tool
def get_current_time() -> str:
    """获取当前时间（模拟）"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def roll_dice(sides: int = 6) -> str:
    """掷骰子，返回随机数"""
    result = random.randint(1, sides)
    return f"掷出了 {result}（{sides}面骰子）"


# 汇总所有工具
tools = [calculator, get_weather, get_current_time, roll_dice]


# ============================================================
# 3. 初始化 LLM
# ============================================================

def create_llm():
    """创建 Ollama LLM 实例"""
    return ChatOllama(
        model="gemma4:26b-a4b-it-q4_K_M",
        temperature=0,
    )


# ============================================================
# 4. ReAct 节点函数
# ============================================================

def call_model_node(state: ReActState) -> dict:
    """
    思考节点：LLM 分析当前情况，决定下一步行动

    这里体现了 ReAct 的 "Thought" 部分
    """
    messages = state["messages"]
    llm = create_llm()

    # 绑定工具到 LLM
    llm_with_tools = llm.bind_tools(tools)

    # 调用 LLM
    response = llm_with_tools.invoke(messages)

    print(f"\n{'='*60}")
    print(f"[Thought] LLM 思考:")
    if hasattr(response, 'content'):
        print(f"  {response.content}")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"  [决定执行工具]")
        for tool_call in response.tool_calls:
            print(f"    → {tool_call['name']}({tool_call['args']})")
    print(f"{'='*60}")

    return {"messages": [response]}


# 创建工具节点（处理工具调用）
tool_node = ToolNode(tools)


# ============================================================
# 5. 条件路由：决定下一步
# ============================================================

def should_continue(state: ReActState) -> Literal["tools", "end"]:
    """
    路由函数：根据 LLM 的输出决定下一步

    - 如果 LLM 调用了工具 → 去工具节点
    - 如果 LLM 直接回答 → 结束
    """
    messages = state["messages"]
    last_message = messages[-1]

    # 检查最后一条消息是否有工具调用
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"

    # 检查迭代次数，防止无限循环
    if state.get("iteration", 0) >= 10:
        print("\n[警告] 达到最大迭代次数，强制结束")
        return "end"

    return "end"


def check_iteration(state: ReActState) -> Literal["continue", "end"]:
    """工具执行后，决定是否继续"""
    iteration = state.get("iteration", 0)

    if iteration >= 10:
        return "end"
    return "continue"


# ============================================================
# 6. 构建 ReAct 图
# ============================================================

def build_react_graph() -> StateGraph:
    """构建 ReAct 循环图"""

    builder = StateGraph(ReActState)

    # 添加节点
    builder.add_node("agent", call_model_node)
    builder.add_node("tools", tool_node)

    # 设置入口
    builder.set_entry_point("agent")

    # 添加条件边：agent → tools 或 end
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        }
    )

    # 工具执行后回到 agent（形成循环）
    builder.add_conditional_edges(
        "tools",
        check_iteration,
        {
            "continue": "agent",
            "end": END,
        }
    )

    return builder.compile()


# ============================================================
# 7. 演示函数
# ============================================================

def demo_react():
    """演示 ReAct 模式"""

    print("\n" + "="*70)
    print("LangGraph ReAct 模式演示")
    print("="*70)
    print("""
ReAct 循环：
  1. Thought: LLM 分析问题，决定是否需要使用工具
  2. Action: 执行工具调用
  3. Observation: 获取工具结果
  4. 重复直到完成任务

可用工具：
  - calculator: 数学计算
  - get_weather: 查询天气
  - get_current_time: 获取时间
  - roll_dice: 掷骰子
    """)

    graph = build_react_graph()

    # 测试问题列表
    questions = [
        "帮我计算 100 乘以 0.8 再加上 50",
        "北京今天天气怎么样？",
        "掷一个 20 面骰子",
        "现在几点了？",
    ]

    for i, question in enumerate(questions, 1):
        print("\n" + "="*70)
        print(f"问题 {i}: {question}")
        print("="*70)

        initial_state = {
            "messages": [HumanMessage(content=question)],
            "iteration": 0
        }

        try:
            final_state = graph.invoke(initial_state)

            print("\n" + "-"*70)
            print("最终回答:")
            # 获取最后一条 AI 消息
            for msg in reversed(final_state["messages"]):
                if hasattr(msg, 'content') and msg.content and isinstance(msg, AIMessage):
                    print(f"  {msg.content}")
                    break
            print("-"*70)

        except Exception as e:
            print(f"\n[错误] {str(e)}")


def interactive_demo():
    """交互式演示"""
    print("\n" + "="*70)
    print("ReAct 交互模式")
    print("="*70)
    print("输入问题，LLM 会使用工具来回答")
    print("输入 'quit' 退出\n")

    graph = build_react_graph()

    while True:
        try:
            question = input("\n你的问题: ").strip()

            if question.lower() in ['quit', 'exit', 'q']:
                print("退出交互模式")
                break

            if not question:
                continue

            initial_state = {
                "messages": [HumanMessage(content=question)],
                "iteration": 0
            }

            print("\n[开始思考...]")
            final_state = graph.invoke(initial_state)

            print("\n[回答]")
            for msg in reversed(final_state["messages"]):
                if hasattr(msg, 'content') and msg.content and isinstance(msg, AIMessage):
                    print(f"{msg.content}")
                    break

        except KeyboardInterrupt:
            print("\n\n退出交互模式")
            break
        except Exception as e:
            print(f"[错误] {str(e)}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_demo()
    else:
        demo_react()

    print("\n" + "="*70)
    print("ReAct 模式关键点")
    print("="*70)
    print("""
【核心思想】
  LLM 不是一次性给出答案，而是：
  1. 先思考（Thought）
  2. 决定需要什么信息（Action）
  3. 获取工具结果（Observation）
  4. 基于结果继续思考，直到完成任务

【实现方式】
  - Agent 节点：LLM 决策，可能调用工具
  - Tool 节点：执行工具调用
  - 条件边：根据是否有工具调用决定路由
  - 循环：Tool → Agent → Tool → ...

【与之前演示的区别】
  之前：预设规则，固定流程
  ReAct：LLM 动态决策，自适应流程

【应用场景】
  - 需要多步推理的任务
  - 需要获取外部信息的任务
  - 需要调用 API 的任务
  - 复杂问题分解
""")
