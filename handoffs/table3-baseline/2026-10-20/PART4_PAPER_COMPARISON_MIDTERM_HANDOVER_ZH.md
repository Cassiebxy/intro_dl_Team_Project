> GitHub阅读层：先读[新会话总交接](HANDOVER_NEW_SESSION_ZH.md)。完整原始证据、代码和便携重放脚本在同目录ZIP；下文重放命令均在解压后的包根目录执行。ZIP保留原准备时说明，当前发布状态以本目录README和reviews为准。

# Part 4｜论文对照与midterm报告整合交接

日期：2026-10-20。负责人姓名由团队确认。先读本文件，再看[rubric逐项映射](MIDTERM_RUBRIC_CHECKLIST_ZH.md)。当前数字来自我们本地实际运行，尚待Part3队友独立签收；不要把本交接文当成最终已提交midterm。

## 1. 你已经收到的材料
1. 完整3096条请求/原始响应/逐例分数、summary和哈希；便携重放不需GPU。
2. 六行论文vs本地对照、十二组order结果、失败统计、代表输出和两张可编辑源数据支持的PNG/PDF图。
3. 评分口径、冻结环境、已知差异、唯一解析失败和Part3签收模板。
4. 用户提供的3张midterm评分标准截图的来源记录，以及本包逐行转写/落实清单；截图在原聊天中可核对。

你的工作是独立核对论文、结合Part3签收解释结果、整合全组材料并检查rubric。不要重搭baseline或把后续normalizer写成已训练。

## 2. 已完成的baseline与边界
目标是Table3的Qwen2.5-7B六行：258×6×2=3096。它回答描述措辞与工具正确使用偏移的问题；未训练模型。
正式运行于2026-10-20 15:47 EDT完成，技术故障0、解析失败1、截断0，自动评分重放一致。
原论文对照是Section2.2.1/Table3，不是658案例/17模型的Section3和Table13。
只有original-vs-edited双工具竞争；没有额外clean-vs-clean、单工具无编辑控制、router条件或normalizer消融。不能把original候选工具自身CUR当成独立clean-control实验结果。

## 3. 论文参照与六行结果
已于今日核对[正式PDF](https://aclanthology.org/2025.emnlp-main.1060.pdf)第3页（印刷页20956）Table3中的Qwen六行。请你仍独立再核一次；不必从现有数值倒推论文四舍五入前计数。

| Cue | edited次数 | 本地edited CUR | 本地original CUR | 本地ratio | 本地CR | 论文 edited / original / ratio / CR | CR差(pp) |
|---|---|---|---|---|---|---|---|
| 1 | 244/516 | 47.29% | 23.84% | 1.984 | 71.12% | 49.8% / 25.4% / 1.96 / 75.2% | -4.08 |
| 2 | 270/516 | 52.33% | 18.22% | 2.872 | 70.54% | 58.1% / 18.2% / 3.19 / 76.4% | -5.86 |
| 3 | 269/516 | 52.13% | 18.60% | 2.802 | 70.74% | 59.9% / 16.3% / 3.68 / 76.2% | -5.46 |
| 4 | 282/516 | 54.65% | 16.47% | 3.318 | 71.12% | 61.4% / 14.7% / 4.17 / 76.2% | -5.08 |
| 5 | 304/516 | 58.91% | 11.82% | 4.984 | 70.74% | 65.3% / 10.7% / 6.13 / 76.0% | -5.26 |
| 6 | 316/516 | 61.24% | 9.88% | 6.196 | 71.12% | 66.9% / 8.5% / 7.84 / 75.4% | -4.28 |

完整精度、整数计数与全部差值在[tables/paper_vs_local_table3.csv](tables/paper_vs_local_table3.csv)。CUR/CR差值用百分点(pp)，ratio差值为无单位差；别把两者混写。

可以陈述：合并双顺序后，六条cue的edited CUR都高于original，ratio约1.984–6.196；cue6为61.24%对9.88%，ratio6.196，CR71.12%。
需要同时陈述：这不是论文数值的精确复现；本地CR约70.54–71.12%，较论文低4.08–5.86pp。差异原因尚未定位，不能直接归因于MPS、模型能力下降或某个特定实现。
不能陈述：normalizer已缓解偏差、所有顺序都偏爱改写、统计显著、跨模型/跨数据泛化、独立多seed复现成功。

## 4. 顺序分析：报告必须保留的重要发现
| Cue | 原始在前 edited CUR | 原始在前 original CUR | 原始在前ratio | 改写在前 edited CUR | 改写在前 original CUR | 改写在前ratio | edited顺序差(pp) |
|---|---|---|---|---|---|---|---|
| 1 | 23.26% | 47.29% | 0.492 | 71.32% | 0.39% | 184 | +48.06 |
| 2 | 34.11% | 36.05% | 0.946 | 70.54% | 0.39% | 182 | +36.43 |
| 3 | 34.11% | 36.82% | 0.926 | 70.16% | 0.39% | 181 | +36.05 |
| 4 | 38.37% | 32.56% | 1.179 | 70.93% | 0.39% | 183 | +32.56 |
| 5 | 46.90% | 23.26% | 2.017 | 70.93% | 0.39% | 183 | +24.03 |
| 6 | 50.39% | 19.77% | 2.549 | 72.09% | 0.00% | undefined | +21.71 |

重点：original-first下cue1–3的edited CUR低于original；edited-first下edited CUR约70–72%，original几乎0。cue6 edited-first分母为0，ratio为undefined，不能画成0或任意截断的无限大。
因此六行合并结果能支持“在本设置下总体复现改写优势方向”，但不能支持“优势不受工具顺序影响”。本实验交换顺序同时重分配位置后缀1/2，位置和名称标签存在耦合；不能单凭这张表识别纯位置效应或证明程序错误。
当前12种设置是六cue×两顺序，不是12个独立数据集；同一case在条件间重复，不能当3096个相互独立的原始query来做置信推断。
图见[顺序效应](figures/order_effects.png)，报告时应与主对照图一起展示，避免只选有利结果。

## 5. midterm可用的英文段落（待Part3签收及全组编辑）
### Baseline method
We reproduced the Qwen2.5-7B component of the assertive-cue experiment in Table 3 of Faghih et al. (2025). For each of 258 BFCL live_simple cases, we constructed two functionally identical candidate tools and appended one of six fixed cues to one tool description. Both presentation orders were evaluated, yielding 3,096 requests. We used the public Qwen2.5-7B-Instruct checkpoint with BF16 weights on an Apple Silicon GPU. Prompts and parameter checking were adapted from the pinned released implementation; backend and random-number differences are documented.

### Results and limitation
After aggregating both orders, edited-tool CUR exceeded original-tool CUR for all six cues, with ratios ranging from 1.984 to 6.196. For cue 6, edited and original CUR were 61.24% and 9.88%, respectively, with a CR of 71.12%. These values differ from the published reference, and substantial order dependence remains: for the first three cues, edited-tool CUR did not exceed original-tool CUR in the original-first condition. We therefore interpret the experiment as a directional reproduction under our local runtime, rather than exact numerical or order-robust replication. One malformed output was retained as a failure in the original denominator.

### Proposed extension / next steps
Our proposed extension is a trainable description normalizer that rewrites the description field while preserving the tool name and argument schema. Normalizer training and evaluation have not yet been completed. Next, we will finalize grouped train/dev/test and held-out-style protocols, compare the planned normalizer backbones under shared evaluation settings, and test both downstream bias reduction and preservation of performance on clean descriptions.

这三段不是整篇报告；abstract、motivation、literature、训练loss、contributions和future plan仍需全组填充/确认。

## 6. 按4–5页组织的建议（不是rubric额外规定）
| 段落 | 建议篇幅 | 该放什么 |
|---|---|---|
| Abstract + motivation/objectives | 约0.5页 | 给非专家的问题、受益者、当前baseline结论及normalizer目标 |
| Related work/background | 约0.5页 | 1–2核心文献；至少一篇把baseline/指标与问题连接；全篇文献达到截图2–3 minimum |
| Method + data + metrics | 约1页 | baseline输入输出、258×6×2、CUR/CR；normalizer标planned；本阶段loss=N/A（纯推理） |
| Baseline/reproduction + results | 约1.5页 | 自己运行证据、主表/图、顺序图、失败例、论文差值 |
| Discussion + next steps + contributions | 约0.5–1页 | 差异/风险、2–3具体下一步、当前真实分工、GitHub链接 |

页数4–5已在截图中显示，但是否包含参考文献、模板完整URL、deadline/提交流程未由截图完整核实；负责人查原课程页面。不要把旧timeline当官方确认。

## 7. rubric的证据与当前缺口
- Mandatory baseline：真实输入、响应、score、对照和环境已备齐；Part3独立签收待完成。
- Baseline reproduction evidence：从本包选一条成功和一条失败输出，保留case ID、配置/权重revision、运行日志/哈希；论文表格本身不是我们的证据。
- Experimental depth/iteration：诚实展示6cue×2order共12设置；20条smoke只是端到端验证、与正式集重叠；重放是验证而非新的模型实验。没有多seed重复或训练曲线，不得虚构。
- Model description：已有[可编辑方法图素材](figures/PIPELINE_IO_ZH.md)，可按报告排版重绘。normalizer输入“manipulated description”→输出“normalized description”→双工具LLM→CUR/CR，同时把已完成baseline和planned normalizer视觉区分。
- Loss function：本baseline无训练loss；后续supervised seq2seq token cross-entropy只能作为拟采用方法，须训练负责人确认。
- Error/ablation/bonus行截图中没有填写midterm细则；失败分析和现有order/cue对比可帮助报告，但不能说这是官方额外硬性评分项，也不能编造权重。
- Contributions：proposal里的旧文字只描述proposal写作，不代表今天分工；由四人确认姓名与实际贡献。
- GitHub：当前公开README仍写full run in progress，可能需要在用户批准本包后更新完成状态；本包现已获用户授权发布；完整证据在ZIP，GitHub首页状态已同步。

## 8. 最后核对与交给全组
- [ ] Part3签收完成或明确标为待核验；数值、分母和唯一parse error一致。
- [ ] 自己核对论文Table3六行、模型名称、cue原文；引用Faghih为Kazem，别沿用proposal中错误的A.首字母。
- [ ] 同时展示pooled与order结果；解释差异时把已证实与待验证假设分开。
- [ ] 检查1–2核心文献连接及全篇2–3 minimum引用；本包[参考文献](REFERENCES.bib)提供3个已核对来源。
- [ ] 按官方模板合并4–5页草稿；当前normalizer/teacher/split进展向对应队友确认。
- [ ] 确认2–3具体下一步、真实contribution和GitHub链接；未完成事项不写成成果。
- [ ] 交全组：论文vs本地表、order图、完整报告草稿、局限/问题清单与rubric checklist。

### 尚未解释的问题清单
1. 为什么本地CR整体低于论文约4–6pp？后端/精度、未公开原revision或seed、数据/评估细节都只是候选解释，尚无消融证据。
2. edited-first几乎不正确使用original的强位置/标签不对称，是否也在论文对应逐例输出出现？是否值得以后新增clean-vs-clean与名称控制？本轮未运行这些控制。
3. 这258案例后续如何与normalizer split及held-out style边界衔接？需要独立协议，不能因为做了baseline就宣布无泄漏。
4. 唯一格式失败若做宽松解析，是否改变分数？主结果不修复；如诊断另列。
