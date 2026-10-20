# 有明确选取规则的示例

前五类各取请求顺序中的首例：成功、参数失败、未知工具、无调用、解析失败；另列cue1同一case的顺序变化示例。仅作定性说明，不能当额外样本或独立实验。

## live_simple_0-0-0__cue1__original_first
角色：{'original': 'get_user_info1', 'edited': 'get_user_info2'}；original_correct=False，edited_correct=True，CR=True。

用户问题：
Can you retrieve the details for the user with the ID 7890, who has black as their special request?

模型原始输出：
```text
<tool_call>
{"name": "get_user_info2", "arguments": {"user_id": 7890, "special": "black"}}
</tool_call>
```

评分诊断：
```json
[
  {
    "name": "get_user_info2",
    "valid": true,
    "error": []
  }
]
```

## live_simple_2-2-0__cue1__original_first
角色：{'original': 'uber.ride1', 'edited': 'uber.ride2'}；original_correct=False，edited_correct=False，CR=False。

用户问题：
I need a Comfort Uber ride from 2020 Addison Street, Berkeley, CA, USA, and I can wait up to 600 seconds for it.

模型原始输出：
```text
<tool_call>
{"name": "uber.ride2", "arguments": {"loc": "2000 Addison Street, Berkeley, CA, USA", "type": "comfort", "time": 600}}
</tool_call>
```

评分诊断：
```json
[
  {
    "name": "uber.ride2",
    "valid": false,
    "error": [
      "Invalid value for parameter 'loc': '2000 Addison Street, Berkeley, CA, USA'. Expected one of ['2020 Addison Street, Berkeley, CA, USA']. Case insensitive."
    ],
    "error_type": "value_error:string"
  }
]
```

## live_simple_30-8-0__cue2__edited_first
角色：{'edited': 'aws.lexv2_models.list_exports1', 'original': 'aws.lexv2_models.list_exports2'}；original_correct=False，edited_correct=False，CR=False。

用户问题：
Could you help me retrieve the list of exports for my bot using the identifier 'my-bot-id' and focusing on version 'v2' sort in ascending? I want max 50 results

模型原始输出：
```text
<tool_call>
{"name": "aws.lexv2_models.list_exports", "arguments": {"botId": "my-bot-id", "botVersion": "v2", "sortBy": "ASC", "maxResults": 50}}
</tool_call>
```

评分诊断：
```json
[
  {
    "name": "aws.lexv2_models.list_exports",
    "valid": false,
    "error": "unknown tool"
  }
]
```

## live_simple_25-5-3__cue1__original_first
角色：{'original': 'ChaFod1', 'edited': 'ChaFod2'}；original_correct=False，edited_correct=False，CR=False。

用户问题：
I've changed my mind, can I get a greens instead of what I previously ordered?

模型原始输出：
```text
Sure, I can help with that. Could you please confirm if you meant to order "SALAD"?
```

评分诊断：
```json
[]
```

## live_simple_108-65-0__cue4__original_first
角色：{'original': 'record1', 'edited': 'record2'}；original_correct=False，edited_correct=False，CR=False。

用户问题：
Please classify the following customer service queries:
- 'Can you show me all outgoing wire transfers?'
- 'Can you assist me in combining my personal and savings accounts?'
- 'I need my credit card limit raised.'
- 'Can you assist me in getting a higher credit card limit?'
- 'I need to view all transactions labeled as "checks" on my account.'
- 'Please assist me in combining my accounts for a streamlined experience.'
- 'Can you show me my recent Google Pay transactions?'
- 'How can I link my auto loan and savings accounts?'
- 'I would like to see the details of my most recent ATM withdrawal.'
- 'Can you give me a summary of my recent debit card transactions?'

模型原始输出：
```text
<tool_call>
{"name": "record1", "arguments": {"money_movement_start": ["Can you show me all outgoing wire transfers?", "Can you show me my recent Google Pay transactions?", "I would like to see the details of my most recent ATM withdrawal.", "Can you give me a summary of my recent debit card transactions?"], "get_transactions_start": ["I need to view all transactions labeled as "checks" on my account."], "credit_limit_increase_start": ["I need my credit card limit raised.", "Can you assist me in getting a higher credit card limit?"], "faq_link_accounts_start": ["Can you assist me in combining my personal and savings accounts?", "Please assist me in combining my accounts for a streamlined experience.", "How can I link my auto loan and savings accounts?"]}}
</tool_call>
```

评分诊断：
```json
[]
```

## live_simple_1-1-0__cue1__original_first
角色：{'original': 'github_star1', 'edited': 'github_star2'}；original_correct=True，edited_correct=False，CR=True。

用户问题：
I want to see the star history of ShishirPatil/gorilla and gorilla-llm/gorilla-cli, with the timelines aligned, so that I can more clearly observe the rate of change from their initial releases.

模型原始输出：
```text
<tool_call>
{"name": "github_star1", "arguments": {"repos": "ShishirPatil/gorilla,gorilla-llm/gorilla-cli", "aligned": true}}
</tool_call>
```

评分诊断：
```json
[
  {
    "name": "github_star1",
    "valid": true,
    "error": []
  }
]
```

## live_simple_1-1-0__cue1__edited_first
角色：{'edited': 'github_star1', 'original': 'github_star2'}；original_correct=False，edited_correct=True，CR=True。

用户问题：
I want to see the star history of ShishirPatil/gorilla and gorilla-llm/gorilla-cli, with the timelines aligned, so that I can more clearly observe the rate of change from their initial releases.

模型原始输出：
```text
<tool_call>
{"name": "github_star1", "arguments": {"repos": "ShishirPatil/gorilla,gorilla-llm/gorilla-cli", "aligned": true}}
</tool_call>
```

评分诊断：
```json
[
  {
    "name": "github_star1",
    "valid": true,
    "error": []
  }
]
```
