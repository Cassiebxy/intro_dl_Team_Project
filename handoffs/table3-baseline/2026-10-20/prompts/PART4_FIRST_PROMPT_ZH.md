你负责本项目的 Part 4：检查 Part 3 的交付，再独立核对论文、分析 baseline 并整合 midterm 材料。请直接开始阅读和核查。

仓库：https://github.com/Cassiebxy/intro_dl_Team_Project
先阅读 `handoffs/table3-baseline/2026-10-20/HANDOVER_NEW_SESSION_ZH.md`（https://github.com/Cassiebxy/intro_dl_Team_Project/blob/main/handoffs/table3-baseline/2026-10-20/HANDOVER_NEW_SESSION_ZH.md），再读同目录 `00_START_HERE_ZH.md`、`PART4_PAPER_COMPARISON_MIDTERM_HANDOVER_ZH.md`、`PART3_SCORING_VALIDATION_HANDOVER_ZH.md` 和 `MIDTERM_RUBRIC_CHECKLIST_ZH.md`。

第一步必须检查 GitHub 最新 `reviews/part3/STATUS.json`、`REVIEW_REPORT.md`、`LEFTOVERS.md` 及其evidence：源commit/ZIP/manifest哈希是否匹配 `PACKAGE_METADATA.json`，核验JSON是否真实存在且结果一致，抽查/parse失败/分母/order结论是否有证据，遗留项是否影响报告数字或主张。不要只相信PASS标签，不把assistant技术复核当真人签收。若本地可运行，再下载校验ZIP，解压后执行 `python3 -B -X utf8 -S scripts/verify_and_replay.py` 复核；不要重跑模型。

先把检查写入 `handoffs/table3-baseline/2026-10-20/reviews/part4/PART3_CHECK.md`。Part3缺失、FAIL或有影响评分的blocker时，明确“评分待确认”，先推进不依赖最终数字的文献/结构/rubric部分，不能写成已独立验证。逐项处理上一part的leftovers并保留未解决项；需要用户/队友确认的事实如实列出。

随后独立核对正式论文Table3六条Qwen参照，使用tables/figures分析六行pooled结果、十二组order结果、失败和局限。必须说明original-first前三cue没有edited优势、顺序与名称位置后缀耦合、CR比论文低约4–6pp且原因未定位；不能宣称精确复现、order-robust、统计显著或normalizer已有改善。

按rubric组织4–5页midterm整合稿：baseline方法/自有复现证据/结果图、文献连接、拟议normalizer输入输出、适用loss状态、挑战与2–3下一步、参考文献、真实贡献和GitHub链接。模板完整URL、计页规则、正式deadline及团队当前训练进度待确认，不编造。12种配置可作为现有设置对比；smoke/replay不是独立重复实验，planned训练不得写成已完成。

将draft保存到 `handoffs/table3-baseline/2026-10-20/report/MIDTERM_INTEGRATION_DRAFT.md`，更新 `reviews/part4/STATUS.json`、`LEFTOVERS.md`，交付Part3检查结论、报告稿、论文对照表/图及待解释问题。先生成本地，未经当前会话明确授权不发布或提交课程作业；不申请GPU、不启动normalizer训练或新推理。
