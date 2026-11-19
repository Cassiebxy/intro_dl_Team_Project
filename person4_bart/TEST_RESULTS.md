# 本地接口检查记录

日期：2026-11-18。执行：

```bash
person4_bart/.venv/bin/python -m unittest discover -s person4_bart/tests -v
```

结果：12 项测试全部通过。最后一次执行是在显式固定生成参数与修正 EOS 边界之后。

检查覆盖：

1. 人工训练／验证工具组隔离与 clean identity 数量。
2. 推理文件拒绝 gold target 和额外元数据。
3. 重复输入 ID 被拒绝。
4. test 配对不能作为 train 加载。
5. 跨 split 的工具组／完全相同 canonical target 重叠被拒绝。
6. 缺失和错误记录保留在 exact-match 分母。
7. 输入 SHA-256 不一致不能计为有效成功。
8. 重复和额外输出 ID 被识别。
9. 空输出、截断不能以 ok 状态通过接口检查。
10. 否定条件缺失能被字面审核发现。
11. HTML 报告转义输入和模型输出，避免把描述当成页面代码。
12. 生成上限与超长输入显式保留错误 ID；自然 EOS 恰在上限时正常结束；推理使用固定长度、greedy 且不继承 no-repeat 限制。

真实 MPS 集成证据另见最终运行中的 `summary.json`、`reload_check.json` 与额外 `diagnostic_rewrites.jsonl`。单元检查不评价模型语义能力；真实试跑已发现并保留一条过删失败。
