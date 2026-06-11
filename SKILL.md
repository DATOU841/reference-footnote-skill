---
name: 参考文献补注
description: Use for ReferenceFootnote workflows on already-written academic articles when the task is to diagnose citation needs, reverse-lookup supporting literature in a RAG platform, form search-intake handoffs for unsupported claims, plan footnote/reference insertions, and build citation QA delivery packages. Do not use for writing articles from scratch, real CNKI/WoS/Zotero/PDF/RAG operations, or general polishing.
---

# 参考文献补注 Skill

版本：0.6.0-dev

## 文衡原生协议

正式补注、citation QA、RAG 反查或检索入库交接任务启动前必须先进入文衡 B02，由主仓 `/api/tasks` 创建或绑定 `reference_footnote` 任务，取得 `wenheng_task_id`、标准 task folder、F06 routing decision 和 H08 evidence stub。缺少 `wenheng_task_id`、task folder 或 routing decision 时，本 skill 只能生成 `wenheng-intake-request`，列明已有文章状态、需要的脱敏材料摘要、是否已有 RAG 库和建议 routing；不得进入 S00 正式 workflow，不得读取真实全文或 RAG 数据。

启动前必须读取 F06 routing decision，确认目标通道未 forbidden；涉及注释措辞、正文契合性、审查意见表述时，还必须读取 G07 active rules。若阶段仅为证据检索、RAG 反查或结构化补库交接，G07 可判定不适用，但必须在 evidence / handoff 写明 `style_memory_not_applicable_reason`。

每次 evidence / handoff 必须包含：

- `style_memory_source`
- `style_memory_rules_applied`
- `style_memory_rules_ignored`
- `style_memory_conflicts`
- `style_memory_not_applicable_reason`
- `style_memory_feedback_candidate_id`

S00-S120 关键节点必须回写 B02 timeline，S40/S45/S50/S65/S120 必须写 E05/B02/H08 脱敏状态。失败必须进入 H08 error review；完成必须进入文衡 archive package。用户反馈、审查意见、风险清理经验和交付复盘只进入 G07 feedback candidate，不得自动晋升 active rule。

文衡协议细节见 `docs/wenheng-native-protocol.md`；handoff 字段见 `templates/wenheng-handoff-schema.json`。

## 硬边界

- 只面向已经写好的文章，不从零写论文。
- 不替代 `正文写作`，不执行正式正文生产链；但本 skill 可独立调用“写作池式审查”能力，用于注释位置、注释措辞、正文契合性和论证强度复核。
- 不直接运行 CNKI、WoS、Zotero、PDF 获取或 RAG 导库；2.5 导库完成后的 RAG 反查在本版本默认只允许 mock/readiness 形态，live executor 需另行授权、证据与 Review。
- 不读取或操作 `openclaw-cnki-takeover`。
- 不探测 `localhost:22`。
- 不运行 advance-pool、mimo。
- 写作池能力只允许在 ReferenceFootnote 自有阶段中使用：不得依赖 `正文写作` skill 的 `03-writer`、guard、ledger 或服务器正式第三步状态；不得借写作池从零写正文。
- 不使用正式文章任务目录作为测试场。
- 真实检索和入库只能通过结构化请求交给 `检索入库`。
- 对没有已声明可用 RAG 文献库的文章，必须先反推检索蓝图并交给 `检索入库` 建设初始文献库；不得在无库状态编造参考文献。
- RAG 命中不能直接当成可靠引用，必须经过证据解释和风险门禁。

## 工作流

1. S00 启动和边界检查：运行 `scripts/startup.py`，确认离线模式和目录结构。
2. S10 文章导入：用 `scripts/article-intake.py` 生成 `article-structure.json`。
3. S20 Claim / citation need：用 `scripts/claim-segmentation.py` 和 `scripts/citation-need-diagnosis.py` 生成 `claim-segments.json`、`citation-needs.json`。
4. S30 检索蓝图：用 `scripts/build-search-blueprint.py` 从全文反推研究方向、关键词、来源类型和文献池质量要求。
5. S40 检索入库交接：用 `scripts/build-initial-search-handoff.py` 与 `scripts/build-search-intake-call.py` 生成调用包。
6. S45 入库完成和质量验收：用 `scripts/apply-intake-completion.py`、`scripts/validate-intake-quality.py` 记录和验收文献库。
7. S50 逐段/逐句 RAG 反查：S50a 用 `scripts/build-rag-request.py` 生成请求；S50b 用 `scripts/run-rag-reverse-lookup.py` 在 mock/readiness 模式写入 `state/rag-calls/<batch>.response.json`；S50c 用 `scripts/validate-rag-response.py` 解释证据。live executor 缺配置时阻断为 `missing_rag_executor_config`，不得要求用户手工提供回执，也不得把 mock 证据写成 production RAG。
8. S55 grounding 解析：用 `scripts/resolve-grounding.py` 将 RAG chunk 映射到 MinerU/MU Markdown、parsed text、page map 或 PDF fallback 状态。
9. S60 evidence trace ledger：用 `scripts/build-evidence-trace-ledger.py` 建立按全文顺序的证据主线。
10. S65 证据地图和缺口交接：用 `scripts/build-evidence-map.py`、`scripts/build-search-handoff.py`、`scripts/build-search-intake-call.py` 生成二轮补库请求。
11. S66-S68 脚注思考层：
    - S66 用 `scripts/build-footnote-thinking-request.py` 从全文顺序 evidence trace、正文上下文、RAG chunk 和 grounding 摘要生成逐条脚注意图请求；
    - S67 用 `scripts/run-footnote-thinking-pool.py` 导入或执行推进池式脚注构思；无 mock 或外部结果时阻断为 `thinking_pool_not_configured`；
    - S68 用 `scripts/validate-footnote-thinking-result.py` 验证脚注意图，分流为 `validated_footnotes`、`validated_references`、`rewrite_needed`、`human_review`、`no_note`、`rejected`。
12. S70 注释/参考文献规划：
    - S70a 用 `scripts/build-footnote-candidate-pool.py` 生成脚注候选池；该脚本只消费 S68 validated thinking 结果，不得从 evidence-map 直接生成脚注；
    - S70b 同时生成 `reference-candidate-pool.json`，接收 thinking 的 `reference_only` 决策和 evidence-map 中的有效参考文献基础池；
    - S70c 用 `scripts/prune-footnotes.py` 裁剪脚注候选，prune 只作为安全网，不得承担主要清理职责；
    - S70d 用 `scripts/plan-footnotes.py` 生成 `insertion-plan.json`。
13. S80 独立写作池式审查：用 `scripts/build-writing-pool-review-request.py`、`scripts/apply-writing-pool-review-result.py`、`scripts/validate-writing-pool-review.py` 复核位置、措辞和正文契合性。
14. S85 风险清单：用 `scripts/build-risk-inventory.py` 输出高风险点。
15. S90 风险清理：用 `scripts/build-risk-cleanup-plan.py`、`scripts/apply-risk-cleanup-result.py` 清理风险。
16. S95 清理后重建：用 `scripts/rebuild-cleaned-artifacts.py` 生成清理后的 citation needs、注释计划、参考文献和补库需求。
17. S100 完整全文插入：用 `scripts/insert-full-text.py` 生成插入注释和参考文献的完整 Markdown。
18. S105 全文顺序核查：用 `scripts/export-full-order-audit.py` 输出全文顺序逐条核查清单。
19. S110 最终 gate：用 `scripts/validate-final-delivery-gate.py` 阻断未清理风险、未闭合写作池要求、未消费文献等问题。
20. S120 交付包：用 `scripts/build-delivery.py` 输出收束后的交付包；过程材料进入 `delivery/process/`。

## 何时读取参考文件

- 需要阶段机细节时读 `docs/state-machine.md`。
- 需要 RAG 反查请求/响应格式时读 `docs/rag-protocol.md`。
- 需要执行 2.5 后 RAG 反查时读 `config/rag-executor.yaml`，默认 mock；live 模式必须有单独授权、密钥边界、证据和 Review。
- 需要与 `检索入库` 交接时读 `docs/handoff-protocol.md`。
- 需要独立调用写作池审查注释位置和措辞时读 `docs/writing-pool-review-protocol.md`。
- 需要理解检索入库调用包和补库后二轮 RAG 调用时读 `docs/collaboration-flow.md`。
- 需要判断证据强度和风险时读 `docs/evidence-classification.md`。
- 需要处理 RAG chunk、Markdown/parsed text、page map 和 PDF fallback 时读 `docs/grounding-protocol.md`。
- 需要发布或部署边界时读 `docs/quality-gates.md` 和 `docs/boundary-rules.md`。

## Claude 规划/审查交接规则

- 每次需要 Claude 规划、审查或复核时，Codex 必须直接在对话窗口给用户一份可复制的完整提示词。
- 提示词必须明确写入位置，使用句式：`你有写入权限，请将结果写入：<绝对路径>`。
- 提示词必须要求 Claude 完成后只回复：是否已写入、文件路径、结论或推荐版本、Codex 下一步执行重点。
- Codex 不得只让 Claude “检查一下”而不指定产物路径；所有 Claude 输出都必须落到 `.handoff/claude/` 或用户指定的绝对路径。
- 若用户说“Claude 结束了”，Codex 必须优先读取该指定路径，而不是依赖对话记忆。

## 质量原则

- `strong_support` 才能默认进入可引用候选；`partial_support` 必须附带限定说明或改写建议。
- `page_missing`、`ocr_uncertain`、`secondhand_citation`、`concept_approximate` 必须进入人工复核清单。
- `conflict` 不能作为支撑引用，只能作为反对观点或风险提示。
- 作者原创观点、过渡句、常识句不得强行补注。
- 仍无证据的 critical claim 必须进入高风险清单，不得伪造脚注。
- RAG 反查必须发生在初始文献库建设和入库质量验收之后；旧版 pre-ingestion RAG 仅允许 fixture bypass 或用户明确声明已有 RAG 库。
- S50 RAG 反查结果是内部 executor 产物，不是用户手工回执；`state/rag-calls/<batch>.response.json` 必须先写入再进入证据解释。
- 脚注和尾注是正文内容的必要补充，不是参考文献罗列；`reference_only` 禁止进入脚注正文。
- 脚注是正文中“文中未尽而必要”的补充说明，必须是独立可读的说明性文字；纯证据支撑、纯文献出处、研究局限自我辩护和方法论免责不得作为脚注。
- `annotation_purpose=evidence`、`annotation_purpose=source_anchor` 和 `annotation_purpose=reference_only` 永远不得进入脚注候选池，只能进入参考文献规划或风险记录。
- 脚注候选必须在 build 阶段通过内容独立性、非文献格式、必要性和非自证性前置门禁；不得依赖 prune、写作池或 risk cleanup 清理本不该生成的脚注。
- 脚注正文不得包含完整参考文献引用格式，不得列作者、文献完整题名、期刊/出版社、年份页码组合或参考文献编号。
- 没有 S66-S68 的推进池式脚注意图结果，不得进入脚注候选池；RAG evidence reasoning 只能作为证据材料，不能直接作为脚注文本。
- `decision=rewrite_needed` 只能进入风险与建议，不得自动改正文，也不得改作脚注。
- 入库完成回执应报告 `usable_text_chars`，文献池平均可消费正文级材料低于 200 字/篇时必须标注材料风险。
- RAG 入库通常已经由 PDF 生成 MinerU/MU Markdown 或等价 parsed text。默认核查层是 RAG chunk 对 Markdown/parsed text 的定位和上下文复核；PDF 只在页码映射冲突、OCR/版式风险、表格/图片/竖排等场景作为 fallback。
- `analogy_only` 只能作为类比旁证，不能升级为 `strong_support`；一手权属缺失时不得强行补注。
- 最终插入和参考文献整理后，必须按全文顺序逐处复核真实性、位置和契合性；涉及正文/注释表达判断的点位必须进入 ReferenceFootnote 自有写作池审查，不得拆成脱离正文顺序的“脚注表”和“参考文献表”单独判断。
- 写作池审查只能给出四类结果：`keep`、`revise_note`、`move_note`、`drop_note`、`return_paragraph_for_rewrite`。除机械编号、格式和标点外，Codex 不得自行改正文判断强度；若需要改正文，必须要求写作池返回完整段落。
