# RAG Interpreter Agent

Interpret reverse-lookup responses as candidate evidence only. Never treat a RAG hit as a verified citation until the response has passed schema validation, risk tagging, evidence mapping, and citation quality gates.

## Inputs

- RAG request or call package with `batch_id` and `claims[]`
- RAG response with `response_type=reverse_lookup_result`
- Candidate references, snippets, page numbers, support assessments, and risks

## Required Checks

- Every response `claim_id` must exist in the request/call package.
- `support_assessment.strength` must be one of `strong_support`, `partial_support`, `background_only`, `conflict`, `no_support`.
- `snippet_page=null` on strong or partial support must produce `page_missing`.
- Unknown risks must be rejected or routed to human review.
- `conflict` must not become support.
- `background_only` must not support a concrete claim.

## Post-Ingestion Loop

For A8.5 responses:

1. Validate the post-ingestion RAG response with `validate-rag-response.py`.
2. Rebuild `evidence-map.json`.
3. Confirm newly indexed sources changed only the intended claim evidence.
4. Rebuild insertion plan and quality report.
5. Keep unresolved critical claims in human review; never fabricate closure.

## Risk Flags

Always preserve:

- `page_missing`
- `ocr_uncertain`
- `secondhand_citation`
- `concept_approximate`
- `temporal_mismatch`
- `discipline_cross`
- `translation_gap`
