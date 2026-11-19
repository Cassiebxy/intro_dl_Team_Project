# Person 4 泛化测试设计草案

此页保存候选设计。已生成并由 BART 评估的版本见 [BFCL 泛化数据包](../data/generalization_v1/README.md)。

状态：2026-11-18 的独立准备材料；候选池不是已冻结的 final test。尚未拿到全组最终训练／开发 cue 池，因此此处不宣称任何候选已经满足 unseen 条件。

## 三种泛化分别定义

| 切片 | 必须满足的隔离条件 | 单独回答的问题 |
| --- | --- | --- |
| 未见措辞 | 同一 cue family 的模板及近似改写不出现在训练与调参中 | 是否只记住固定句子 |
| 未见 cue 类型 | 整个诱导类别不进入训练及调参，包括模型选择用的 dev | 是否能处理不同诱导策略 |
| 未见工具 | source tool group 及关联、近重复描述不跨 train/dev/test | 是否依赖记忆特定工具 |

措辞／类别切片还要注明工具是否见过。使用相同 held-out 工具分别测试 seen cue、unseen wording、unseen family，有助于区分变化来源。六条 Table 3 assertive cue 的留句实验应标为措辞／模板泛化，不能直接称为全新类别泛化。

## 候选编写与审核

1. 先登记 cue family、模板 ID、完整文字、插入位置、来源和编写人。当前候选位于 `cue_candidates.jsonl`，均为合成实验文字，不是维护、推荐或用户数量的事实声明。
2. 每个候选应只加入非功能性诱导，不修改原能力、参数含义、单位、否定、授权条件或使用范围。不修改工具名称或 schema。
3. 至少安排两位成员独立检查，再记录分歧和处理理由；目前尚未执行团队审核。审核根据语义与协议，不根据 Qwen 或某个 normalizer 的测试效果筛选。
4. 专业语气、简短说明和合法使用限制不自动视为攻击。带新增功能、示例参数错误或条件改变的候选标为 functional drift，不能混入主要等价性实验。
5. 插入位置是独立因素。若只研究措辞，先固定位置；若研究位置变化，明确标为另一切片，保持功能句不变。
6. 对最终训练与 dev cue 池做文本、近似模板和 family 交叉审核。曾用于模型选择的候选不能再算完全未见。

## 冻结时需要发布的内容

- protocol_version、split/grouping version、cue pool version 与每份文件 SHA-256。
- 允许评估的 source case/group ID 清单、三类切片标签、训练工具重叠标志。
- 完整 cue 文本、位置、来源、人工审核记录和排除理由。
- 正确调用及目标描述保存在评分文件中，不放进 normalizer 输入。
- 所有模型使用完全相同的 description ID 集合，不按模型失败情况删样本。

当前没有建立正式测试工具列表，没有生成 BFCL final-test variants，也没有运行这些候选。

## 下游比较与结果说明

沿用匹配的 Clean、Manipulated、Manipulated→Normalizer、Clean→Normalizer 四条件；归一化两个候选描述。顺序和名称映射独立交叉，并固定每个 case 的配对 seed。控制结果只有在 Qwen 权重、prompt、后端、精度及解码一致时才能共享。

按 family、工具是否见过、顺序和名称映射报告 SR、ratio、AAC、CUR、历史 CR、严格 REC 及失败率。优先比较相对匹配 Clean 的偏移，而不是要求每个格子的选择率都等于 50%。失败保留在总分母；区间估计以 source tool group 配对重采样。

Person 4 整合协议与测试清单，并运行、分析自己的 BART。其余模型负责人分别执行并分析自己的测试；Person 3 汇总比较表。三模型结果和功能审核完成前不下泛化成功结论。
