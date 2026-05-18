---
name: 参考文献补注
description: Use for ReferenceFootnote workflows on already-written academic articles when the task is to diagnose citation needs, reverse-lookup supporting literature in a RAG platform, form search-intake handoffs for unsupported claims, plan footnote/reference insertions, and build citation QA delivery packages. Do not use for writing articles from scratch, real CNKI/WoS/Zotero/PDF/RAG operations, or general polishing.
---

# 参考文献补注 Skill

版本：0.5.0-dev

## 硬边界

- 只面向已经写好的文章，不从零写论文。
- 不替代 `正文写作`，只输出补注任务包或人工补注方案。
- 不直接运行 CNKI、WoS、Zotero、PDF 获取或 RAG 导库。
- 不读取或操作 `openclaw-cnki-takeover`。
- 不探测 `localhost:22`。
- 不运行 writing-pool、advance-pool、mimo。
- 不使用正式文章任务目录作为测试场。
- 真实检索和入库只能通过结构化请求交给 `检索入库`。
- 对没有已声明可用 RAG 文献库的文章，必须先反推检索蓝图并交给 `检索入库` 建设初始文献库；不得在无库状态编造参考文献。
- RAG 命中不能直接当成可靠引用，必须经过证据解释和风险门禁。

## 工作流

1. A0 启动和边界检查：运行 `scripts/startup.py`，确认离线模式和目录结构。
2. A1 文章导入：用 `scripts/article-intake.py` 生成 `article-structure.json`。
3. A2 Claim 拆解：用 `scripts/claim-segmentation.py` 生成 `claim-segments.json`。
4. A3 引用需求诊断：用 `scripts/citation-need-diagnosis.py` 生成 `citation-needs.json`。
5. A3.5 检索蓝图：用 `scripts/build-search-blueprint.py` 从文章整体反推研究方向、关键词、来源类型和文献池质量要求。
6. A4 初始文献库建设交接：用 `scripts/build-initial-search-handoff.py` 生成 `search_intake_library_build` 请求。
7. A4.5 初始文献库调用包：用 `scripts/build-search-intake-call.py` 生成交给 `检索入库` 的 JSON 调用包和中文提示词。
8. A5 入库完成应用：用 `scripts/apply-intake-completion.py` 记录 `检索入库` 返回状态。
9. A5.5 入库质量验收：用 `scripts/validate-intake-quality.py` 检查文献池数量、可消费材料、来源类型覆盖和 RAG 入库率。
10. A6 入库后 RAG 反查请求：用 `scripts/build-rag-request.py` 生成离线请求；无入库完成或用户声明已有库时必须拒绝。
11. A6.5 RAG 证据解释：用 `scripts/validate-rag-response.py` 验证 fixture 或外部交回的离线响应。
12. A7 证据映射：用 `scripts/build-evidence-map.py` 汇总支撑强度、风险和缺口。
13. A7.5 缺口二轮补库交接：用 `scripts/build-search-handoff.py` 为 RAG 后仍无支撑的关键 claim 生成 `round2` gap 请求。
14. A7.6 缺口补库调用包：用 `scripts/build-search-intake-call.py` 生成二轮交接包。
15. A8/A8.5 可用于二轮入库完成和二轮 RAG 回流。
16. A9a-A9c 脚注候选池、必要性裁剪和参考文献裁剪。
17. A9-A11 脚注方案、质量门禁、真实性复核、边界一致性和交付包。

## 何时读取参考文件

- 需要阶段机细节时读 `docs/state-machine.md`。
- 需要 RAG 反查请求/响应格式时读 `docs/rag-protocol.md`。
- 需要与 `检索入库` 或 `正文写作` 交接时读 `docs/handoff-protocol.md`。
- 需要理解检索入库调用包和补库后二轮 RAG 调用时读 `docs/collaboration-flow.md`。
- 需要判断证据强度和风险时读 `docs/evidence-classification.md`。
- 需要发布或部署边界时读 `docs/quality-gates.md` 和 `docs/boundary-rules.md`。

## 质量原则

- `strong_support` 才能默认进入可引用候选；`partial_support` 必须附带限定说明或改写建议。
- `page_missing`、`ocr_uncertain`、`secondhand_citation`、`concept_approximate` 必须进入人工复核清单。
- `conflict` 不能作为支撑引用，只能作为反对观点或风险提示。
- 作者原创观点、过渡句、常识句不得强行补注。
- 仍无证据的 critical claim 必须进入高风险清单，不得伪造脚注。
- RAG 反查必须发生在初始文献库建设和入库质量验收之后；旧版 pre-ingestion RAG 仅允许 fixture bypass 或用户明确声明已有 RAG 库。
- 脚注和尾注是正文内容的必要补充，不是参考文献罗列；`reference_only` 禁止进入脚注正文。
- 入库完成回执应报告 `usable_text_chars`，文献池平均可消费正文级材料低于 200 字/篇时必须标注材料风险。
- 最终插入和参考文献整理后，必须通过外部 PDF + RAG 回执逐条复核真实性、页码/OCR、位置和契合性。
