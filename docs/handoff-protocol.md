# Handoff Protocol

ReferenceFootnote 只生成和验证离线交接数据，不执行上下游真实任务。

## To 检索入库

Top-level fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `protocol_version` | yes | 当前为 `1.0` |
| `request_type` | yes | 固定为 `search_intake_gap` |
| `source_skill` | yes | 固定为 `参考文献补注` |
| `target_skill` | yes | 固定为 `检索入库` |
| `staging_status` | yes | 0.3.0-dev 固定为 `blocked` |
| `handoff_id` | yes | 本批交接 ID |
| `batch_id` | yes | 分批 ID |
| `macro_round` | yes | `round1` 或 `round2` |
| `priority` | yes | `P0`、`P1`、`P2` |
| `requests[]` | yes | gap 驱动的补库请求 |

`requests[]` fields:

| Field | Meaning |
| --- | --- |
| `request_id` | 请求 ID |
| `macro_round` | 第一大轮或第二大轮 |
| `gap_id` | 可映射到 writer gap-routing-table 的 gap ID |
| `claim_id` | ReferenceFootnote claim ID |
| `claim_text` | 原 claim 文本 |
| `claim_type` | claim 类型 |
| `need_level` | citation need level |
| `source_need` | 所需来源类型 |
| `priority` | 单条优先级 |
| `source_direction` | 来源方向说明 |
| `purpose` | 补库目的 |
| `minimum_requirement` | 最低要求 |
| `ideal_requirement` | 理想要求 |
| `search_strategy.keywords_zh` | 中文关键词 |
| `search_strategy.keywords_en` | 英文关键词 |
| `search_strategy.author_hints` | 作者线索 |
| `search_strategy.theory_hints` | 理论线索 |
| `search_strategy.databases` | 目标数据库，如 CNKI、WoS |
| `search_strategy.source_types` | 期刊、专著、一手材料等 |
| `search_strategy.discipline` | 学科 |
| `search_strategy.constraints` | gap 驱动、不泛检、目标库等约束 |

第二大轮请求必须保持 gap driven，只进入 `C` 库，不覆盖第一大轮基线。

## From 检索入库

Top-level fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `completion_id` | yes | 完成回执 ID |
| `handoff_id` | yes | 对应 handoff |
| `batch_id` | yes | 对应 batch |
| `status` | yes | `completed`、`partial`、`failed` |
| `results[]` | yes | 每条请求的完成结果 |

`results[]` fields:

| Field | Meaning |
| --- | --- |
| `request_id` | 对应请求 ID |
| `claim_id` | 对应 claim |
| `status` | `completed`、`partial`、`failed` 或 `ingested` |
| `sources_found[]` | 找到的来源摘要 |
| `kb_routing.macro_round` | round1 / round2 |
| `kb_routing.target_kb` | A / B / C |
| `kb_routing.rag_index` | RAG 索引或库名 |
| `pdf_status.required` | 是否需要 PDF |
| `pdf_status.available` | PDF 是否可用 |
| `pdf_status.verified` | PDF 是否核验 |
| `import_status.stage25_ready` | 是否达到 2.5 ready |
| `import_status.rag_indexed` | 是否已入 RAG |
| `import_status.import_batch_id` | 导库批次 |
| `zotero_id` | Zotero key 或条目 ID |
| `ref_metadata` | title、authors、year、source、pages |

`apply-intake-completion.py` 只验证并记录这些字段，不触发真实导库或二轮查询。

## To 正文写作 Or Human

`handoff_to_writing.json` fields:

| Field | Meaning |
| --- | --- |
| `target_skill` | 固定为 `正文写作` |
| `protocol_version` | 当前为 `1.0` |
| `quality_status` | A10 质量门禁状态 |
| `insertions[]` | 可执行脚注插入任务 |
| `no_insert_zones[]` | 不得自动补注的位置 |
| `high_risk_unsupported[]` | 高风险证据项 |
| `unresolved_critical_claims[]` | 仍未闭合的 critical claims |
| `existing_references_merge_status` | 既有参考文献合并状态 |
| `writer_consumption_notes` | 给 writer 的消费说明 |

`insertions[]` should include:

- `claim_id`
- `claim_type`
- `need_level`
- `target_location`
- `evidence_type`
- `source_role`
- `consumption_depth_suggestion`
- `footnote_content.text`
- `gbt7714_footnote`
- `evidence_basis.support_strength`
- `evidence_basis.confidence`
- `evidence_basis.risks`
- `requires_rewrite`
- `rewrite_suggestion`

`no_insert_zones[]` should include `no_insert_reason` and optional `writer_action` so writer can decide whether to mark author opinion, lower claim strength, delete, or send to human review.

## Search-Intake Call Package Schema

`build-search-intake-call.py` wraps a search-intake handoff for an external `检索入库` run.

| Field | Meaning |
| --- | --- |
| `call_type` | `skill_handoff_call` |
| `call_id` | call package ID |
| `source_skill` | `参考文献补注` |
| `target_skill` | `检索入库` |
| `execution_status` | fixed `prepared_not_executed` |
| `requires_user_authorization_for_real_search` | true |
| `allowed_real_executor` | `检索入库` |
| `allowed_server_entry_if_authorized` | optional metadata for the downstream executor; ReferenceFootnote must not execute it |
| `forbidden_for_referencefootnote[]` | forbidden external actions |
| `handoff` | original search-intake request |
| `expected_completion_schema` | completion fields that `apply-intake-completion.py` validates |

## Post-Ingestion RAG Call Package Schema

`build-post-ingestion-rag-call.py` prepares a second RAG lookup after ingestion.

| Field | Meaning |
| --- | --- |
| `call_type` | `rag_reverse_lookup_after_ingestion` |
| `target_system` | `RAG platform` |
| `execution_status` | fixed `prepared_not_executed` |
| `requires_external_rag_operator` | true |
| `claims[]` | only claims whose completion row has `import_status.rag_indexed=true` |
| `return_contract` | required RAG response fields and risk policy |
