# 图注（按需放入midterm）

## paper_vs_local_CUR
中文：Qwen2.5-7B的Table3复现，六条assertive cue在两个工具顺序上合并（每条N516）。灰色为论文参照，蓝色为本地真实运行。两面板分别显示edited与original工具的CUR；后端和随机过程不同，未画置信区间，不代表统计等价。
English: Table 3 reproduction for Qwen2.5-7B, pooled over both presentation orders (N=516 per cue). Gray bars show published reference values and teal bars show our local run. Panels report edited- and original-tool CUR separately. Backend and sampling differences remain; no uncertainty intervals are shown.

## order_effects
中文：将本地CUR按工具展示顺序拆分（每条cue/order N258）。edited-first时original CUR近零，original-first前三条cue没有edited优势。展示顺序和名称位置后缀同时变化，不能单独识别纯位置因果效应。
English: Local CUR by presentation order (N=258 per cue/order). Original-tool CUR is nearly zero when the edited tool is presented first, whereas the first three cues do not favor the edited tool in the original-first condition. Presentation position and name suffix are coupled; these panels do not isolate a pure position effect.

两图均用tables中的完整精度数据生成。PDF为矢量图；PNG适合预览。cue全文在Part3文档，避免在图中堆叠长句。
