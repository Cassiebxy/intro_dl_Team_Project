# Part3 完整本地交付

2026-10-21：**Part3 评分与验证、本地交付及真人签收均已完成，结果 PASS，原分数不变。** 技术执行者为 Codex assistant；Kyrie 已明确阅读核对并签收 PASS。未 commit/push。

先读 [REVIEW_REPORT.md](REVIEW_REPORT.md)，再看 [LEFTOVERS.md](LEFTOVERS.md)。本次不需要 GPU，没有重新推理或训练。

## 交付内容

| 内容 | 位置 |
|---|---|
| 逐项验收与完成范围 | [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md) |
| 评分方法、全部核验结论、限制 | [REVIEW_REPORT.md](REVIEW_REPORT.md) |
| 机器可读状态 | [STATUS.json](STATUS.json) |
| Part4 接手说明 | [HANDOFF_TO_PART4.md](HANDOFF_TO_PART4.md) |
| 3,096 行逐例 CSV、六行汇总、十二组顺序、两类失败统计 | [results/README.md](results/README.md) |
| 本次逐例重放、汇总与 verification JSON | [evidence/replay/](evidence/replay/verification_result.json) |
| 补充核查：20 评分边界、6 解析边界、全量表格核对 | [evidence/audit_result.json](evidence/audit_result.json) |
| 14 条案例阅读说明与原文 | [evidence/CASE_REVIEW.md](evidence/CASE_REVIEW.md)、[sampled_cases.json](evidence/sampled_cases.json) |
| 论文定义、两个 prompt 与官方源码哈希核查 | [SOURCE_AND_PROMPT_REVIEW.md](evidence/SOURCE_AND_PROMPT_REVIEW.md) |
| 环境和原重放记录 | [evidence/RUN_RECORD.json](evidence/RUN_RECORD.json) |
| 本地交付文件校验清单 | [DELIVERY_MANIFEST.json](DELIVERY_MANIFEST.json) |
| 负责人签收与 Git 上传步骤 | [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)、[PUSH_INSTRUCTIONS.md](PUSH_INSTRUCTIONS.md) |

## 另一台电脑如何复核

Python >=3.10 即可。先完整解压本交接目录已有的 ZIP，保持 `TABLE3_BASELINE_HANDOVER_2026-10-20/` 与 `reviews/` 同级，然后从 `handoffs/table3-baseline/2026-10-20/` 执行：

```sh
python3 -B -X utf8 -S TABLE3_BASELINE_HANDOVER_2026-10-20/scripts/verify_and_replay.py --output reviews/part3/evidence/replay
python3 -B -X utf8 -S reviews/part3/evidence/independent_audit.py
python3 -B -X utf8 -S reviews/part3/evidence/prepare_delivery.py
```

最后一条会检查已保存的重放证据、导出已核实结果、刷新本地交付 manifest/提交清单。重放会更新本机 Python/执行时间记录，因此重新运行后应重新整理交付；这不构成新增模型实验。不要在待重放前手改原 ZIP 或其固定文件。

## 用户自行上传

真人确认原文及签收版本见 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)。现在按 [PUSH_INSTRUCTIONS.md](PUSH_INSTRUCTIONS.md)提交本目录列出的成果，GitHub 上传由你执行。

`evidence/` 中原重放和技术核查 JSON 保留执行时的签收快照，部分字段仍为 PENDING；这些是历史核验记录。当前正式签收状态以 [STATUS.json](STATUS.json)和 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)为准，不将技术脚本执行归为真人亲自执行。
