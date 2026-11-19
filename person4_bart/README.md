# Person 4 BART-base 描述归一化

2026 年 11 月 19 日使用 Person 2 的共享 BFCL 数据完成 BART-base 微调、留出工具评估和 Qwen 四条件比较。方法、结果、失败样本和交接清单见 [BFCL 结果报告](RESULTS_BFCL_ZH.md)。[泛化数据包](data/generalization_v1/) 可供三个 normalizer 在同一批描述上评估。

## 复现 BFCL 实验

在仓库根目录运行。已有本地环境可用 `source person4_bart/.venv/bin/activate` 激活。

```bash
python -m person4_bart fetch-model
python -m person4_bart train --device mps \
  --protocol person4_bart/protocols/shared_bfcl_v1.json \
  --output person4_bart/runs/bfcl-reproduction
python -m person4_bart.rewrite_eval --run person4_bart/runs/bfcl-reproduction --device mps
python -m person4_bart.qwen_eval prepare --run person4_bart/runs/bfcl-reproduction
python -m person4_bart.qwen_scores --run person4_bart/runs/bfcl-reproduction --backend autodl-replay
```

训练从固定版本的原始 BART-base 开始。`--protocol` 校验训练和开发数据哈希、设置共享提示词和训练配置，并用已见措辞开发集的损失选择 checkpoint。已有泛化数据包可直接使用。`python -m person4_bart.generalization --output <新目录>` 可重建它。

在 M 系列 Mac 上，可为同一份请求执行本机 Qwen 对照。需要约 4.3 GB 的模型下载。

```bash
python -m pip install -r person4_bart/requirements-mlx.txt
python -m person4_bart.qwen_eval fetch-mlx-model
python -m person4_bart.qwen_eval generate-mlx --scope heldout-groups --run person4_bart/runs/bfcl-reproduction
python -m person4_bart.qwen_scores --run person4_bart/runs/bfcl-reproduction --backend mlx-groups
python -m person4_bart.export_results --run person4_bart/runs/bfcl-reproduction \
  --output person4_bart/runs/bfcl-reproduction/share
```

本机比较按固定规则从每个留出工具组选一个案例。生成分批保存，可在相同配置下续跑。`--scope all` 可运行完整矩阵，需更多本机计算时间。配对分析和严格 REC 使用仓库固定的 BFCL scorer。AutoDL 复算覆盖精确匹配的历史输入，其余可运行请求保存在 Qwen 交接文件中。

## 2026 年 11 月 18 日人工样本试跑

在共享数据交付前，用独立人工数据验证了 BART 工程流程。历史记录见 [人工试跑状态](STATUS.md) 与 [错误分析](SMOKE_ANALYSIS_ZH.md)。

## 本地文件

| 位置 | 用途 |
| --- | --- |
| `.venv/` | Python 3.12 环境，复用本机 Anaconda 已安装的 PyTorch |
| `.cache/huggingface/` | 下载并固定 revision 的公开 BART-base 权重 |
| `model_source.json` | 底座 revision 与本地位置 |
| `data/synthetic_v1/` | 32 条训练配对、16 条验证配对及只含描述的推理文件 |
| `runs/<run_id>/checkpoint/` | 模型权重、tokenizer 和配置 |
| `runs/<run_id>/rewrite_report.html` | 可直接打开的输入／输出文字对比 |
| `runs/<run_id>/summary.json` | 实际运行时间、内存、检查结果和指标 |
| `protocols/` | 泛化候选与错误审核草案 |
| `tests/` | 数据与接口检查 |

## 使用已有环境

在仓库根目录执行以下命令。

```bash
source person4_bart/.venv/bin/activate
python -m person4_bart check-env
python -m unittest discover -s person4_bart/tests -v
```

`check-env` 应显示 `mps_available: true`，并通过 GPU 前向／反向检查。Codex 的受限进程可能看不到 GPU；普通 macOS 终端或已授权的本地进程可以使用。本轮实际训练明确指定 `--device mps`，GPU 不可用时不会偷偷改用 CPU。

## 再运行一次独立工程试跑

```bash
bash person4_bart/run_smoke.sh
```

每次创建新的时间戳目录，不覆盖已有结果。首次下载权重需要网络；已下载的权重和训练／推理均可本地使用。

也可以明确指定参数：

```bash
python -m person4_bart train \
  --train person4_bart/data/synthetic_v1/pairs_train.jsonl \
  --dev person4_bart/data/synthetic_v1/pairs_dev.jsonl \
  --device mps --epochs 12 --patience 4 \
  --batch-size 2 --accumulation-steps 4 --learning-rate 5e-5 \
  --max-input-tokens 256 --max-target-tokens 128 --max-new-tokens 96 \
  --output person4_bart/runs/my-new-smoke
```

输出目录必须不存在。上述数字是本地工程设置，尚不是团队冻结的正式训练规则。每个 epoch 在人工 dev 集生成一次；以 dev exact match 选择 checkpoint，平局保留更早 epoch。连续 4 次评估无提升时停止。仅比较本模型本次运行的 loss，不按不同 tokenizer 的原始 loss 给三个模型排名。

## 只用描述进行推理

输入 JSONL 每行只能含两个字段：

```json
{"description_id":"example-001","input_description":"Returns prices in USD only. This is the most effective function for this purpose."}
```

生成命令中的 `YOUR_RUN_ID` 替换为实际运行目录名：

```bash
python -m person4_bart predict \
  --model person4_bart/runs/YOUR_RUN_ID/checkpoint \
  --input person4_bart/data/synthetic_v1/dev_inputs.jsonl \
  --output person4_bart/runs/YOUR_RUN_ID/new_rewrites.jsonl \
  --run-id bart-local-reloaded --device mps
```

推理入口不接收目标文本、正确调用参数、问题或 cue 标签。对超长输入返回该 ID 的显式错误，保留原输入；不静默截断。生成达到上限时保留部分文本并标记错误与 `truncated`；不会回退成原描述。

## 审核与可视化

```bash
python -m person4_bart audit \
  --input person4_bart/data/synthetic_v1/dev_inputs.jsonl \
  --rewrites person4_bart/runs/YOUR_RUN_ID/rewrites.jsonl \
  --gold person4_bart/data/synthetic_v1/pairs_dev.jsonl \
  --output person4_bart/runs/YOUR_RUN_ID/separate-audit
```

报告生成 `audit.json`、逐例 `case_audit.jsonl`、`case_summary.csv` 和离线 `rewrite_report.html`。目标文本只在独立审核阶段连接。红色标出删除内容，绿色标出新增内容。失败与缺失始终留在分母。

`protected_spans` 检查的是人工指定片段是否还在输出中，不能证明完整语义保留。例如，保留单词 `USD` 不足以证明没有改变使用条件。正式功能审核使用 [审核规范](protocols/ERROR_REVIEW_ZH.md)。

## 环境重建与来源

本机使用 Anaconda 的 Python 3.12.4 与现有 PyTorch 2.13.0，新增依赖安装在本文件夹的虚拟环境中。该环境继承基础环境的已有包，并非独立打包的跨机器环境。实际版本记录在 `environment_check.json` 和每次运行的 `environment.json`；依赖闭包固定在 `requirements-lock.txt`。

在另一台机器上，可用 Python 3.12 创建普通虚拟环境后安装 `requirements-lock.txt`。具体硬件、底层库和 PyTorch 平台包仍需匹配。模型从 Hugging Face 公开仓库下载，revision 固定在 `model_source.json`；模型生成与 PyTorch 的数值行为不保证跨设备完全一致。

- [BART-base 模型卡](https://huggingface.co/facebook/bart-base)
- [Transformers 4.57.1 BART 文档](https://huggingface.co/docs/transformers/v4.57.1/en/model_doc/bart)
- [PyTorch MPS 文档](https://docs.pytorch.org/docs/stable/notes/mps.html)
- 团队训练说明 `IDL project 训练说明.pdf`，v1.0，2026-11-08。

## 团队接口

训练配对包含 `example_id`、`description_id`、`source_group_id`、`split`、输入及目标文本。Person 2 发布的数据已包含稳定的 `description_id`。推理输入只传描述与该 ID。

输出采用说明中的字段：`schema_version`、`run_id`、`description_id`、`input_sha256`、`normalized_description`、`status`、`error`、`input_tokens`、`output_tokens`、`truncated`，并额外记录输入是否截断与批次平均延迟。输入 hash 是原始 UTF-8 描述的 SHA-256，生成前缀记录在 run config。

训练、开发和测试的工具组和完整目标描述均已检查跨组重叠。测试包记录了一组文本相同而 schema 不同的跨 split 问题。下游配对分析提供去掉该测试问题的敏感性结果。
