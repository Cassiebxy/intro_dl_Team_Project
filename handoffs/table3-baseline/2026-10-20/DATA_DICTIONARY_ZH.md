> GitHub阅读层：先读[新会话总交接](HANDOVER_NEW_SESSION_ZH.md)。完整原始证据、代码和便携重放脚本在同目录ZIP；下文重放命令均在解压后的包根目录执行。ZIP保留原准备时说明，当前发布状态以本目录README和reviews为准。

# 文件与字段说明

| 文件 | 用途/单位 |
|---|---|
| tables/per_case_scores.csv | 3096行，逐请求；布尔分数为0/1，case_id是原258案例ID，id另含cue/order |
| tables/paper_vs_local_table3.csv | 六行；*_pct单位0–100%，*_pp为本地减论文的百分点；ratio无单位；含整数分子 |
| tables/order_effects.csv | 六行，每行两个顺序，各N258；ratio空白为undefined |
| evidence/run_snapshot/full/results_by_order.csv | 十二行，原始运行导出；CUR/CR使用0–1比例 |
| evidence/run_snapshot/full/baseline_table3_results.csv | 六行原始导出，CUR/CR使用0–1比例 |
| evidence/run_snapshot/full/scores.jsonl | 每请求完整calls、diagnostics、角色正确性及score.status |
| evidence/run_snapshot/full/raw_responses.jsonl | 模型原文、生成token IDs、seed、耗时、attempt、finish_reason；raw status=ok表示生成成功，非正确率 |
| evidence/run_snapshot/requests.jsonl | 冻结query、双工具schema、roles、expected、cue_id/order、token数及上限 |
| evidence/run_snapshot/expected.jsonl | 按呈现名称映射的ground_truth/roles；ground_truth参数值是BFCL允许答案列表，不是直接执行参数 |
| evidence/run_snapshot/prompts.jsonl | 当时实际输入字符串及SHA256；不再次apply chat_template |
| evidence/run_snapshot/full/attempts.jsonl | started/ok事件及成功response；同一attempt有多个事件，不能把事件行数当调用次数 |
| tables/response_failure_counts.csv | 请求级互斥分类，合计3096；含成功类 |
| tables/call_diagnostic_counts.csv | 调用级诊断，多个调用可能来自一个请求；valid_call仅代表那次调用正确 |
| evidence/run_snapshot/protocol.json | 原运行来源、输入与模型metadata哈希、revision、解码及差异；绝对路径仅供原机provenance |
| MANIFEST.json | 本包固定文件的SHA256；不包含自身和validation动态重放输出 |

original_correct/edited_correct按语义角色计，不等同于工具位置1/2。CR至少一工具正确；全量仍N3096，每cue516。
elapsed_seconds为单请求生成所测时间，可能包含运行环境调度或睡眠影响；其总和/平均不能保证等于全天墙钟时长。smoke与full重叠，不能累加成3116个独立测试。

本包没有权重、虚拟环境、凭据或新训练数据；包含原始实验query/输出、代码和裁剪的官方参考副本，上传前由用户决定发布范围。code/original_tests保留原测试源码作为证据，内含原机路径；便携入口仅scripts/verify_and_replay.py。
