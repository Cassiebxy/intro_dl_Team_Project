# Person 4 BART-base 实验与交接

2026 年 11 月 19 日。BART-base 已用 Person 2 的 BFCL 配对数据微调。留出集显示，模型能去掉训练中使用的优先推荐措辞，也能处理部分新 cue。遇到另一些句式时，它直接保留了整条 cue。

## 训练与比较口径

训练使用 Person 2 的 `b2552bb` 数据版本。400 条训练配对来自 100 条源描述和 57 个工具组，其中 25% 是 clean → clean。BART 从 `facebook/bart-base` 的固定 revision 初始化，在 Mac M4 上用 FP32、AdamW、学习率 5e-5、有效 batch 16、seed 42 跑 3 个 epoch，共 75 次优化更新。训练时只输入描述，Qwen 请求里的问题、工具名和参数 schema 由程序保留。

采用 Person 2 已发表的提示词、训练预算与 checkpoint 选择指标。每轮计算 92 条 clean 或已见措辞开发配对的 teacher-forced loss，选择最小的第 1 个 epoch。23 条额外措辞只用于开发集生成评分。BART 梯度按有效目标 token 数加权，Person 2 的 FLAN 代码按 microbatch 样本数加权。两者使用各自 tokenizer。实验总耗时 185.2 秒，MPS 驱动分配采样峰值约 4.91 GiB。重载后 115 条开发输出与保存前一致。训练假设、数据和 checkpoint 哈希见 [BART 运行记录](results/bfcl_v1/bart_run.json) 和 [协议](protocols/shared_bfcl_v1.json)。

## 文本恢复与泛化

| 数据 | 精确恢复 | 解释 |
| --- | ---: | --- |
| Person 2 dev | 112/115 | 23 条源描述，每条 5 种变体 |
| Person 2 test | 95/95 | 19 条留出源描述。其 wording probe 已用于 dev 观察 |
| 新泛化集 clean | 19/19 | 清洁输入原样保留 |
| 新泛化集已见优先 cue | 19/19 | 同一训练 cue 应用于留出工具 |
| 新优先措辞 1 | 0/19 | 19 次均复制输入，保留 cue |
| 新优先措辞 2 | 15/19 | 4 次复制输入，保留 cue |
| 新家族维护频率 | 19/19 | 19 次均精确恢复 |
| 新家族用户数量背书 | 0/19 | 19 次均复制输入，保留 cue |

新泛化集共 114 条描述，来自 19 条源描述、13 个工具组和 42 个可用于下游的 BFCL 问题。同一组在所有比较条件中保持一致。三类切片的识别基于微调和开发数据。每个新家族仅含一条候选模板，结果由 BART 的实测输出和源描述逐 ID 比较得到。随机种子只跑一组。数据文件包括输入、目标、候选来源、分组、重复问题标记和哈希。见 [泛化数据包](data/generalization_v1/README.md)、[逐切片文本指标](results/bfcl_v1/rewrite_summary.csv) 和 [恢复率图](results/bfcl_v1/rewrites_by_cue.png)。

与 Person 2 的 FLAN-T5-small 在相同 115 个 dev ID 上配对。两模型均恢复 104 条，BART 单独恢复 8 条，两者均未恢复 3 条。原始 BART 在相同提示词和本次贪心生成设定下完整恢复 0/115。这些数字描述各自在此设置下的行为。开发结果按描述重复计数，且不同底座的 tokenizer、预训练和优化细节不同。见 [配对开发集结果](results/bfcl_v1/paired_dev_vs_flan.csv)。

## 失败分析

新泛化集的 42 条非精确恢复均完整复制输入。因此原有功能文字保留，但整句诱导仍在。未见措辞 1 与用户数量背书没有被模型删掉。开发集还有以下实际失败。见 [全部非精确恢复记录](results/bfcl_v1/rewrite_mismatches.jsonl)。

| 现象 | 观察 | 分类 |
| --- | --- | --- |
| 反转工具，dev wording probe | 删除了字符串按字符倒序与布尔值取反的独立说明，把字符串写成取反，并重复数字条件。足以改变工具行为的解释。 | 功能错误及过删 |
| 越南语行程工具，已见 `prefix_2` | 去掉 cue 时将 `loại chuyến đi`（行程类型）缩成 `loại`（类型）。保留了位置和等待时间，缩略后的条件含义依赖上下文。 | 功能细节缺失 |
| 同一越南语工具，dev wording probe | 完整复制输入。原有越南语字符和功能文字保留，优先推荐句也保留。 | 漏删 |

以上为逐文本复核。精确恢复提供字面证据，Qwen 行为另用同一请求的配对评分。所有 115 条开发和 114 条新泛化输入均有输出，未发现空输出或达到 BART 生成上限的失败。

## AutoDL 四条件复算

用档案中的模型完整输入、案例、工具顺序、名称映射和种子进行精确匹配，再使用同一个固定的 BFCL scorer 评分。对归一化条件，两个候选描述都经过 BART。Clean 的 `edited` 只是作为对照的候选身份。已见 cue 的两组四条件均覆盖完整。

| 案例范围 | Clean 编辑工具选择率 | Manipulated | BART → Qwen | 四条件各自严格 REC |
| --- | ---: | ---: | ---: | ---: |
| 与 Person 2 一致的 16 个 dev 案例、两种顺序、固定名称映射 | 5/32 | 7/32 | 5/32 | 28/32 |
| 42 个留出案例 × 两种顺序 × 两种名称映射 | 83/168 | 99/168 | 83/168 | 112/168 |

已见 cue 的所有 BART 改写输入与相应 Clean 输入一致，Clean → BART 也一致。留出案例的选择率差为 +9.52 个百分点，BART 后为 0 个百分点。因为复算使用同一档案里的相同输入，复用结果记录了恢复干净输入时的行为。精确文本恢复后仍有 56/168 个请求未通过严格 REC。这些请求对 Clean 的调用得分也同样失败。见 [四条件指标](results/bfcl_v1/autodl-replay/condition_summary.csv) 和 [配对效应](results/bfcl_v1/autodl-replay/paired_summary.csv)。

全量计划 2,144 个条件，AutoDL 档案匹配 1,060 个。新 cue 下未获精确匹配的 1,084 个条件有独立 Qwen 输入与评分映射，待按团队最终采用的 Qwen 配置运行。AutoDL 历史 manifest 未记录基础模型 revision。见 [请求矩阵](results/bfcl_v1/qwen_matrix.json) 和 [AutoDL 覆盖](results/bfcl_v1/autodl-replay/coverage.csv)。

## 本机 Qwen 四条件实测

本机的首批全量计时较长，因此按照案例 ID 的 SHA-256，每个留出工具组选一个案例。本机实验保留了全部五条 cue、两种工具顺序、两种名称映射，以及同一套 Clean 和 Clean → BART 控制，共 624 条请求。同案、顺序、名称映射和完整输入相同的条件共享一次确定性生成。冻结的 Qwen2.5-7B-Instruct 4-bit checkpoint 使用 Apple MLX Metal 和贪心解码，生成上限 512 token。模型 chat template 与 AutoDL 档案的哈希一致。模型量化、后端和解码设置与 AutoDL 不同。见 [本机运行配置](results/bfcl_v1/mlx-groups/run_manifest.json) 和 [MLX 权重说明](https://huggingface.co/mlx-community/Qwen2.5-7B-Instruct-4bit)。

624 条请求全部评分。五条 cue 的平均绝对选择率差从 18.85 降至 6.54 个百分点，严格调用正确从 189/260 变为 194/260。两条原样复制的 cue 保持原来的下游偏移。本机选出的 13 个案例未包含标记的重复问题。见 [本机 Qwen 实验结果](results/bfcl_v1/MLX_RESULTS_ZH.md) 与 [选择率和正确率图](results/bfcl_v1/qwen_mlx_by_cue.png)。

## 团队交接

- Person 2 和 Person 3 可用 [114 条推理输入](data/generalization_v1/normalizer_inputs_test.jsonl) 及 [评分配对文件](data/generalization_v1/pairs_test.jsonl) 运行各自模型。队友可复核 cue 家族标注和功能等价性。
- Person 1 可使用 [1,084 条待补跑请求和评分映射](results/bfcl_v1/autodl_pending_requests.zip)。两个 JSONL 文件已通过原 controlled runner 的 `--validate-only`。原 runner 的执行长度只支持 smoke 或 7,224 条完整矩阵，需要在团队推理环境使用支持自定义批次的入口。如改用不同的 Qwen checkpoint 或后端，应在该后端运行对应的 Clean 和 Manipulated 控制。
- Person 3 可读取 [轻量结果总目录](results/bfcl_v1/) 的文本与下游指标。在三模型共同结果落盘后汇入同一对照表。
- 论文写作可用 [英文方法和结果稿](BART_REPORT_EN.md)。权重、逐次训练日志、完整 Qwen 输入／输出以及 HTML 改写对照在 `runs/bfcl-person2-20261119-v1/` 中。
