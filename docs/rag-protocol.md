# RAG Reverse Lookup Protocol

The skill only builds and validates reverse-lookup payloads. It does not query a live RAG service in 0.5.0-dev. RAG reverse lookup is blocked until initial library intake is complete, unless the user explicitly declared an existing RAG library.

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
- `background_only`
- `conflict`
- `no_support`

## Evidence Rules

RAG hits are candidate evidence only. A candidate cannot become a clean citation when it has unresolved risks such as `page_missing`, `ocr_uncertain`, `secondhand_citation`, `concept_approximate`, `temporal_mismatch`, `discipline_cross`, or `translation_gap`.
