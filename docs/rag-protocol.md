# RAG Reverse Lookup Protocol

The skill builds, executes, and validates reverse-lookup payloads after 2.5 RAG ingestion is complete. It does not ingest into RAG. RAG reverse lookup is blocked until initial library intake is complete, unless the user explicitly declared an existing RAG library.

## Executor

`scripts/run-rag-reverse-lookup.py` reads `state/rag-requests/<batch>.json`, reads `config/rag-executor.yaml`, then writes `state/rag-calls/<batch>.response.json`.

- `mode: mock` keeps local gates offline and can synthesize fixture responses.
- `mode: live` requires `base_url`, `api_key_env`, and `model`.
- missing live configuration blocks with `missing_rag_executor_config`; it is not converted into a user-facing response request.

## Request

Required fields:

- `protocol_version`: `1.0`
- `request_type`: `reverse_lookup`
- `batch_id`
- `claims[]`
- each claim: `claim_id`, `text`, `claim_type`, `need_level`, `citation_type`, `search_dimensions`, `context`

Search dimensions may include semantic text, keywords, concepts, author hints, theory hints, known references, and constraints.

## Response

Required fields:

- `protocol_version`: `1.0`
- `response_type`: `reverse_lookup_result`
- `batch_id`
- `results[]`
- each result: `claim_id`, `status`, `candidates[]`

Candidate support strength must be one of:

- `strong_support`
- `partial_support`
- `analogy_only`
- `background_only`
- `conflict`
- `no_support_found`

## Evidence Rules

RAG hits are candidate evidence only. A candidate cannot become a clean citation when it has unresolved risks such as `page_missing`, `ocr_uncertain`, `secondhand_citation`, `concept_approximate`, `temporal_mismatch`, `discipline_cross`, or `translation_gap`.

RAG responses should include any available `chunk_text`, `source_file`, `item_key`, `file_id`, `kb_id`, `markdown_path`, `parsed_text_path`, `page_map`, and `pdf_path`. `chunk_text` is the locator; Markdown/parsed text is the default verification layer; PDF is fallback only when page-map, OCR, or layout risks require it. See `docs/grounding-protocol.md`.

Allowed support strengths are `strong_support`, `partial_support`, `analogy_only`, `background_only`, `conflict`, and `no_support_found`. `analogy_only` cannot be promoted to direct support.
