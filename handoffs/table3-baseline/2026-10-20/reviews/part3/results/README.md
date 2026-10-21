# 已核实的原版评分结果

这些文件是原交接包内已核实结果的字节一致副本，方便 Part4 直接使用；没有新增或修改分数。来源 run：`baseline-table3-qwen7b-20261020-mps`。逐文件来源和 SHA256 见上层 DELIVERY_MANIFEST.json。

| 文件 | 行数 | 单位/说明 |
|---|---:|---|
| [per_request_scores.csv](per_request_scores.csv) | 3096 | 每请求一行，布尔分数为 0/1 |
| [summary_by_cue.csv](summary_by_cue.csv) | 6 | 每 cue N=516；CUR/CR 为 0–1，ratio 无单位 |
| [summary_by_order.csv](summary_by_order.csv) | 12 | 每 cue/order N=258；CUR/CR 为 0–1，空 ratio 为 undefined |
| [response_failure_counts.csv](response_failure_counts.csv) | 5 | 请求级互斥分类，合计 3096；pct 为 0–100% |
| [call_diagnostic_counts.csv](call_diagnostic_counts.csv) | 11 | 调用级分类，合计 3038 calls，不是请求数 |

评分解释、空数组和 optional-answer 限制见 [REVIEW_REPORT](../REVIEW_REPORT.md)。两个 CUR 可重叠；CR 不是 strict-all。真人签收状态以 [STATUS](../STATUS.json)为准。
