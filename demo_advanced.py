"""
LangGraph 进阶演示：任务审批流程

展示更复杂的图结构：
- 循环执行
- 多级条件分支
- 状态累积
- 并行分支概念
- 中断和人工干预点
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

# ============================================================
# 1. 复杂状态定义
# ============================================================

class ApprovalState(TypedDict):
    """审批流程状态"""
    # 任务信息
    task_name: str
    amount: float           # 金额，影响审批级别
    department: str         # 部门

    # 审批流程状态
    current_level: int      # 当前审批层级 (1=主管, 2=经理, 3=总监)
    approvals: list[dict]   # 已完成的审批记录
    rejections: list[str]   # 拒绝原因

    # 流程控制
    status: str             # pending, approved, rejected
    retry_count: int        # 重试次数


# ============================================================
# 2. 节点定义：模拟审批操作
# ============================================================

def supervisor_review(state: ApprovalState) -> dict:
    """主管审批（第1级）"""
    print(f"\n  [主管审批] 审批任务: {state['task_name']}")
    print(f"  金额: ¥{state['amount']:,} 部门: {state['department']}")

    # 简化规则：金额 < 1000 直接通过
    if state['amount'] < 1000:
        decision = "approved"
        comment = "金额在授权范围内，批准"
        print(f"  ✓ 决定: {comment}")
    else:
        decision = "escalate"  # 需要升级
        comment = "金额超限，需上级审批"
        print(f"  → 决定: {comment}")

    return {
        "approvals": [{
            "level": 1,
            "role": "主管",
            "decision": decision,
            "comment": comment
        }],
        "current_level": 2 if decision == "escalate" else 1,
        "status": decision if decision != "escalate" else "pending"
    }


def manager_review(state: ApprovalState) -> dict:
    """经理审批（第2级）"""
    print(f"\n  [经理审批] 审批任务: {state['task_name']}")

    # 规则：金额 < 10000 通过
    if state['amount'] < 10000:
        decision = "approved"
        comment = "金额在授权范围内，批准"
        print(f"  ✓ 决定: {comment}")
    else:
        decision = "escalate"
        comment = "金额超限，需总监审批"
        print(f"  → 决定: {comment}")

    return {
        "approvals": [{
            "level": 2,
            "role": "经理",
            "decision": decision,
            "comment": comment
        }],
        "current_level": 3 if decision == "escalate" else 2,
        "status": decision if decision != "escalate" else "pending"
    }


def director_review(state: ApprovalState) -> dict:
    """总监审批（第3级）"""
    print(f"\n  [总监审批] 审批任务: {state['task_name']}")

    # 规则：所有金额都需审核，但可能拒绝
    if state['amount'] > 50000:
        decision = "rejected"
        comment = "金额过大，需要董事会特别审批"
        print(f"  ✗ 决定: {comment}")
    else:
        decision = "approved"
        comment = "最终批准"
        print(f"  ✓✓ 决定: {comment}")

    return {
        "approvals": [{
            "level": 3,
            "role": "总监",
            "decision": decision,
            "comment": comment
        }],
        "status": decision
    }


def notify_rejection(state: ApprovalState) -> dict:
    """拒绝通知节点"""
    last_approval = state['approvals'][-1]
    reason = last_approval['comment']
    print(f"\n  [发送通知] 任务被拒绝")
    print(f"  原因: {reason}")

    return {
        "rejections": [reason],
        "status": "rejected"
    }


def notify_approval(state: ApprovalState) -> dict:
    """批准通知节点"""
    print(f"\n  [发送通知] 任务已批准！")
    print(f"  共经过 {len(state['approvals'])} 级审批")

    # 打印审批链
    print("\n  审批链:")
    for approval in state['approvals']:
        print(f"    • {approval['role']}: {approval['comment']}")

    return {"status": "approved"}


def check_retry(state: ApprovalState) -> dict:
    """检查是否可以重试"""
    retry = state['retry_count'] + 1
    print(f"\n  [检查重试] 第 {retry} 次尝试")

    if retry <= 2:
        print(f"  → 允许重试，调整金额后重新提交")
        # 模拟调整金额
        new_amount = state['amount'] * 0.8
        print(f"  → 调整金额: ¥{state['amount']:,.0f} → ¥{new_amount:,.0f}")
        return {
            "retry_count": retry,
            "amount": new_amount,
            "current_level": 1,
            "status": "pending"
        }
    else:
        print(f"  ✗ 超过最大重试次数")
        return {"retry_count": retry}


# ============================================================
# 3. 条件路由函数
# ============================================================

def after_supervisor(state: ApprovalState) -> str:
    """主管审批后的路由"""
    last_decision = state['approvals'][-1]['decision']

    if last_decision == 'approved':
        return 'notify_approval'
    elif last_decision == 'escalate':
        return 'manager_review'
    return 'notify_rejection'


def after_manager(state: ApprovalState) -> str:
    """经理审批后的路由"""
    last_decision = state['approvals'][-1]['decision']

    if last_decision == 'approved':
        return 'notify_approval'
    elif last_decision == 'escalate':
        return 'director_review'
    return 'notify_rejection'


def after_director(state: ApprovalState) -> str:
    """总监审批后的路由"""
    last_decision = state['approvals'][-1]['decision']

    if last_decision == 'approved':
        return 'notify_approval'
    return 'notify_rejection'


def after_rejection(state: ApprovalState) -> str:
    """拒绝后的路由：决定是否重试"""
    if state['retry_count'] < 2:
        return 'check_retry'
    return END


def after_retry_check(state: ApprovalState) -> str:
    """重试检查后的路由"""
    if state['retry_count'] <= 2:
        return 'supervisor_review'  # 重新开始流程
    return END


# ============================================================
# 4. 构建审批流程图
# ============================================================

def build_approval_graph() -> StateGraph:
    """构建审批流程图"""

    builder = StateGraph(ApprovalState)

    # 添加所有节点
    builder.add_node("supervisor_review", supervisor_review)
    builder.add_node("manager_review", manager_review)
    builder.add_node("director_review", director_review)
    builder.add_node("notify_approval", notify_approval)
    builder.add_node("notify_rejection", notify_rejection)
    builder.add_node("check_retry", check_retry)

    # 设置入口
    builder.set_entry_point("supervisor_review")

    # 主管审批后的条件分支
    builder.add_conditional_edges(
        "supervisor_review",
        after_supervisor,
        {
            "manager_review": "manager_review",
            "notify_approval": "notify_approval",
            "notify_rejection": "notify_rejection"
        }
    )

    # 经理审批后的条件分支
    builder.add_conditional_edges(
        "manager_review",
        after_manager,
        {
            "director_review": "director_review",
            "notify_approval": "notify_approval",
            "notify_rejection": "notify_rejection"
        }
    )

    # 总监审批后的条件分支
    builder.add_conditional_edges(
        "director_review",
        after_director,
        {
            "notify_approval": "notify_approval",
            "notify_rejection": "notify_rejection"
        }
    )

    # 批准后结束
    builder.add_edge("notify_approval", END)

    # 拒绝后的条件分支（是否重试）
    builder.add_conditional_edges(
        "notify_rejection",
        after_rejection,
        {
            "check_retry": "check_retry",
            END: END
        }
    )

    # 重试检查后可能重新开始
    builder.add_conditional_edges(
        "check_retry",
        after_retry_check,
        {
            "supervisor_review": "supervisor_review",
            END: END
        }
    )

    return builder.compile()


# ============================================================
# 5. 演示函数
# ============================================================

def demo_approval_process():
    """演示：审批流程"""

    test_cases = [
        {"task_name": "购买办公用品", "amount": 500, "department": "行政部"},
        {"task_name": "团队团建费用", "amount": 5000, "department": "市场部"},
        {"task_name": "服务器采购", "amount": 30000, "department": "技术部"},
        {"task_name": "年度营销活动", "amount": 80000, "department": "市场部"},
    ]

    graph = build_approval_graph()

    for i, case in enumerate(test_cases, 1):
        print("\n" + "="*70)
        print(f"测试案例 {i}: {case['task_name']}")
        print("="*70)

        initial_state = {
            "task_name": case['task_name'],
            "amount": case['amount'],
            "department": case['department'],
            "current_level": 1,
            "approvals": [],
            "rejections": [],
            "status": "pending",
            "retry_count": 0
        }

        final_state = graph.invoke(initial_state)

        print("\n" + "-"*70)
        print(f"最终结果: {final_state['status'].upper()}")
        if final_state['status'] == 'approved':
            print(f"审批级别: {'主管' if final_state['current_level'] == 1 else '经理' if final_state['current_level'] == 2 else '总监'}")
        print("-"*70)


# ============================================================
# 6. 额外演示：展示状态可视化概念
# ============================================================

def show_graph_structure():
    """打印图结构说明"""
    print("\n" + "="*70)
    print("审批流程图结构")
    print("="*70)
    print("""
                    ┌─────────────────┐
                    │ 主管审批        │
                    └────────┬────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
           金额<1K       金额≥1K      拒绝
                │            │            │
                ↓            ↓            ↓
         ┌──────────┐  ┌──────────┐  ┌──────────┐
         │批准通知  │  │经理审批  │  │拒绝通知  │
         └──────────┘  └────┬─────┘  └────┬─────┘
                            │             │
                 ┌──────────┼──────────┐  │
                 │          │          │  │
            金额<10K    金额≥10K     拒绝  │
                 │          │          │  │
                 ↓          ↓          │  │
          ┌──────────┐ ┌──────────┐   │  │
          │批准通知  │ │总监审批  │   │  │
          └──────────┘ └────┬─────┘   │  │
                              │        │  │
                     ┌────────┼────────┤  │
                     │        │        │  │
                   通过      拒绝      │  │
                     │        │        │  │
                     ↓        ↓        ↓  ↓
                 ┌─────────────────────────┐
                 │   [重试检查] ──→ [主管] │
                 └─────────────────────────┘

关键特性：
1. 多级审批：根据金额自动升级
2. 条件分支：每个审批点有多个出口
3. 状态累积：approvals 列表记录所有审批
4. 循环重试：拒绝后可重新提交
""")


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    show_graph_structure()
    demo_approval_process()

    print("\n" + "="*70)
    print("LangGraph 进阶概念总结")
    print("="*70)
    print("""
【多级条件分支】
  - 每个节点可以有多个条件出口
  - add_conditional_edges(node, func, mapping)
  - mapping 定义返回值到节点的映射

【状态累积】
  - 使用 list 类型字段记录历史
  - 每个节点追加信息，不覆盖
  - 可用于审计、调试

【循环控制】
  - 通过条件边实现循环
  - 需要设置循环终止条件
  - 避免无限循环（使用计数器）

【实际应用模式】
  1. 审批流程：多级条件分支
  2. 工作流：节点串联 + 状态累积
  3. 重试机制：循环 + 计数器
  4. 分类路由：根据输入分发到不同处理

【设计建议】
  - 先画流程图，再编码
  - 每个节点只做一件事
  - 状态结构尽量扁平
  - 条件逻辑集中在路由函数
""")
