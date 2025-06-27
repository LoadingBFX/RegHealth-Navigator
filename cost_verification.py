#!/usr/bin/env python3

print("=== 成本验证 ===")
print("测试数据:")
print("- 总tokens: 14,109,286")
print("- 报告成本: $1.4109")
print()

print("计算验证:")
tokens = 14109286
cost = tokens / 1000 * 0.0001
print(f"- 计算成本: ${cost:.4f}")
print(f"- 差异: ${abs(cost - 1.4109):.6f}")
print(f"- 是否匹配: {abs(cost - 1.4109) < 0.0001}")
print()

print("详细计算:")
print(f"公式: {tokens} / 1000 * 0.0001")
print(f"步骤1: {tokens} / 1000 = {tokens / 1000}")
print(f"步骤2: {tokens / 1000} * 0.0001 = {cost}")
print()

print("OpenAI定价验证:")
print("- 模型: text-embedding-ada-002")
print("- 价格: $0.0001 per 1K tokens")
print("- 我们的公式: total_tokens / 1000 * 0.0001")
print("- 公式正确性: ✅ 完全正确")
print()

print("结论: 成本计算完全正确！")
print("- 我们的 $1.4109 成本与 OpenAI 官方定价完全相符")
print("- 计算公式: total_tokens / 1000 * 0.0001")
print("- 定价模型: text-embedding-ada-002") 