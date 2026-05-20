---
name: 参考文献补注
description: Use for ReferenceFootnote workflows on already-written academic articles when the task is to diagnose citation needs, reverse-lookup supporting literature in a RAG platform, form search-intake handoffs for unsupported claims, plan footnote/reference insertions, and build citation QA delivery packages. Do not use for writing articles from scratch, real CNKI/WoS/Zotero/PDF/RAG operations, or general polishing.
---

# 参考文献补注 Skill

版本：0.5.2-dev

## 硬边界

- 只面向已经写好的文章，不从零写论文。
- 不替代 `正文写作`，不执行正式正文生产链；但本 skill 可独立调用“写作池式审查”能力，用于注释位置、注释措辞、正文契合性和论证强度复核。
- 不直接运行 CNKI、WoS、Zotero、PDF 获取或 RAG 导库。
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
7. S50 逐段/逐句 RAG 反查：用 `scripts/build-rag-request.py` 和 `scripts/validate-rag-response.py` 生成/消费离线 RAG 请求与回执。
8. S55 grounding 解析：用 `scripts/resolve-grounding.py` 将 RAG chunk 映射到 MinerU/MU Markdown、parsed text、page map 或 PDF fallback 状态。
9. S60 evidence trace ledger：用 `scripts/build-evidence-trace-ledger.py` 建立按全文顺序的证据主线。
10. S65 证据地图和缺口交接：用 `scripts/build-evidence-map.py`、`scripts/build-search-handoff.py`、`scripts/build-search-intake-call.py` 生成二轮补库请求。
11. S70 注释/参考文献规划：用候选池、裁剪和 `scripts/plan-footnotes.py` 生成 `insertion-plan.json`。
12. S80 独立写作池式审查：用 `scripts/build-writing-pool-review-request.py`、`scripts/apply-writing-pool-review-result.py`、`scripts/validate-writing-pool-review.py` 复核位置、措辞和正文契合性。
13. S85 风险清单：用 `scripts/build-risk-inventory.py` 输出高风险点。
14. S90 风险清理：用 `scripts/build-risk-cleanup-plan.py`、`scripts/apply-risk-cleanup-result.py` 清理风险。
15. S95 清理后重建：用 `scripts/rebuild-cleaned-artifacts.py` 生成清理后的 citation needs、注释计划、参考文献和补库需求。
16. S100 完整全文插入：用 `scripts/insert-full-text.py` 生成插入注释和参考文献的完整 Markdown。
17. S105 全文顺序核查：用 `scripts/export-full-order-audit.py` 输出全文顺序逐条核查清单。
18. S110 最终 gate：用 `scripts/validate-final-delivery-gate.py` 阻断未清理风险、未闭合写作池要求、未消费文献等问题。
19. S120 交付包：用 `scripts/build-delivery.py` 输出收束后的交付包；过程材料进入 `delivery/process/`。

## 何时读取参考文件

- 需要阶段机细节时读 `docs/state-machine.md`。
- 需要 RAG 反查请求/响应格式时读 `docs/rag-protocol.md`。
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
- 脚注和尾注是正文内容的必要补充，不是参考文献罗列；`reference_only` 禁止进入脚注正文。
- 入库完成回执应报告 `usable_text_chars`，文献池平均可消费正文级材料低于 200 字/篇时必须标注材料风险。
- RAG 入库通常已经由 PDF 生成 MinerU/MU Markdown 或等价 parsed text。默认核查层是 RAG chunk 对 Markdown/parsed text 的定位和上下文复核；PDF 只在页码映射冲突、OCR/版式风险、表格/图片/竖排等场景作为 fallback。
- `analogy_only` 只能作为类比旁证，不能升级为 `strong_support`；一手权属缺失时不得强行补注。
- 最终插入和参考文献整理后，必须按全文顺序逐处复核真实性、位置和契合性；涉及正文/注释表达判断的点位必须进入 ReferenceFootnote 自有写作池审查，不得拆成脱离正文顺序的“脚注表”和“参考文献表”单独判断。
- 写作池审查只能给出四类结果：`keep`、`revise_note`、`move_note`、`drop_note`、`return_paragraph_for_rewrite`。除机械编号、格式和标点外，Codex 不得自行改正文判断强度；若需要改正文，必须要求写作池返回完整段落。
