# BART 方法与结果写作草案

此页保存工程阶段的写作准备。实际 BFCL 方法和数值见 [英文报告稿](../BART_REPORT_EN.md) 与 [BFCL 交接报告](../RESULTS_BFCL_ZH.md)。

当前仅完成独立工程准备和人工样本试跑。正式项目数据、团队冻结协议和下游结果尚待接入。实际本地进度见 `../STATUS.md`；不要把工程试跑指标写成正式 BFCL 结果。

## 可据现有实现填写的方法

模型使用公开 `facebook/bart-base` 预训练权重，具体 revision 记录在 `model_source.json`。BART 为 encoder–decoder，监督目标是输入描述到功能性目标描述的 token negative log-likelihood。padding 标签置为 -100；梯度累积按有效 target token 数加权。模型只改写 description，工具名、参数 schema 与问题不由模型生成。

本地工程采用 FP32、eager attention、MPS 和 greedy generation。训练／验证文件分离，固定生成上限，不依赖推理时的 gold 长度。记录 source hash、代码 hash、seed、训练配置、逐 epoch loss、选中 epoch、运行时间和观察到的内存计数器。checkpoint 保存权重、tokenizer 及配置，重载后重新生成并逐 ID 比较。

## 正式实验待填写

- 最终 protocol_version、数据／split／grouping／cue-pool 版本与 hash。
- 三模型统一的输入模板、数据组成、调参预算、early stopping 与模型选择规则。
- BART 最终超参数、各类截断／异常的处理与统计。
- 匹配 Qwen 控制、评估矩阵、权重 revision、后端与 scorer 版本。
- 三类泛化结果、功能审核、逐例诊断、配对／工具组统计分析。

## 结果与局限

工程运行只回答本机能否完成训练、保存、重载、生成和审核流程。正式结果需同时解释相对 Clean 的偏好偏移、调用正确性与功能保留，不能只凭训练 loss 或 exact match 宣称缓解有效。

BART 与 FLAN-T5 的比较同时涉及预训练与 instruction tuning 差异，不宜将所有差异归因于 encoder–decoder 架构。MPS 与 CUDA 的数值及随机性不同；下游控制必须匹配。字面约束检查可能漏掉语义错误，也可能将合法释义判为未匹配，因此需要独立人工审核。
