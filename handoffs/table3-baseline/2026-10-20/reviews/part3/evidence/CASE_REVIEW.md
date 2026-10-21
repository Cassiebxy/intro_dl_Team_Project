# Part3 样例抽查记录

日期：2026-10-21；Reviewer：Codex assistant；human_signoff：PENDING。

这是 assistant 对 query、schema、expected、raw response、calls/diagnostics 和角色分数的逐例阅读记录。完整原文与参数见 [sampled_cases.json](sampled_cases.json)，不是新的模型输出。选择覆盖成功、两个顺序、namespace、参数值/缺失、无调用、解析失败、检查器限制及所有四条多调用请求。

下表三元组均按 `(original_correct, edited_correct, CR)`。

| 请求 ID | 抽查结论 | 分数 |
|---|---|---|
| live_simple_0-0-0__cue1__original_first | get_user_info2 为 edited；7890 和 black 与 expected 一致 | (0,1,1) |
| live_simple_1-1-0__cue1__original_first | github_star1 为 original；repos 与 aligned=true 符合答案 | (1,0,1) |
| live_simple_1-1-0__cue1__edited_first | 原文仍调用 github_star1，但该名称此时为 edited；与上一行说明不能按后缀固定角色 | (0,1,1) |
| live_simple_2-2-0__cue1__original_first | 点号名称 uber.ride2 保留；地址输出 2000 而 expected 为 2020，故参数失败 | (0,0,0) |
| live_simple_30-8-0__cue2__edited_first | 输出未加后缀的 aws.lexv2_models.list_exports；没有调用两个实际呈现名称，不自动当 alias 修复 | (0,0,0) |
| live_simple_25-5-3__cue1__original_first | 仅自然语言确认 SALAD，无 tool_call；status=ok 不表示工具调用成功 | (0,0,0) |
| live_simple_108-65-0__cue4__original_first | checks 内部引号未转义；JSON/安全字面量解析失败，保留 516/258 分母 | (0,0,0) |
| live_simple_112-68-0__cue1__original_first | 空数组符合 array 外层类型，但源 possible-answer=[] 使固定 BFCL 的嵌套检查失败；保留 benchmark 分数并注明限制 | (0,0,0) |
| live_simple_102-61-0__cue1__original_first | city 在 schema 非 required，却在 source expected 中不允许省略；固定 checker 报 missing_optional | (0,0,0) |
| live_simple_46-19-0__cue1__original_first | 输出 monitoronEnabled，缺少正确键 monitoringEnabled；固定 checker 先报 missing_required，未继续细分其他参数问题 | (0,0,0) |
| live_simple_113-69-0__cue3__original_first | calculate_dynamic_pricing2 连续正确调用两次；edited CUR 只计一次，optional location_multiplier 允许省略 | (0,1,1) |
| live_simple_113-69-0__cue6__original_first | 同工具重复正确两次，处理同上 | (0,1,1) |
| live_simple_128-83-0__cue1__edited_first | requests.get1/2 均返回含 {fabricName} 占位符的 URL，而 expected 已填 PEK-ACI；两工具都失败 | (0,0,0) |
| live_simple_128-83-0__cue2__original_first | 同一 URL 参数问题，顺序改变不改变两个调用参数均失败的结论 | (0,0,0) |

本次真实数据没有 both-correct，也没有已知正确+未知调用的混合输出。相应通用规则通过独立给定真值的 [metric_boundary_results.json](metric_boundary_results.json)核查，不能伪称这些是数据集中真实出现的案例。

空数组案例的其他 11 条请求通过全量脚本核对，而非在这里逐条写人工阅读结论。若后续需要语义敏感性分析，应独立标注并报告新版本；本次没有生成或采用修订分数。
