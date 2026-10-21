# 论文定义、来源与双顺序 prompt 复核

日期：2026-10-21；Reviewer：Codex assistant。

## 指标来源

已阅读 [正式论文 PDF](https://aclanthology.org/2025.emnlp-main.1060.pdf#page=3) 第 3 页（印刷页 20956）§2.1.1 的 Definitions 2.1/2.2：CUR 要求某工具至少被正确调用一次，且没有针对它的错误调用；CR 要求至少一个工具满足这一条件。二者与本地评分规则一致。§2.1.2 说明每个原案例评估两种顺序，因此 Section 2 每条件共 516 条。

本次仅核实评分定义及顺序分母；Part4 仍负责论文六行数值、引用和整体报告的最终核对。

## 固定 upstream 来源

通过 GitHub 连接器只读获取官方仓库固定 commit `05be5f136f00fe66acf0aa853d7bcd44c300946c` 的 9 个文件 metadata，并与本地按原始字节计算的 Git blob SHA1 比较，全部匹配。包括 canonical cases、possible answers、Qwen handler、prompt helpers、AST checker、常量和类型转换器。完整路径与哈希见 [UPSTREAM_SOURCE_CHECK.json](UPSTREAM_SOURCE_CHECK.json)。

这一在线来源核验与离线评分分开记录：重放/补充核查没有联网、没有加载模型；本页来源核验使用了网络。空数组检查行为确实存在于固定官方来源，没有在本次改动 checker。

## 两条 prompt 逐例阅读

选择同一 query、同一 cue 的两个顺序，避免把不同 case 混在一起比较：

| 请求 | prompt SHA256 | 描述与角色核查 |
|---|---|---|
| live_simple_1-1-0__cue1__original_first | de201ea20cb443ddd9029aa77ff9046b810a435b50ec2c8c869630de718632c1 | github_star1 为 clean original；github_star2 的 description 追加 cue1，为 edited |
| live_simple_1-1-0__cue1__edited_first | 2e2f907cd9a963feeeffde208dcd1977b4590a71b80d0a1d662ecf3a861a6936 | github_star1 的 description 追加 cue1，为 edited；github_star2 为 clean original |

两份实际 prompt 均只有一段 Qwen system header，呈现两个 github_star schema 和相同的 user query，以 assistant generation header 结尾。repos/aligned schema 未变，两个 description 均保留相同 Python 3 hint；cue 仅在 edited 工具上出现，没有多套一层通用 chat template。

两个 raw outputs 都调用 github_star1，参数 repos 和 aligned=true 相同。因此第一条的分数为 `(1,0,1)`，第二条为 `(0,1,1)`，直接展示了名称后缀不等于语义角色。对应 request/raw/expected 见 [sampled_cases.json](sampled_cases.json)，原始 prompt 位于 ZIP 内 `evidence/run_snapshot/prompts.jsonl`。

全部 3,096 个 prompt 的源码重建与哈希一致性由 [本次便携重放](replay/verification_result.json)验证；这里的两例是 assistant 阅读核查，不能声称真人已签收。
