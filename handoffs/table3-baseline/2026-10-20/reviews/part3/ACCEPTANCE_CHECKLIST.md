# Part3 验收清单

依据：[原 Part3 任务说明](../../PART3_SCORING_VALIDATION_HANDOVER_ZH.md)第 1、7、8 节。

| 原任务 | 状态 | 本次证据 |
|---|---|---|
| 核实 ZIP、MANIFEST、固定来源/输入/代码 | PASS | ZIP/MANIFEST 哈希、87 固定文件；[重放 JSON](evidence/replay/verification_result.json)；[9 个 upstream 文件比对](evidence/UPSTREAM_SOURCE_CHECK.json) |
| 独立确认 CUR/CR 和 BFCL 参数检查 | PASS | 对照正式论文定义；3,034 非空输出与固定官方 dup checker 一致；[20 个额外边界](evidence/metric_boundary_results.json) |
| 检查 original-first 与 edited-first 的 roles、expected、prompt | PASS | 全量构造/映射/3,096 prompt 检查；[同 case 双顺序阅读](evidence/SOURCE_AND_PROMPT_REVIEW.md) |
| 名称、namespace、phantom/alias | PASS | canonical 258/258 名称一致；对 27 个未知名称调用单独记录，没有模糊修复 |
| 查同工具一对一错、both-correct、无调用、未知工具、类型错误 | PASS | [评分边界真值](evidence/metric_boundary_results.json)、[案例阅读](evidence/CASE_REVIEW.md)；both-correct/混合 unknown 等未在真实数据出现的情况明确标 synthetic |
| 唯一解析失败原文、引号、零分和分母 | PASS | `live_simple_108-65-0__cue4__original_first` 保留；[本次重放 JSON](evidence/replay/verification_result.json) |
| 检查 3,096 唯一 ID、6×516、12×258 | PASS | [补充核查结果](evidence/audit_result.json) |
| 本机独立重放并保留输出、Python 版本 | PASS | [RUN_RECORD](evidence/RUN_RECORD.json)、[本次 verification](evidence/replay/verification_result.json) |
| 核对逐例 score、六行 summary、按顺序 summary、失败统计 | PASS | 全量比较；[已核实交付表](results/README.md) |
| 复查强顺序差异，记录评分变更 | PASS | 原分数未变；original-first cue1–3 无 edited 优势；cue6 edited-first ratio undefined |
| 写评分说明、未决事项、Part4 交接 | COMPLETE | [报告](REVIEW_REPORT.md)、[遗留项](LEFTOVERS.md)、[Part4 接手文件](HANDOFF_TO_PART4.md) |
| 真人签收 | PASS | Kyrie 在当前聊天明确确认；原文与版本见 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md) |
| 上传 GitHub | USER WILL PUSH | [精确提交步骤](PUSH_INSTRUCTIONS.md)；助手没有 commit/push |

技术、交付和真人签收均已完成，没有技术 blocker。用户自行 commit/push。空数组及 optional-answer 行为按固定 BFCL 保留并在报告中解释，不影响原版结果可重放的结论。
