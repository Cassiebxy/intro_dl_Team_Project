# Person 3: FLAN-T5-base, cue ablation, and comparisons

Implementation based on main commit `8cf4b2e5f9d7305d611c626d79f1c0f1ef49836f`.

**Status: code and CPU/data checks completed; FLAN-T5-base training and Qwen inference NOT run.** No base weights or base scores are claimed. The editing environment had no PyTorch installed. Training and prediction must still pass the smoke run on the target machine. Existing Person 2 and Person 4 outputs are reused only for the descriptive dev text comparison.

## 实验做什么

- `multi`: 从预训练 FLAN-T5-base 开始，沿用 Person 2 的 400 条训练数据。
- `single`: 同样的 100 个工具描述，各保留 1 条 clean，另将选中的 cue 样本重复 3 次。共 400 次样本曝光、25% clean，与 multi 同为 3 epochs、75 次 optimizer updates。默认 `suffix_1`，另两种 cue 可分别运行作为敏感性分析。
- 多 cue 指训练集中有三种措辞，不是一条描述叠加三个 cue。原始数据同时改变措辞、cue family 和插入位置，因此不能把差异解释为纯粹的 cue 数量效应。单 cue 的重复曝光也属于实验差异。
- rule baseline 只删训练中已知的三个完整句子，且只在描述边界匹配；不根据测试结果扩充规则。

共享原始 train/dev/test 划分，先校验 manifest 的全部哈希与 group/tool/input 的跨集合重叠。保持 Person 2 的 prompt、AdamW 默认参数、5e-5 learning rate、effective batch 16、microbatch 4、seed 42。复现其按 microbatch 样本数加权的训练 loss，以及 seen-wording dev batch loss 均值的 checkpoint selection。BART 的 token weighting 不同，汇总时需要注明。

生成按 4 条一批，greedy decode，使用 Person 2 的输入长度 cap。输入不静默截断；特别长的输入可能导致显存不足。默认 FP32，自动选择 CUDA/MPS/CPU。不要在 8 GB Mac 上直接启动完整训练，先在目标机器做 smoke。

## 从仓库根目录运行

```bash
python -m pip install -r experiments/person3-base/requirements.txt
python experiments/person3-base/pipeline.py audit
python -m unittest discover -s experiments/person3-base -v
```

准备本地 `google/flan-t5-base` 模型目录，然后把下面 `/path/to/flan-t5-base` 换为实际路径。也可使用 `--model google/flan-t5-base --revision <40位模型commit SHA>` 下载固定版本。所有输出目录必须不存在，避免覆盖旧证据。

```bash
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --smoke --output experiments/person3-base/runs/smoke
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --mode multi --output experiments/person3-base/runs/base-multi
python experiments/person3-base/pipeline.py train --model /path/to/flan-t5-base --mode single --single-cue suffix_1 --output experiments/person3-base/runs/base-single
```

正式训练保存 `checkpoint/`（最佳）、`last/`（最后一轮）、optimizer 状态、训练曝光记录、loss、环境与数据哈希，并重新加载最佳模型生成 dev 改写。`last` 用于保留恢复素材，当前 CLI **尚无自动 resume**，中断后不要把重新训练说成连续恢复。Smoke 只检查 16 条训练和 8 条验证，不可用于正式结果。

评估最佳模型，不能用 test 决定 checkpoint 或调参：

```bash
python experiments/person3-base/pipeline.py predict --model experiments/person3-base/runs/base-multi/checkpoint --inputs experiments/person2-small/data/normalizer_inputs_test.jsonl --output experiments/person3-base/runs/base-multi-test
python experiments/person3-base/pipeline.py score --pairs experiments/person2-small/data/pairs_test.jsonl --rewrites experiments/person3-base/runs/base-multi-test/rewrites.jsonl --method base-multi --output experiments/person3-base/runs/base-multi-test-score
```

同样对 single 运行。共同泛化集则将输入替换为 `person4_bart/data/generalization_v1/normalizer_inputs_test.jsonl`，评分 pairs 替换为同目录 `pairs_test.jsonl`，并换用新输出目录。由于团队已检查该泛化集，后续若根据其结果修改模型，应将它当作诊断集，另留最终未见测试集。

规则 baseline 和 dev 评分：

```bash
python experiments/person3-base/pipeline.py predict --rule --inputs experiments/person2-small/data/normalizer_inputs_dev.jsonl --output experiments/person3-base/runs/rules-dev
python experiments/person3-base/pipeline.py score --pairs experiments/person2-small/data/pairs_dev.jsonl --rewrites experiments/person3-base/runs/rules-dev/rewrites.jsonl --method rules --output experiments/person3-base/runs/rules-dev-score
```

## 下游 Qwen 接口

```bash
python experiments/person3-base/prepare_qwen.py --pairs experiments/person2-small/data/pairs_dev.jsonl --rewrites experiments/person3-base/runs/base-multi/rewrites.jsonl --method base-multi --output experiments/person3-base/runs/qwen-base-multi-dev
python table3/controlled_baseline/run_qwen_controlled.py --input experiments/person3-base/runs/qwen-base-multi-dev/controlled_inputs.jsonl --mapping experiments/person3-base/runs/qwen-base-multi-dev/controlled_mapping.jsonl --validate-only
```

导出 Clean、Manipulated、Normalized、Clean-through-normalizer。两候选的 description 都改写，question/name/schema 保持不变，保留原来的 order/name mapping/seed。全 dev 导出 1,400 请求，35 cases，覆盖两种顺序和两种名称映射；与 Person 2 的 16-case 子集不同，不能直接拿其汇总分数对比。给所有方法导出同样矩阵，交给 Person 1 用冻结 Qwen 配置运行并用共同评分器打分。本脚本不自动提交 GPU 工作，也不假定旧 archive 可复用。

导出遇到缺失、错误或截断的改写会失败，不偷偷删除失败样本。应先保留并报告这些失败，再决定共同的失败评分规则。最后的下游汇总需要记录：方法、数据集、Qwen revision/backend/decoding、cue、order、name mapping、分母、edited selection、CUR、条件参数正确率、strict response correctness 和 paired transitions。不要混合 AutoDL 与本地量化 Qwen 的结果。该版本提供请求导出；下游结果汇总需要真实共同评分结果后再完成。

## 汇总与已经验证的结果

`score` 可读取 Person 2 的 `generated` 和 Person 4 的 `normalized_description` 格式；严格要求 description ID 覆盖一致。有 hash 的记录也校验输入 hash。`compare` 拒绝混合不同 pairs 文件的 hash，并生成 CSV/PNG/SVG：

```bash
python experiments/person3-base/pipeline.py compare --summaries path/to/rules/summary.json path/to/small/summary.json path/to/base/summary.json path/to/bart/summary.json --output experiments/person3-base/runs/comparison
```

当前 [dev 比较表](evidence/comparison.csv) 与 [图](evidence/comparison.svg) 由实际运行评分脚本得到：rules 92/115、已发表 small 104/115、已发表 BART 112/115。规则在 clean 和三个已知 cue 上为 92/92，在 dev 新措辞上为 0/23。这是同一组 23 描述的五个变体，不能当作 115 个独立样本，也不是最终 test 排名。Base 待训练，不填虚构分数。

Exact recovery 只测逐字恢复，不等于完整语义正确，也不能单独证明消除选择偏差。`review_mismatches.jsonl` 留下逐例对比，人工标注保留了什么、误删了什么、漏删了什么，并选成功/失败案例写报告。

验证：3 个 unittest 通过；400/115/95 数据审计通过；规则实际运行；small/BART dev 重评分与原报告一致；图表生成成功；规则 dev 导出的 1,400 Qwen 请求通过原 runner `--validate-only`。没有运行深度学习训练或下游推理。
