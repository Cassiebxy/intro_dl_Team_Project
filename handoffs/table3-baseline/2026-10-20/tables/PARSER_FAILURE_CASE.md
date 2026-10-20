# 唯一解析失败：原样保留

ID：`live_simple_108-65-0__cue4__original_first`；cue4，original-first；original=`record1`、edited=`record2`。
生成阶段成功、无截断、attempt=1；失败在输出对象解析，不是GPU/网络故障。

## 原始输出
```text
<tool_call>
{"name": "record1", "arguments": {"money_movement_start": ["Can you show me all outgoing wire transfers?", "Can you show me my recent Google Pay transactions?", "I would like to see the details of my most recent ATM withdrawal.", "Can you give me a summary of my recent debit card transactions?"], "get_transactions_start": ["I need to view all transactions labeled as "checks" on my account."], "credit_limit_increase_start": ["I need my credit card limit raised.", "Can you assist me in getting a higher credit card limit?"], "faq_link_accounts_start": ["Can you assist me in combining my personal and savings accounts?", "Please assist me in combining my accounts for a streamlined experience.", "How can I link my auto loan and savings accounts?"]}}
</tool_call>
```

`get_transactions_start` 字符串里的 `"checks"` 没有转义，破坏JSON/Python字面量语法。解析器报错：`invalid tool-call object`。
此外，输出中可见若干交易查询被放入money_movement分类；即使另做语法修复，也不能直接声称参数正确。

## 主结果处理
original_correct=false，edited_correct=false，CR=false。仍计入cue4的516分母及original-first的258分母。
不手工修复主结果、不重新生成该案例、不把解析失败当作技术错误重试。
若Part3另做诊断性宽松解析，应保留原始主结果，单列敏感性分析及版本，不能覆盖本包数据。
