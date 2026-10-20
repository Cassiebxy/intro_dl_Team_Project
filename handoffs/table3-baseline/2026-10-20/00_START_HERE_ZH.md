# Table 3 baseline交接入口

本目录已获用户授权发布。**先读[零上下文总交接](HANDOVER_NEW_SESSION_ZH.md)，然后Part3复核，Part4检查Part3并整合midterm。**

1. [Part3：评分与验证交接](PART3_SCORING_VALIDATION_HANDOVER_ZH.md)
2. [Part4：论文对照与midterm交接](PART4_PAPER_COMPARISON_MIDTERM_HANDOVER_ZH.md)
3. [评分标准清单](MIDTERM_RUBRIC_CHECKLIST_ZH.md)
4. [Part3启动prompt](prompts/PART3_FIRST_PROMPT_ZH.md) / [Part4启动prompt](prompts/PART4_FIRST_PROMPT_ZH.md)
5. [Part3当前状态](reviews/part3/STATUS.json) / [Part3遗留项](reviews/part3/LEFTOVERS.md)
6. [Part4当前状态](reviews/part4/STATUS.json) / [Part4遗留项](reviews/part4/LEFTOVERS.md)

当前：3096次真实推理及自动评分完成；0技术错误、0截断、1解析失败保留分母。Part3独立技术复核、人工签收和midterm最终整合尚未完成。

**完整证据：[下载ZIP](TABLE3_BASELINE_HANDOVER_2026-10-20.zip)**（GitHub文件页点击Download raw），或使用[直接下载链接](https://raw.githubusercontent.com/Cassiebxy/intro_dl_Team_Project/main/handoffs/table3-baseline/2026-10-20/TABLE3_BASELINE_HANDOVER_2026-10-20.zip)。约4.4MB压缩后，内含约38MB文件，不含模型权重/虚拟环境/凭据。
先用[PACKAGE_METADATA.json](PACKAGE_METADATA.json)核对ZIP SHA256，再解压；之后运行内置脚本，不需要模型、网络或pip安装。

GitHub直接可读的tables/figures与ZIP内文件相同；GitHub阅读层的交接文加了发布/接手说明，不能拿它们替换ZIP内部文件后再要求原MANIFEST通过。保持ZIP证据不变，新的复核产物写入reviews/。
