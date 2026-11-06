# Team 12: Project Status and Normalizer Training and Evaluation Plan

Planning snapshot from November 5, 2026. See the [November 6 pilot report](normalizer-pilot/README.md) for completed runs, results, and the revised baseline design.

## 1. Conclusion and current stage

The proposal and final midterm report identify FLAN-T5-small, FLAN-T5-base, and BART-base as candidates for supervised fine-tuning. All three have pretrained checkpoints suitable for a generative tool-description normalizer.

Qwen2.5-7B-Instruct remains frozen as the downstream tool selector. The normalizer rewrites descriptions, Qwen selects tools and generates arguments, and the checker scores the calls.

Start with FLAN-T5-small and validate training, checkpoint reload, generated descriptions, and downstream evaluation. The first milestone is a reproducible checkpoint, results for the four evaluation conditions on independent development tools, and an error analysis. Compare the two larger candidates after this pipeline works.

## 2. Project status

### 2.1 Completed

- The Qwen baseline covered 258 BFCL cases, six cues, and two presentation orders, totaling 3,096 requests. Score replay, technical review, and manual sign-off were recorded.
- The pooled edited-to-original Correct Usage Rate (CUR) ratios ranged from 1.98 to 6.20, describing observed preference differences in the historical experiment.
- The final midterm report was archived locally.

### 2.2 Pending

The reviewed materials do not establish completion of normalizer training, data splitting, training configuration, or full evaluation. Freeze tool-level splits and held-out cues before training, then evaluate functional preservation, downstream correctness, and generalization.

### 2.3 Evidence and limitations

This review used the Drive proposal, meeting notes updated through October 30, and the archived final midterm report. Current remote runs and course submission status were not verified. Tool order and name suffix changed together in the baseline. The 3,096 requests reuse the same source cases. Normalizer effectiveness has yet to be evaluated.

### 2.4 Meeting notes and TA feedback

Week 3 emphasized the full project motivation, gaps in related work, citations, formulas, a pipeline diagram, a generative method, and generalization. The accompanying notes flag the confound between description wording and tool order, and ask for unseen wording, separate metrics, and functional preservation.

The TA notes identify selection ratio, conditional argument correctness, and overall correctness as the three metrics to define explicitly. Functional preservation remains a separate assessment.

## 3. Candidate models and feasibility

| Checkpoint | Role | Interpretation |
|---|---|---|
| `google/flan-t5-small` | First end-to-end run | Validate the data, supervision, and pipeline |
| `google/flan-t5-base` | Within-family size comparison | Check whether a larger model improves generalization and preservation |
| `facebook/bart-base` | Alternative backbone | Fine-tune a denoising-pretrained encoder–decoder on the same rewriting task |

The public checkpoints support sequence-to-sequence modeling. Measure memory, runtime, and output quality in a pilot. Interpret FLAN-T5 versus BART as a backbone comparison, since the models also differ in pretraining and instruction tuning. Begin with supervised fine-tuning and consider knowledge distillation after the primary experiments.

## 4. Before training: task, data, and leakage controls

### 4.1 Task definition

- Input: a tool description containing manipulative wording.
- Output: a normalized description preserving capabilities, argument meanings, and conditions of use.
- Preserve tool names, argument schemas, and underlying functionality. Keep expected calls and arguments in the scorer. The first model outputs the description alone.

### 4.2 Data splits

Group by source tool. Check for duplicates, near-duplicates, and related records before splitting. A 70/15/15 train/dev/test split is a starting point, subject to the number of independent tools and category coverage. Keep all queries, cues, and rewrites for a source tool in one split. Split before augmentation and record source IDs, tool groups, cue types, generation provenance, and split membership.

Reserve separate test slices for unseen tools with seen cue families, unseen tools with unseen cue families, and unseen phrasings or templates of known manipulations. Holding out one sentence from the six closely related assertive cues provides limited evidence about generalization across manipulation strategies.

### 4.3 Supervision and functional preservation

| Pair type | Purpose |
|---|---|
| Manipulated → clean | Remove irrelevant promotion and priority cues |
| Clean → clean | Preserve descriptions that need no changes |
| Description with genuine restrictions → target retaining those restrictions | Preserve argument meanings, units, negations, authorization, and conditions of use |

Start with roughly 25% clean identity pairs and adjust using development results. Review original descriptions before using them as canonical targets. Vary cue wording and insertion position so the model cannot succeed by deleting the final sentence. If another model generates variants, record its generation setup and manually check meaning. Keep test descriptions and test-generated variants out of training.

For example, remove an unsupported claim that the tool is the most effective and should be called first. Preserve restrictions such as USD-only support, required authorization, lack of historical data, and required date formats. Retain the functional basis of legitimate usage guidance.

## 5. Training procedure and starting configuration

| Item | Proposed setting |
|---|---|
| First model | FLAN-T5-small |
| Training | Full supervised fine-tuning |
| Loss | Target token cross-entropy with padding ignored |
| Optimizer | AdamW |
| Learning rate | Start at 5e-5 and compare with 1e-4 on dev if needed |
| Effective batch size | 16, using gradient accumulation as needed |
| Epochs | Up to 10, with dev-based early stopping |
| Length limits | Set using each tokenizer’s observed length distribution and check input and target truncation |
| Decoding | Fixed greedy decoding for the pilot, with a recorded generation limit |
| Seeds | One fixed seed per model initially, expanding to three if resources permit |

The token loss sums −log pθ(yⱼ given y before j and x) over valid target tokens. Here x is the input description, y is the canonical target, and θ denotes the normalizer parameters. Record how the implementation reduces token losses.

1. Overfit 16–32 training examples to verify that the model can learn the target rewrites.
2. Check labels, padding, truncation, formatting, and empty outputs.
3. Train on the full training split and inspect generations for unseen dev tools.
4. Save and reload the checkpoint and verify outputs on fixed examples.
5. Record training and validation losses, configuration, seed, runtime, peak memory, and dataset version.
6. Run the four downstream dev conditions using frozen Qwen settings.

Use dev rewrite quality, preservation, and downstream results alongside loss. Set model-selection criteria and performance tolerances before the final test. Compare FLAN-T5-base and BART-base using the same splits, targets, and evaluation cases, with comparable tuning budgets and their respective tokenizers.

Verify GPU type, memory, allocation, environment, and persistent storage before training. Train the three models sequentially if needed and run Qwen evaluation separately. Save checkpoints to persistent storage rather than relying on temporary storage. Scheduler notifications were discussed but have not been configured.

## 6. Metrics: tool selection and argument correctness

A CUR change can arise from a shift in tool selection, argument correctness, or both. The proposed case-level definitions preserve compatibility with the existing checker. Confirm aggregation and whether the TA expects a stricter overall metric before running the experiment.

Let N be the number of cases in a condition, t a candidate tool, and e and o the edited and original roles. Let Sᵢₜ indicate that case i contains at least one parsed call to t, regardless of arguments. Let Iᵢₜ indicate at least one correct call to t and no incorrect calls to t, following the existing CUR checker. Iᵢₜ implies Sᵢₜ.

| Metric | Definition |
|---|---|
| Selection rate, SRₜ | Sum of Sᵢₜ over cases divided by N |
| Selection ratio | SRₑ / SRₒ |
| Conditional argument correctness, AACₜ | Sum of Iᵢₜ divided by sum of Sᵢₜ |
| Existing CURₜ | Sum of Iᵢₜ divided by N |
| Overall correctness, CR | Fraction of cases with Iᵢₜ = 1 for at least one candidate |

With consistent case-level aggregation and a nonzero selection denominator, CURₜ = SRₜ × AACₜ. AAC measures success for a selected tool within a case. Both tools can be selected or correct within one case, so the selection rates need not sum to one and CR can differ from the sum of CURs.

Mark zero-denominator ratios as undefined. Keep unparseable cases in N and exclude them from conditional denominators where selection cannot be established. Report parse failures, no calls, unknown tool names, and multiple calls separately. Preserve the historical checker and baseline scores. Give any stricter all-calls-valid metric its own name.

Separately report preference shifts relative to clean inputs, preservation and over-deletion or invention rates, and changes in CR on clean inputs. Use paired comparisons and, where feasible, bootstrap intervals clustered by source tool.

## 7. Downstream experiment

| Condition | Purpose |
|---|---|
| Clean | Reference behavior without manipulative wording |
| Manipulated | Baseline without a defense |
| Manipulated → normalizer | Measure the defense |
| Clean → normalizer | Measure effects on clean inputs |

Match cases, Qwen checkpoint, prompt, decoding, and checker across conditions. If the backend changes, collect matched controls on the new backend before attributing changes to normalization.

Keep edited-only rewriting as a diagnostic. Also evaluate normalizing all candidate descriptions, which reflects deployment when the edited tool is unknown. Match clean controls to each policy and report the policies separately.

Add a clean-vs-clean control to measure existing name and position preferences. Swap position while fixing tool-name assignments. If resources permit, counterbalance names independently and compare description condition, position, and name assignment. Report each order as well as pooled results.

Include a rule-based baseline that removes known cues. Judge success by movement toward clean selection behavior, CR and clean-input performance within predefined tolerances, and retention of important functional constraints. Compare these jointly when interpreting a smaller CUR gap.

## 8. Generalization and error analysis

| Test | Design |
|---|---|
| Unseen wording | Hold out new phrasings or templates of known manipulations |
| Unseen cue family | Exclude an entire manipulation strategy from training and tuning |
| Unseen tool or domain | Hold out a tool category or scenario, such as stock lookup |

Report the three tests separately. Freeze model selection before the final test.

Cross-tabulate rewrite failures with downstream failures. Check for intended tool selection with wrong arguments, residual persuasion and preference shift, deleted constraints or units, invented capabilities, harm to clean inputs, and empty, malformed, truncated, or unparseable outputs. Compare by cue, order, name, tool group, and backbone. Retain original descriptions, rewrites, and downstream results for representative successes and failures.

The Week 3 slide mentions “audit and description” order. The accompanying notes clarify the actionable concern as description wording changing together with tool position. The experiment varies these factors independently. Functional preservation remains part of offline evaluation.

## 9. Report, video, and presentation

- Cover both measurement and mitigation in the motivation. Explain the specific research gap in related work.
- Cite model, dataset, and protocol provenance with linked in-text references.
- Define variables, loss, metrics, denominators, configurations, seeds, and uncertainty analysis.
- Draw the actual pipeline and encoder–decoder training path. Route expected calls only to the scorer and distinguish completed experiments from planned work.
- Include training curves, matched comparison tables, generalization results, representative errors, limitations, and future work.

The supplied notes record a five-minute video due December 5 at 6 p.m., roughly 80% project completion by that point, peer review, and a final report the following week. Confirm the date, time zone, and requirements against the official course notice.

## 10. Review questions

1. Is FLAN-T5-small first, followed by the two comparison models, the desired order?
2. How should multi-call outputs, parse failures, and overall correctness be scored?
3. Which cue families and tool categories should be held out entirely?
4. What GPU allocation, persistent storage, budget, and owners are available?
6. What drop in CR or clean-input performance is acceptable, and how will that tolerance be fixed before testing?


## 11. Sources

- Team 12 Weekly Meeting Logs, IDL Project Proposal, and the final midterm report.
- TA feedback screenshots supplied for the planning review.
- [FLAN-T5-small model card](https://huggingface.co/google/flan-t5-small)
- [FLAN-T5-base model card](https://huggingface.co/google/flan-t5-base)
- [BART-base model card](https://huggingface.co/facebook/bart-base)
- [Hugging Face sequence-to-sequence fine-tuning example](https://huggingface.co/docs/transformers/tasks/summarization)
