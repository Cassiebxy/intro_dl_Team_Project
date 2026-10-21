# Part3 遗留项与 Part4 接手入口

2026-10-21：assistant 技术复核 PASS，原分数不变；真人 Kyrie 已明确签收 PASS。证据见 [REVIEW_REPORT](REVIEW_REPORT.md)、[签收记录](HUMAN_SIGNOFF.md)、[本次重放](evidence/replay/verification_result.json)及[补充核查](evidence/audit_result.json)。

## 已完成

- [x] 核对 ZIP、MANIFEST 及 87 个固定文件哈希。
- [x] 本机独立重放 3,096 条分数和六行汇总，保存实际输出与环境。
- [x] 检查 12×258/6×516、source/expected、双顺序角色、点号名称及 source phantom/alias。
- [x] 补查 20 个评分边界、6 个解析边界、14 条 raw/expected 样例；核对全部四条多调用输出。
- [x] 核对逐例 CSV、六行主表、十二组 order、请求级和调用级统计。
- [x] 更新 REVIEW_REPORT、STATUS，保留原版分数与所有原始证据。
- [x] 记录 Kyrie 在当前聊天中的明确真人签收，保留助手作为技术执行者。

## Blocking

没有发现影响原版评分重放或本地表格完整性的技术 blocker。Kyrie 的真人阅读核对与接受决定已记录，Part3 本地任务已完成。

## Nonblocking / 报告必须保留的限制

1. **签收范围**：Kyrie 接受助手协助完成的技术复核，确认已阅读报告与案例记录；技术执行者仍为 assistant。原 JSON 中的 PENDING 是执行时快照，当前状态以 STATUS/HUMAN_SIGNOFF 为准。
2. **空数组检查器行为**：case `live_simple_112-68-0` 的 12 次请求被固定 BFCL 标为 type_error；根因涉及 `[]` 的源答案表示与嵌套检查，不能简单写成模型输出了非数组类型。主分数未改，不阻塞原规则复现；若调整规则，须单列新版本和差异。
3. **optional 答案标记**：case `live_simple_102-61-0` 的 11 次 missing_optional 来自 source expected 不允许省略 city；schema optional 并不保证 benchmark 判正确。
4. **强顺序差异**：original-first 的 cue1–3 没有 edited 优势；cue6 edited-first 的 ratio 为 undefined。保留位置/名称后缀耦合与案例重复的限制，不声称纯位置因果效应或统计显著。
5. **Part4 自行核对论文**：本次没有重新核对正式 PDF 的六行参考值，也没有解释本地 CR 与论文的差异原因。全组报告仍由 Part4 整合。

## Part4 先做什么

先查看本文件第 1–3 项，再读取 [REVIEW_REPORT](REVIEW_REPORT.md)、[HUMAN_SIGNOFF](HUMAN_SIGNOFF.md)和实际 JSON 证据。可使用原 run `baseline-table3-qwen7b-20261020-mps` 的原版分数；标注 assistant technical review PASS / Kyrie human signoff PASS。不要把评分重放当成新推理实验。

所有本次修改目前仅在本地，尚未 commit/push。解压证据目录和用户已有 `.DS_Store` 属于现有未跟踪文件，本次没有整理或提交它们。
