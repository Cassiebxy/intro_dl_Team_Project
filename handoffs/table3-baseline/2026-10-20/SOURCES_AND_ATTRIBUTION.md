> GitHub阅读层：先读[新会话总交接](HANDOVER_NEW_SESSION_ZH.md)。完整原始证据、代码和便携重放脚本在同目录ZIP；下文重放命令均在解压后的包根目录执行。ZIP保留原准备时说明，当前发布状态以本目录README和reviews为准。

# 来源与证据范围

- 论文正式版本：[ACL Anthology](https://aclanthology.org/2025.emnlp-main.1060/)，[PDF](https://aclanthology.org/2025.emnlp-main.1060.pdf)；核对Table3六条Qwen参照，PDF第3页/印刷20956。
- 固定官方代码：[kazemf78/llm-unreliable-tool-preferences](https://github.com/kazemf78/llm-unreliable-tool-preferences/tree/05be5f136f00fe66acf0aa853d7bcd44c300946c)。reference_upstream仅为本地审核/重放复制所需来源，保留原内容及路径；不是我们的原创代码。该checkout未找到顶层LICENSE文件；pyproject元数据的license声明不等于本包新增发布许可，后续公开前需决定分发方式。
- 模型：[官方Qwen2.5-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/tree/a09a35458c702b33eeacc393d103063234e8bc28)；模型权重不随包分发，校验manifest随包。
- temperature行为：[vLLM0.7.3 sampling_params.py](https://github.com/vllm-project/vllm/blob/v0.7.3/vllm/sampling_params.py)，正温度低于0.01钳制到0.01；[arg_utils.py](https://github.com/vllm-project/vllm/blob/v0.7.3/vllm/engine/arg_utils.py)对应版本默认generation_config=None；不可照最新版本默认值回推。
- [BFCL官方介绍](https://gorilla.cs.berkeley.edu/blogs/8_berkeley_function_calling_leaderboard.html)：数据/参数正确性背景；[ToolTweak](https://arxiv.org/abs/2510.02554)：名字/描述操纵及paraphrasing防御相关工作。均于2026-10-20核对主要元数据。
- rubric来源仅为用户在聊天中提供的三张可见截图，文件名及本地原件未找到的情况见evidence/rubric/SOURCE_NOTE.md；没有访问完整在线评分表，无法确认截图外字段或被裁切的template URL。
- 本地既有proposal提供拟议normalizer方向，不代表那些模型已训练或旧贡献文字仍有效。原proposal中的“A. Faghih”应更正为官方“Kazem Faghih”。
- 本包自身分析以run_snapshot中的真实响应与score为依据，自动计算和队友人工独立签收分开。没有新推理、训练或API模型调用；当前GitHub发布已获用户授权。
