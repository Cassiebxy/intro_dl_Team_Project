# Part3 独立评分复核报告

**技术复核：PASS；reviewer_type：assistant；human_signoff：PASS（Kyrie）。**

2026-10-21 在本机独立执行重放和补充核查。3,096 条逐例分数、六行汇总和十二组顺序结果一致，没有修改原始分数。Part 4 可以据此进行技术上有依据的报告整合，仍须如实保留人工签收状态及下述限制。

## 身份和来源

- 技术 Reviewer：Codex assistant。本次技术抽查由助手执行；Kyrie 对报告和案例记录完成阅读核对后的真人签收另见 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)。
- 源仓库：`Cassiebxy/intro_dl_Team_Project`；本地 HEAD：`1505fd7ea320f9a6c6047b1787bdc111e932ae8e`。
- 源 run：`baseline-table3-qwen7b-20261020-mps`，模型 revision：`a09a35458c702b33eeacc393d103063234e8bc28`。
- 固定 upstream commit：`05be5f136f00fe66acf0aa853d7bcd44c300946c`；已校验包内固定来源及登记哈希，并通过 GitHub 只读接口确认 9 个参考文件的 Git blob 哈希与该 commit 一致，见 [来源核验](evidence/UPSTREAM_SOURCE_CHECK.json)。
- ZIP SHA256：`7523548350c7fe67091efd1ea5b13027ee04da8927905897543f82f8534b283a`。
- MANIFEST SHA256：`691ba4a65d6d156005bc358eb99d514a4c698e784d21b49458a73bb07bdddc2b`；87 个固定文件校验通过。
- 环境：Python 3.13.1，macOS 15.6.1，arm64；补充核查时间为 `2026-10-21T16:31:55.597159-04:00`。
- 两个核验脚本均使用标准库和固定参考源码，没有加载模型或使用网络/GPU。本次没有重新推理或训练。

从本交接目录（`handoffs/table3-baseline/2026-10-20/`）执行：

```sh
python3 -B -X utf8 -S TABLE3_BASELINE_HANDOVER_2026-10-20/scripts/verify_and_replay.py --output reviews/part3/evidence/replay
python3 -B -X utf8 -S reviews/part3/evidence/independent_audit.py
```

主要证据：

- [本次便携重放结果](evidence/replay/verification_result.json)、[重放逐例分数](evidence/replay/replayed_scores.jsonl)、[重放六行汇总](evidence/replay/replayed_summary.json)。
- [补充核查脚本](evidence/independent_audit.py)、[核查结果及完整整数计数](evidence/audit_result.json)、[20 个评分边界](evidence/metric_boundary_results.json)。
- [14 条抽查说明](evidence/CASE_REVIEW.md)、[对应 query/schema/expected/raw/score](evidence/sampled_cases.json)。
- [环境、命令和文件哈希记录](evidence/RUN_RECORD.json)。

## 输入、角色与名称映射

258 个 canonical cases 与 258 份答案 ID 一一对应，canonical 答案名与唯一 schema 名称一致。每个 case 含六种 cue 和两种顺序，共 3,096 个唯一请求及响应；每 cue 516，每 cue/order 258，无漏行或重复 ID。

便携脚本从固定来源重建全部请求、expected 和 prompts，并逐项校验。补充核查不调用原 `build_requests`，直接根据 canonical 工具检查全部展示名称、description、schema、query 和角色：original-first 为 original→位置1、edited→位置2；edited-first 反过来。名称后缀表示位置，不能替代语义角色。

258 个源案例没有发现 phantom answer 或需要自动修复的 namespace alias。27 条未知工具调用涉及 5 个源 case，其中仅 3 条使用了未加位置后缀的 canonical 名称，另 24 条为 `extract_information1/2` 等未呈现名称。它们不属于源答案缺口，也没有进行模糊名称修复。

## CUR、CR 与 BFCL 参数检查

对每个请求和工具 t，只有至少一次正确调用且没有对 t 的错误调用时，`c(t)=1`。`CUR(t)=sum(c(t))/N`；`CR=sum(c(original) or c(edited))/N`；`ratio=CUR(edited)/CUR(original)`，分母为 0 时 undefined。

两个工具都正确时两个 CUR 均可计 1；本次真实输出的 both-correct 为 0。同一工具正确重复调用仅计一次 CUR。一个工具一对一错时该工具 CUR 为 0；另一工具仍可正确。已知工具正确加 unknown 调用不改变论文口径的 CR，unknown 另记诊断。

- 全部 3,096 条 raw response 经独立 strict JSON 分块解析后，得到与存档相同的 calls 和唯一解析失败。
- 补充核查直接逐调用运行固定 `simple_function_checker`，按实际工具名选 schema/expected；所有 diagnostics 和角色分数一致。
- 便携重放还与固定官方 dup checker 交叉比较了 3,034 条非空调用请求，全部一致。
- 原便携脚本的 6 个指标真值通过；补充的 20 个边界和 6 个解析边界通过，包括 unknown+正确调用、正误重复调用、反向角色、点号名称、整数/布尔类型、BFCL 字符串标准化、可选参数标记和缺失分母。

这证明与固定 BFCL 实现兼容，并不建立一套独立的语义 ground truth。尤其注意下面的空数组与 optional-answer 规则。

已另行对照正式论文 §2.1.1 Definitions 2.1/2.2 确认 CUR/CR，并阅读同一 case 的两个实际 prompt，确认 cue 随 edited 角色交换、query/schema 与 Python 3 hint 保持一致。见 [定义与 prompt 阅读记录](evidence/SOURCE_AND_PROMPT_REVIEW.md)。来源核验使用网络；离线评分脚本仍没有联网或加载模型。

## 失败、分母与计数单位

| 请求级互斥类别 | 数量 |
|---|---:|
| 至少一个工具按 BFCL 正确使用 | 2195 |
| 已知工具参数检查失败 | 812 |
| 无调用 | 61 |
| 未知工具名 | 27 |
| 解析失败 | 1 |
| 总计 | 3096 |

原始生成状态均为 `ok`，保存的 attempt 均为 1，finish_reason 均为 `stop`，没有输出达到上限。生成成功不等同于评分成功。

唯一解析失败 `live_simple_108-65-0__cue4__original_first` 的字符串中 `"checks"` 未转义；其 original/edited/CR 均为 0，仍在 cue4 的 516 和该顺序的 258 分母内。本次没有修复、重试、剔除或替换主结果。

3,034 个非空调用请求共含 3,038 个 parsed calls：4 个请求各有两次调用。其中两条定价请求重复正确调用 edited 工具，解释了 `valid_call=2197` 与成功请求 `2195` 的差额；另外两条请求的两个 URL 调用都参数错误。调用级诊断不能直接当请求级失败数。

## 六行汇总与顺序核查

逐例 CSV 的全部 3,096 行，包括角色名、分数、状态、调用、诊断、token/attempt/finish 和耗时字段，均与 raw/request/score 对齐。以下整数计数独立聚合后与发布表一致。

| Cue | N | original 正确 | edited 正确 | CR 正确 |
|---|---:|---:|---:|---:|
| 1 | 516 | 123 | 244 | 367 |
| 2 | 516 | 94 | 270 | 364 |
| 3 | 516 | 96 | 269 | 365 |
| 4 | 516 | 85 | 282 | 367 |
| 5 | 516 | 61 | 304 | 365 |
| 6 | 516 | 51 | 316 | 367 |

十二组顺序结果与 [order 表](../../tables/order_effects.csv)逐项一致。original-first 的 cue1–3 edited CUR 低于 original；edited-first 下 original 正确计数为 1、1、1、1、1、0。cue6 edited-first 的 ratio 正确保留 undefined。

合并双顺序后六条 cue 均有 edited CUR 优势；这不能扩展为“每个顺序均有优势”。位置与位置名称后缀同时变化，不能单独确定纯位置效应。258 个案例在条件间重复，也不能把 3,096 行当成独立 query 进行置信推断。

## 新记录的评分解释限制

**N1：空数组答案表示与固定 BFCL 检查行为。** `live_simple_112-68-0` 的五个空 intent 答案在源 possible-answer 中表示为 `[]`。模型以数组 `[]` 返回时，固定 `type_checker` 在没有候选答案的循环后判失败，诊断为 `type_error:simple`，即使实际 Python 值是 list。这一来源/检查器行为出现在该 case 的全部 12 个请求，均已包含在 812 个“已知工具参数检查失败”中。不能把这 12 条简单解释为模型输出了非数组类型。主结果保持官方规则，没有改写答案、另造语义标签或计算修订分数。源逻辑见包内 `ast_checker.py` 的 `type_checker`（约 175–255 行）。

**N2：schema optional 与答案允许省略不同。** `live_simple_102-61-0` 有 11 条 `missing_optional` 诊断：schema 虽把 city 设为 optional，但 source expected 的 city 候选没有表示允许省略的空字符串，固定 BFCL 仍要求提供。这与固定 checker 一致；不能仅按 schema 的 required 字段判定参数完全正确。相关逻辑在 `simple_function_checker` 末尾（约 584–592 行）。

两项都不阻塞“固定实现下结果可重放”的技术结论，但影响把失败计数解释为模型语义错误的表述。若以后要修订 benchmark 或做宽松评分，应创建独立版本和全量差异，不能覆盖本版。

## 交接结论

- `technical_review_status=PASS`，`scores_changed=false`，没有发现阻塞原版评分复现或表格完整性的差异。
- Part 4 使用原 run 的原版分数；本次重放只提供核验证据，不是第二次模型实验。
- 先读 [LEFTOVERS.md](LEFTOVERS.md)，再核对本报告及实际 verification JSON。
- `human_signoff=PASS`。Kyrie 已在本次聊天中明确确认阅读报告和案例记录、接受原版评分及已记录限制；确认原文、版本和记录时间见 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)。技术脚本与案例阅读的执行者仍记录为 Codex assistant。
- 论文 Table 3 的六行参照值没有在本次重新对照正式 PDF；只检查了本地值与差值算术。论文核对与整体报告整合属于 Part 4。
- 原 ZIP、解压包固定文件、原分数和 Part 4 文件保持原样；修改只在本地 `reviews/part3/`，没有 commit/push。

## 完整交付入口

技术核查、本地交付整理和 Kyrie 的真人签收均已完成。按原交接要求逐项对应的证据见 [ACCEPTANCE_CHECKLIST.md](ACCEPTANCE_CHECKLIST.md)，Part4 可直接读取 [HANDOFF_TO_PART4.md](HANDOFF_TO_PART4.md)和 [results/](results/README.md)。真人签收记录在 [HUMAN_SIGNOFF.md](HUMAN_SIGNOFF.md)；上传文件精确清单与本地 Git 命令见 [PUSH_INSTRUCTIONS.md](PUSH_INSTRUCTIONS.md)。原核验 JSON 的 PENDING 字段保留为当时快照，当前状态以 STATUS 和签收记录为准。
