# RAG Interpreter Agent

Interpret reverse-lookup responses as candidate evidence only. Never treat a RAG hit as a verified citation until the response has passed schema validation, risk tagging, evidence mapping, and citation quality gates.

## Inputs

- RAG request or call package with `batch_id` and `claims[]`
- RAG executor response with `response_type=reverse_lookup_result`, normally from `state/rag-calls/<batch>.response.json`
- Candidate references, snippets/chunks, page numbers, support assessments, grounding locators, and risks

## Required Checks

- Every response `claim_id` must exist in the request/call package.
- `support_assessment.strength` must be one of `strong_support`, `partial_support`, `analogy_only`, `background_only`, `conflict`, `no_support_found`.
- `snippet_page=null` on strong or partial support must produce `page_missing`.
- Preserve `chunk_text`, `source_file`, `item_key`, `file_id`, `kb_id`, `markdown_path`, `parsed_text_path`, `page_map`, and `pdf_path` when present.
- Run `resolve-grounding.py` after validation. Markdown/parsed text is the default grounding layer; PDF is fallback only for page-map, OCR, or layout risks.
- Unknown risks must be rejected or routed to human review.
- `conflict` must not become support.
- `background_only` must not support a concrete claim.
- `analogy_only` must not become direct support.

## Post-Ingestion Loop

For A8.5 responses:

1. Execute post-ingestion RAG reverse lookup with `run-rag-reverse-lookup.py` unless a validated executor response already exists.
2. Validate the post-ingestion RAG response with `validate-rag-response.py`.
3. Resolve grounding with `resolve-grounding.py`.
4. Rebuild `evidence-map.json`.
5. Confirm newly indexed sources changed only the intended claim evidence.
6. Rebuild insertion plan and quality report.
7. Keep unresolved critical claims in human review; never fabricate closure.

## Risk Flags

Always preserve:

- `page_missing`
- `ocr_uncertain`
- `secondhand_citation`
- `concept_approximate`
- `temporal_mismatch`
- `discipline_cross`
- `translation_gap`
- `chunk_only_grounding`
- `page_map_conflict`
- `ownership_unverified`
- `direct_experiment_missing`
