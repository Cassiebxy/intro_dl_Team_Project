# Person 4 人工试跑记录

此页归档 11 月 18 日的工程试跑。共享 BFCL 数据到位后的训练与评估见 [BFCL 结果报告](RESULTS_BFCL_ZH.md)。

更新时间：2026-11-18。所有新增工作保存在本地 `person4_bart/`，未提交或推送 GitHub。

## 已完成并实测

| 项目 | 状态与证据 |
| --- | --- |
| Python 环境 | `.venv/`，Python 3.12.4，复用已有 Anaconda PyTorch；35 个依赖的版本与约束已核对，见 `requirements-lock.txt` |
| Apple GPU | MacBook Air，M4，16 GB，MPS 前向／反向检查通过；见 `environment_check.json` |
| BART 底座 | `facebook/bart-base`，revision `aadd2ab0ae0c8268c7c9693540e9904811f36177`，缓存和路径见 `model_source.json` |
| 人工数据 | 32 条训练配对／8 个工具组，16 条验证配对／4 个独立工具组；25% clean identity，无跨组交集；不是 BFCL |
| 训练与 checkpoint | 已在 MPS 完成全参数微调、保存和重载，最终目录为 `runs/synthetic-smoke-20261118-02/` |
| 输出接口与可视化 | 逐 ID 输出、hash、错误与截断记录；离线 HTML 对比、JSONL／CSV、训练曲线已生成 |
| 数据／接口检查 | 12 项单元检查通过，见 `TEST_RESULTS.md` |
| 独立推理入口 | 已用保存的 checkpoint 在额外 4 条干净人工描述上执行 `predict` 并审核 |
| 泛化与审核草案 | `protocols/` 中有三类泛化定义、8 条未审核候选 cue、错误规范及空白审核表；没有冻结 final test |

## 最终工程运行

最终使用 `runs/synthetic-smoke-20261118-02/`。首次运行 `...-01/` 也保留；第二次将底座继承的摘要生成选项显式清理，关闭 no-repeat n-gram 限制，并核实自然 EOS 恰在上限时不会被误记为截断。

- 设备：MPS，FP32，eager attention。
- 训练：micro batch 2，梯度累积 4，有效 batch 8，AdamW，学习率 5e-5，seed 42。
- 输入／目标长度限额：256／128；生成上限固定 96 token，greedy，不使用 gold 长度。
- 实际完成 7 个 epoch、28 次 optimizer update，选中第 3 个 epoch；之后连续 4 次 exact match 未提升，按工程规则停止。
- 总耗时 **55.268 秒**，包含底座检查、训练、验证、保存重载与最终生成；它不是正式数据训练时间的预测。
- 选中 checkpoint 重载后，16 条验证输出与保存前逐 ID 一致。
- 人工验证集：**16/16 exact match**，无缺失、错误或截断；字面受保护片段检查 16/16。训练样本为 32/32 exact match。
- 观察到的 MPS 驱动分配最大值 3,701,374,976 bytes，约 3.45 GiB；MPS tensor 分配最大值约 2.22 GiB。它们是采样的分配计数器，不是连续测得的整机内存峰值。

数据和训练时的源码 hash、完整配置及原始指标保存在该目录的 `run_config.json`、`history.jsonl`、`summary.json` 和 `reload_check.json`。此后源码加入了 BFCL 训练及评估接口。

## 必须保留的失败发现

额外 4 条干净描述中，3 条原样保留，1 条发生过删：

```text
输入：Uploads a file only after explicit authorization. The maximum file size is 5 MB.
输出：Uploads a file only after explicit authorization.
```

**5 MB 文件上限被删除，属于 over_delete 和 clean_harm。** 这说明小型人工 dev 集 16/16，不能推出一般功能保留成功。

详见 `runs/synthetic-smoke-20261118-02/diagnostic_review/rewrite_report.html` 和 `SMOKE_ANALYSIS_ZH.md`。这 4 条没有参与训练、checkpoint 选择或后续调参。辅助诊断是少量人工例子，不是团队的正式泛化结果。自动字面审核与本次模型审阅也不是独立真人签收。

## 本轮范围

本轮没有训练真实 BFCL 工具，没有运行 Qwen，也没有宣称缓解或泛化已成功。正式团队数据交付后，需要对齐 C0/C1、指令、模型选择规则和 ID 映射，再从原始 BART-base 开始正式训练。CUDA 路径提供接口，但本轮实测设备仅为 MPS。

查阅 [使用与复现说明](README.md) 或 [人工试跑分析](SMOKE_ANALYSIS_ZH.md)。本机 `runs/synthetic-smoke-20261118-02/` 另有 `rewrite_report.html`、`diagnostic_review/rewrite_report.html` 和 `training_curves.png`。
