# 零上下文新会话交接｜Table 3 baseline → Part 3 / Part 4

更新时间：2026-10-20（America/New_York）。这份文件是新会话入口，不要求你读旧聊天。GitHub仓库：https://github.com/Cassiebxy/intro_dl_Team_Project；交接目录：`handoffs/table3-baseline/2026-10-20/`（[在线入口](https://github.com/Cassiebxy/intro_dl_Team_Project/tree/main/handoffs/table3-baseline/2026-10-20)）。

## 1. 我们在做什么任务
CMU11-785小组项目：**Mitigating Tool Preference Bias in LLM Agents via Trainable Description Normalization**。先复现“工具功能/参数相同，仅description措辞不同会引发偏好”的现象，再训练description normalizer缓解偏差。
当前只完成第一阶段的窄baseline：Faghih et al. EMNLP2025 Section2.2.1/Table3中Qwen2.5-7B的六条assertive cues，258个BFCL live_simple案例×6cue×2工具顺序=**3096次正式推理**。每cue516，每cue/order258。不是Table13、不是全论文、不是normalizer训练。
用户当前要求：把已完成baseline交给Part3评分复核与Part4论文对照/报告整合；不重跑模型、不扩大实验。团队目标原为周四10/22前完成baseline，已于10/20完成；midterm正式deadline不能从内部目标推断，需查课程通知。

## 2. 已完成什么（都有证据）
- 258canonical案例与答案核对；六cue、双顺序、roles/expected和exact prompt冻结，输入总3096。
- 官方`Qwen/Qwen2.5-7B-Instruct`，revision`a09a35458c702b33eeacc393d103063234e8bc28`；上游commit`05be5f136f00fe66acf0aa853d7bcd44c300946c`。
- 本地M5 Max/128GB，BF16、MPS/Transformers4.57.1、PyTorch2.9.1；20条smoke通过，正式3096条于2026-10-20 **15:47 EDT**结束。
- 全部3096个唯一response已保存，无技术故障/截断，1条语法解析失败保留在分母。
- 自动逐例评分、六行summary、十二组order summary、论文对照、失败统计及图表生成；离线重放与原score一致。原项目测试54通过；便携核验又对照固定官方dup checker的3034条非空调用结果一致，另有6条手工真值边界。
- 完整本地证据包已制作，并经用户授权上传本目录；GitHub阅读层可直接看文档、CSV、PNG/PDF，完整证据/代码/重放入口在ZIP。
- **这些是已有自动核验，不是新会话Part3已经独立完成，也不等于任何真人队友已签收。**

## 3. 当前卡在哪里
没有技术运行阻塞，模型已跑完。现在卡在**交接后的独立复核与报告整合尚未执行**：
1. Part3需要独立重放、人工/逐例检查评分边界与角色、确认唯一parse error及分母，并保存可追踪review报告和leftovers。
2. Part4需要检查Part3的真实证据，不仅看“PASS”字样；然后核对论文六行、解释order差异、按midterm rubric整合全组报告。
3. 完整template URL被截图裁切，截图提供4–5页但是否含文献/正式deadline未确认；贡献姓名与当前normalizer进展要向团队核实。
4. 正式结果与论文有差异，原因尚未定位；禁止把后端差异当成已验证原因。normalizer、正式split/held-out-style协议、clean控制和多seed实验均未完成。

接手前先从GitHub最新`reviews/part3/`、`reviews/part4/`读STATUS、REVIEW_REPORT、LEFTOVERS；本交接写作时均PENDING，之后可能已被更新，不要覆盖后续同学的进度。

## 4. 关键结果与可用结论
- pooled六cue均edited CUR>original；ratio约1.984–6.196。cue6：edited61.24%、original9.88%、ratio6.196、CR71.12%。
- 本地CR约70.54–71.12%，比论文低4.08–5.86个百分点；属于方向性而非精确数值复现。
- 强顺序/名称标签不对称：original-first下cue1–3没有edited优势；edited-first下original CUR几乎0。位置与1/2后缀同时变化，不能据此单独证明纯位置因果效应。
- 两工具CUR定义上可重叠，不是互补概率；本次both-correct实际为0。ratio分母0写undefined，不写0或随意封顶。
- 唯一parse错误：`live_simple_108-65-0__cue4__original_first`，字符串中未转义的`"checks"`破坏JSON；不修复/重生成主结果，仍计cue4的516分母。
- 互斥请求分类：2195至少一个工具正确、812已知工具参数失败、61无调用、27未知工具名、1解析失败。未知模型输出名不是canonical源数据的phantom缺口。

## 5. GitHub材料怎么找
| 位置 | 用途 |
|---|---|
| [README](README.md)、[Part3交接](PART3_SCORING_VALIDATION_HANDOVER_ZH.md)、[Part4交接](PART4_PAPER_COMPARISON_MIDTERM_HANDOVER_ZH.md) | 阅读顺序与具体职责 |
| [完整ZIP](TABLE3_BASELINE_HANDOVER_2026-10-20.zip) / [PACKAGE_METADATA](PACKAGE_METADATA.json) | 原始输入/输出/score、固定代码和来源、环境、portable replay；先核对ZIP SHA256 |
| [tables](tables/) | 3096逐例CSV、六行论文vs本地、order分析、失败统计和代表案例 |
| [figures](figures/) | PNG/PDF主结果/顺序图、可编辑方法图和图注 |
| [rubric清单](MIDTERM_RUBRIC_CHECKLIST_ZH.md)、[REFERENCES](REFERENCES.bib) | 评分截图逐行落实、3个核对过的引用 |
| [Part3 reviews](reviews/part3/) | Part3独立复核与遗留项，开始前必读 |
| [Part4 reviews](reviews/part4/) | 对Part3的检查记录、rubric进度和待解决问题 |
| [启动prompts](prompts/) | 分别给Part3/Part4的新会话首条消息 |

完整ZIP SHA256：`7523548350c7fe67091efd1ea5b13027ee04da8927905897543f82f8534b283a`；解压内MANIFEST SHA256：`691ba4a65d6d156005bc358eb99d514a4c698e784d21b49458a73bb07bdddc2b`。最终以同目录PACKAGE_METADATA为机器可读依据。
解压得到`TABLE3_BASELINE_HANDOVER_2026-10-20/`，进入该目录运行：
```sh
python3 -B -X utf8 -S scripts/verify_and_replay.py
```
Windows可将python3换python。Python>=3.10，无需下载模型或安装torch。输出到包内`validation/replay/`；新会话要保留自己的核验输出，不把原包已有的自动结果当新执行证据。

## 6. 下一步计划与交付接口
### Part3先做
读最新review状态→获取并校验ZIP→离线重放→抽查CUR/CR/roles/alias/唯一错误→形成独立技术结论。
把结论写到`reviews/part3/REVIEW_REPORT.md`，更新`STATUS.json`和`LEFTOVERS.md`，新增自己的verification JSON。报告包括源commit/ZIP/manifest哈希、运行环境、核验命令/结果、抽查case IDs、是否改分数、blocker及影响。
无错误可将technical_review_status记PASS，但reviewer_type须如实标明human或assistant；只有真人明确签收才更新human_signoff。若当前评分有问题，写新版本及全量差异，原ZIP不变。

### Part4再做，并检查Part3
读取Part3三份交接结果，核对其源包/哈希和真实核验输出；能本地运行时再重放一次，检查review结论是否与CSV/raw evidence一致、leftovers是否影响六行数字和报告主张。
若Part3缺失/FAIL或存在影响分数的未解决blocker，先完成不依赖最终分数的结构/文献/rubric准备，并明确标“评分待确认”；不要把baseline写成已独立验证。能解决的文档/可重放小问题可核实后修正并留记录，不能隐瞒遗留项。
在`reviews/part4/PART3_CHECK.md`记录检查结果；再按rubric完成对照/顺序/失败/局限/2–3下一步和贡献待确认列表。建议报告稿写到`report/MIDTERM_INTEGRATION_DRAFT.md`，其状态是draft而非已提交。

## 7. 踩过的坑
1. **范围混淆**：Table3=3096；Table13是后续可选大矩阵，不能混入本任务，也不需要先训练normalizer。
2. **角色不能按后缀猜**：工具按呈现位置命名1/2，反转顺序会交换original/edited含义；始终读roles。
3. **评分不是选择率或strict-all**：同工具一对一错不能计CUR；两工具都正确可同时计；CR至少一个工具正确。无调用/parse失败不能从分母删掉。
4. **upstream import有副作用**：部分模块初始化API client或建目录。固定cue离线追加；本包只提取纯prompt/评分逻辑，参考来源只读。
5. **解码版本差异**：上游温度请求0.001被vLLM0.7.3钳制到0.01；该版本默认sampling不自动加载最新版的HF generation-config设置，不可用新版本默认值回推。
6. **Mac后端不同**：不能直接照装CUDA/vLLM0.7.3；本地BF16容量足够。MPS数值/RNG、每请求seed和原论文未知revision差异都已记录。
7. **合盖会暂停**：逐请求持久保存和文件锁支持恢复。此次最终已完成，无需为恢复而新开推理；不要把电脑当前休眠误认为未完成。
8. **smoke/replay不等于独立重复实验**：20条smoke与全量重叠，评分重放也不是第二次模型推理。
9. **截图路径与内容不同**：聊天图可读，但Desktop路径原文件未找到；rubric已忠实转写，未假装包含原图，也未补造被裁切URL、权重或空白格要求。
10. **旧proposal/README可能过时**：proposal写normalizer会在midterm前训练不代表已完成；旧作者“A. Faghih”应为Kazem。当前任务成果不要用旧计划替代。
11. **便携重放用专用脚本**：原runner保留原机绝对路径；不要直接拿它在别的电脑replay。用ZIP内portable脚本，保留`-X utf8`避免Windows编码错误。
12. **Git与认证**：本地真实repo原本有未提交EDA代码和README改动，不reset/clean/覆盖。CLI gh token此前失效，但连接的GitHub工具可用；不要搜集或打印凭据。正常提交即可，不force、不绕过分支保护。

## 8. 当前边界与旧上下文位置
只推进分配给你的Part；无授权不申请远端GPU、不启动训练/新推理、不自动发邮件或消息给队友、不替真人签收、不发布最终课程提交。
本次用户已授权发布本交接材料；对后续review/report修改遵循当前新会话用户授权和repo规则。若本地资料尚未提交，保留现有改动并仅提交自己负责文件。
原电脑项目根目录`/Users/cathybao/Documents/Projects/Team_Project_dl`；Git repo在`repo/intro_dl_Team_Project/`；原run在`runs/baseline-table3-qwen7b-20261020-mps/`；本地包在`private/handoffs/TABLE3_BASELINE_HANDOVER_2026-10-20/`。这些不是新机器上的必需路径。
同步ChatGPT项目的`sources/`只读，不编辑/移动/删除。不要把本地个人路径或原图缺失当成完成本次离线review的阻塞，所需证据已在ZIP中。
