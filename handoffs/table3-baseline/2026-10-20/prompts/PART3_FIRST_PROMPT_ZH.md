你负责本项目的 Part 3：Table 3 baseline 的独立评分与验证。请直接开始核查，不重新训练或运行模型。

仓库：https://github.com/Cassiebxy/intro_dl_Team_Project
先阅读 `handoffs/table3-baseline/2026-10-20/HANDOVER_NEW_SESSION_ZH.md`（https://github.com/Cassiebxy/intro_dl_Team_Project/blob/main/handoffs/table3-baseline/2026-10-20/HANDOVER_NEW_SESSION_ZH.md），再读同目录 `00_START_HERE_ZH.md`、`PART3_SCORING_VALIDATION_HANDOVER_ZH.md` 和 `DATA_DICTIONARY_ZH.md`。

首先从 GitHub 最新版本读取 `reviews/part3/STATUS.json`、`REVIEW_REPORT.md`、`LEFTOVERS.md`，判断上一位是否已有进展；不要覆盖或重复已完成工作。已有自动评分不等于你已完成独立复核。

按 `PACKAGE_METADATA.json` 下载同目录完整ZIP，核对ZIP/内MANIFEST的SHA256，解压到单独工作目录。进入解压包根目录运行 `python3 -B -X utf8 -S scripts/verify_and_replay.py`（Windows可用python）；无需下载权重、pip装torch或调用模型。

独立检查3096唯一请求、6×516/12×258分母、original/edited角色随顺序变化、CUR/CR与BFCL参数检查、重复调用边界、phantom/alias与模型未知工具区别，以及唯一parse失败保留分母。结合raw response手工抽查并记录case IDs。对照逐例score、summary和强顺序不对称，不能只看总体六行。

把你自己的核验JSON和环境证据保存到 `handoffs/table3-baseline/2026-10-20/reviews/part3/evidence/`，完善 `REVIEW_REPORT.md`、`STATUS.json` 和 `LEFTOVERS.md`。记录源commit/ZIP/manifest哈希、抽查结论、是否改分数、blocking/nonblocking遗留项及对Part4的影响；reviewer_type如实写assistant或human，不代替真人签收。原ZIP和原始结果保持不变，若需改分数就输出新版本与完整差异。

先完成本地审核与交接文件；只在当前会话有发布授权时更新GitHub，不能force push。结束时告诉我验证通过哪些、仍卡在哪里、Part4能否使用哪一版分数，以及它首先应读哪个leftover。只推进Part3，不申请GPU、不启动新推理/训练，也不自动推进Part4。
