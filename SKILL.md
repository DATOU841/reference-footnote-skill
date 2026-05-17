---
name: 参考文献补注
description: Use for ReferenceFootnote workflows on already-written academic articles when the task is to diagnose citation needs, reverse-lookup supporting literature in a RAG platform, form search-intake handoffs for unsupported claims, plan footnote/reference insertions, and build citation QA delivery packages. Do not use for writing articles from scratch, real CNKI/WoS/Zotero/PDF/RAG operations, or general polishing.
---

# 参考文献补注 Skill

版本：0.3.0-dev

## 硬边界

- 只面向已经写好的文章，不从零写论文。
- 不替代 `正文写作`，只输出补注任务包或人工补注方案。
- 不直接运行 CNKI、WoS、Zotero、PDF 获取或 RAG 导库。
- 不读取或操作 `openclaw-cnki-takeover`。
- 不探测 `localhost:22`。
- 不运行 writing-pool、advance-pool、mimo。
- 不使用正式文章任务目录作为测试场。
- 真实检索和入库只能通过结构化请求交给 `检索入库`。
- RAG 命中不能直接当成可靠引用，必须经过证据解释和风险门禁。

## 工作流

1. A0 启动和边界检查：运行 `scripts/startup.py`，确认离线模式和目录结构。
2. A1 文章导入：用 `scripts/article-intake.py` 生成 `article-structure.json`。
3. A2 Claim 拆解：用 `scripts/claim-segmentation.py` 生成 `claim-segments.json`。
4. A3 引用需求诊断：用 `scripts/citation-need-diagnosis.py` 生成 `citation-needs.json`。
5. A4 RAG 反查请求：用 `scripts/build-rag-request.py` 生成离线请求，不执行真实查询。
6. A5 RAG 证据解释：用 `scripts/validate-rag-response.py` 验证 fixture 或外部交回的离线响应。
7. A6 证据映射：用 `scripts/build-evidence-map.py` 汇总支撑强度、风险和缺口。
8. A7 检索入库交接：用 `scripts/build-search-handoff.py` 为无支撑关键 claim 生成分批请求。
9. A7.5 检索入库调用包：用 `scripts/build-search-intake-call.py` 生成交给 `检索入库` 的 JSON 调用包和中文提示词，等待用户授权或外部执行。
10. A8 补库完成应用：用 `scripts/apply-intake-completion.py` 记录 `检索入库` 返回状态。
11. A8.5 补库后二轮 RAG 调用包：用 `scripts/build-post-ingestion-rag-call.py` 为已入库来源生成二轮 RAG 反查调用包。
12. A9 脚注方案：用 `scripts/plan-footnotes.py` 生成插入建议、参考文献表和 no-insert zones。
13. A10 质量门禁：用 `scripts/validate-citation-plan.py` 生成质量报告。
14. A11 交付包：用 `scripts/build-delivery.py` 生成 delivery package。

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
