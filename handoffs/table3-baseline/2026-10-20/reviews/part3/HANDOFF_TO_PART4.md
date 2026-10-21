# 给 Part4 的评分交接

状态：assistant technical review PASS；交付文件完整；human signoff PASS（Kyrie）。使用原 run `baseline-table3-qwen7b-20261020-mps` 的原版分数，本次没有改分。

请依次看 [LEFTOVERS.md](LEFTOVERS.md)、[REVIEW_REPORT.md](REVIEW_REPORT.md)、[Kyrie 明确签收记录](HUMAN_SIGNOFF.md)、[实际 verification JSON](evidence/replay/verification_result.json)和[完整交付清单](DELIVERY_MANIFEST.json)。原技术 JSON 保留签收前快照，当前签收状态以 STATUS/HUMAN_SIGNOFF 为准。

## 可以直接接入的结果

| 文件 | 单位和范围 |
|---|---|
| [per_request_scores.csv](results/per_request_scores.csv) | 3,096 行，每请求一行；含角色、分数、诊断与 raw 对齐字段 |
| [summary_by_cue.csv](results/summary_by_cue.csv) | 六行，每 cue N=516；含 CUR/CR 和本地 ratio |
| [summary_by_order.csv](results/summary_by_order.csv) | 十二行，每 cue/order N=258；CUR/CR 为 0–1，ratio 空值为 undefined |
| [response_failure_counts.csv](results/response_failure_counts.csv) | 请求级互斥分类，总和 3,096 |
| [call_diagnostic_counts.csv](results/call_diagnostic_counts.csv) | 调用级，共 3,038 calls，不能和请求统计直接相加 |
| [重放 score JSONL](evidence/replay/replayed_scores.jsonl) | 与原存档全部逐条一致 |

交付 CSV 是原版结果中已核实的文件副本；语义、来源和哈希见 [results/README.md](results/README.md)及 manifest。参数正确性沿用固定 BFCL，未另造语义 gold labels。

## 结果与解释边界

3,096 个请求均生成成功，无截断，唯一解析失败保留分母。请求级分类：2195 至少一个工具正确、812 已知工具参数检查失败、61 无调用、27 未知工具名、1 解析失败。

合并顺序时六种 cue 都有 edited CUR 优势；original-first 的 cue1–3 没有这一优势，edited-first 下 original 近零。名称后缀随位置变化，位置与名称标签耦合。案例跨条件重复，不能将 3,096 行当作独立 query 做置信推断。

两个需要写进评分/错误说明的细节：`live_simple_112-68-0` 的 12 次 type_error 涉及源答案空数组与固定 checker 行为；`live_simple_102-61-0` 的 11 次 missing_optional 涉及 expected 对 city 不允许省略。不能把这两类诊断直接当成直观语义类型错误，主分数保持原样。

本次已核实论文的 CUR/CR 定义；论文六行参考值、差异原因、整体 midterm 写作和对真人签收状态的复查仍由 Part4 完成。重放不是额外模型实验，没有训练/normalizer 结果。
