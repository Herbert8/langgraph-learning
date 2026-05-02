"""
LangGraph 基础概念演示 - 最简版

避免循环，专注理解核心概念
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END

# ============================================================
# 1. State（状态）定义
# ============================================================

class SimpleState(TypedDict):
    """简单状态"""
    value: int
    steps: list[str]


# ============================================================
# 2. Node（节点）定义
# ============================================================

def step1(state: SimpleState) -> dict:
    """步骤 1"""
    new_value = state["value"] + 10
    print(f"  [步骤1] {state['value']} + 10 = {new_value}")
    return {"value": new_value, "steps": ["步骤1：+10"]}


def step2(state: SimpleState) -> dict:
    """步骤 2"""
    new_value = state["value"] * 2
    print(f"  [步骤2] {state['value']} * 2 = {new_value}")
    return {"value": new_value, "steps": ["步骤2：*2"]}


def step3(state: SimpleState) -> dict:
    """步骤 3"""
    new_value = state["value"] - 5
    print(f"  [步骤3] {state['value']} - 5 = {new_value}")
    return {"value": new_value, "steps": ["步骤3：-5"]}


# ============================================================
# 3. 条件分支演示
# ============================================================

class BranchState(TypedDict):
    """分支状态"""
    value: int
    path: list[str]


def branch_node(state: BranchState) -> dict:
    """分支前的节点"""
    print(f"  [分支节点] 当前值: {state['value']}")
    return {"path": ["到达分支点"]}


def positive_node(state: BranchState) -> dict:
    """正数分支"""
    print(f"  [正数分支] 值为正: {state['value']}")
    return {"path": ["走正数分支"], "value": state["value"] + 100}


def negative_node(state: BranchState) -> dict:
    """负数分支"""
    print(f"  [负数分支] 值为负: {state['value']}")
    return {"path": ["走负数分支"], "value": state["value"] - 100}


def zero_node(state: BranchState) -> dict:
    """零值分支"""
    print(f"  [零分支] 值为零: {state['value']}")
    return {"path": ["走零分支"], "value": 0}


def check_value(state: BranchState) -> str:
    """
    条件边函数：根据值决定分支
    返回：节点名称（字符串）
    """
    if state["value"] > 0:
        return "positive"
    elif state["value"] < 0:
        return "negative"
    else:
        return "zero"


# ============================================================
# 4. 构建图
# ============================================================

def demo_linear():
    """演示 1：线性流程"""
    print("\n" + "="*60)
    print("演示 1：线性流程")
    print("="*60)
    print("\n流程: 步骤1 -> 步骤2 -> 步骤3 -> 结束\n")

    # 构建图
    builder = StateGraph(SimpleState)

    # 添加节点
    builder.add_node("step1", step1)
    builder.add_node("step2", step2)
    builder.add_node("step3", step3)

    # 连接节点（普通边）
    builder.set_entry_point("step1")   # 设置入口
    builder.add_edge("step1", "step2")   # step1 完成后执行 step2
    builder.add_edge("step2", "step3")   # step2 完成后执行 step3
    builder.add_edge("step3", END)       # step3 完成后结束

    # 编译
    graph = builder.compile()

    # 执行
    initial_state = {"value": 5, "steps": []}
    print(f"初始状态: value={initial_state['value']}\n")

    final_state = graph.invoke(initial_state)

    print(f"\n最终状态: value={final_state['value']}")
    print("\n执行步骤:")
    for step in final_state["steps"]:
        print(f"  ✓ {step}")


def demo_branching():
    """演示 2：条件分支"""
    print("\n" + "="*60)
    print("演示 2：条件分支")
    print("="*60)
    print("\n流程: 分支节点 --(根据值判断)--> 正数/负数/零 -> 结束\n")

    # 构建图
    builder = StateGraph(BranchState)

    # 添加节点
    builder.add_node("branch", branch_node)
    builder.add_node("positive", positive_node)
    builder.add_node("negative", negative_node)
    builder.add_node("zero", zero_node)

    # 设置入口
    builder.set_entry_point("branch")

    # 添加条件边
    builder.add_conditional_edges(
        "branch",        # 源节点
        check_value,     # 路由函数
        {                # 返回值到节点的映射
            "positive": "positive",
            "negative": "negative",
            "zero": "zero",
        }
    )

    # 所有分支都指向结束
    builder.add_edge("positive", END)
    builder.add_edge("negative", END)
    builder.add_edge("zero", END)

    # 编译
    graph = builder.compile()

    # 测试不同值
    for test_value in [10, -5, 0]:
        print(f"\n--- 测试值: {test_value} ---")
        initial_state = {"value": test_value, "path": []}
        final_state = graph.invoke(initial_state)

        print(f"最终值: {final_state['value']}")
        print("路径:")
        for p in final_state["path"]:
            print(f"  • {p}")


def demo_stream():
    """演示 3：使用 stream 查看中间状态"""
    print("\n" + "="*60)
    print("演示 3：Stream 模式（查看中间状态）")
    print("="*60 + "\n")

    builder = StateGraph(SimpleState)
    builder.add_node("step1", step1)
    builder.add_node("step2", step2)
    builder.add_node("step3", step3)

    builder.set_entry_point("step1")
    builder.add_edge("step1", "step2")
    builder.add_edge("step2", "step3")
    builder.add_edge("step3", END)

    graph = builder.compile()

    initial_state = {"value": 3, "steps": []}

    print("使用 stream() 查看每个节点的执行:\n")

    # stream 生成每个节点的执行结果
    for event in graph.stream(initial_state):
        # event 格式: {"节点名": 状态更新}
        for node_name, state_update in event.items():
            print(f"节点 '{node_name}' 输出状态更新: {state_update}")

    print("\n使用 invoke() 只返回最终状态:")
    final_state = graph.invoke(initial_state)
    print(f"最终状态: {final_state}")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    demo_linear()
    demo_branching()
    demo_stream()

    print("\n" + "="*60)
    print("LangGraph 核心概念速查")
    print("="*60)
    print("""
┌─────────────────────────────────────────────────────────────┐
│ 1. State（状态）                                             │
│    - 用 TypedDict 定义                                       │
│    - 是数据在图中流动的载体                                   │
├─────────────────────────────────────────────────────────────┤
│ 2. Node（节点）                                              │
│    - 是一个函数                                              │
│    - 签名: def func(state: State) -> dict                   │
│    - 返回要更新的字段字典                                     │
├─────────────────────────────────────────────────────────────┤
│ 3. Edge（边）                                                │
│    - 普通边: add_edge(A, B) - A → B                         │
│    - 条件边: add_conditional_edges(A, func, mapping)        │
│      func(state) 返回节点名，mapping 匹配到下一个节点        │
├─────────────────────────────────────────────────────────────┤
│ 4. StateGraph（图）                                          │
│    - StateGraph(StateType) - 创建构建器                     │
│    - add_node(name, func) - 添加节点                        │
│    - set_entry_point(node) - 设置入口                       │
│    - compile() - 编译为可执行图                             │
├─────────────────────────────────────────────────────────────┤
│ 5. 执行方式                                                  │
│    - invoke(state) - 同步执行，返回最终状态                 │
│    - stream(state) - 流式执行，生成每个节点的输出           │
├─────────────────────────────────────────────────────────────┤
│ 6. END                                                       │
│    - 特殊常量，表示图的终止点                                │
│    - add_edge(node, END) - 节点执行后结束                   │
└─────────────────────────────────────────────────────────────┘
""")
