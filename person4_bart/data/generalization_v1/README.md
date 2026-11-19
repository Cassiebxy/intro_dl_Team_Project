# BFCL 留出工具与新 cue 数据包

沿用 Person 2 的工具分组和测试集，共 42 个 BFCL 问题、19 条源工具描述、13 个工具组。每条源描述生成六种输入，共 114 条。所有 cue 都追加在描述末尾。

| 切片 | 描述变体数 | 含义 |
| --- | ---: | --- |
| Clean | 19 | 原始工具描述 |
| Seen cue | 19 | 训练使用过的 Table 3 cue 1，应用在留出的工具上 |
| Unseen wording | 38 | 同类优先推荐的两种新措辞 |
| Unseen family | 38 | 维护频率和用户数量背书，各一个模板 |

`normalizer_inputs_test.jsonl` 是推理输入，只有 `description_id` 和 `input_description`。`pairs_test.jsonl` 保存评分所需的原始描述及切片信息。`cases_test.jsonl` 映射下游案例和工具组。`cues.jsonl` 记录完整措辞、来源、与 train/dev 文本的最近匹配及语义复核。团队其他成员可在同一批 ID 上独立复核。

工具组、源工具、案例和完整目标文本与 train/dev 均无交集。已有的 Person 2 test wording probe 同样出现在 dev，本数据包使用另外两条优先推荐措辞。这里的 unseen 按本次微调和开发数据定义。所有未见 cue 均用于留出的工具，因此观察结果反映两种留出因素的组合。每个新家族只有一个模板。

`live_simple_115-71-0` 的问题文本与训练案例 `live_simple_116-72-0` 相同，工具描述及参数 schema 不同。两者沿用 Person 2 分组。下游配对分析提供排除该测试问题的敏感性结果。

数据协议与哈希见 [protocol](../../protocols/shared_bfcl_v1.json) 和 [manifest](manifest.json)。另见 [泛化设计草案](../../protocols/GENERALIZATION_DRAFT_ZH.md) 和 [BART 实验结果](../../RESULTS_BFCL_ZH.md)。
