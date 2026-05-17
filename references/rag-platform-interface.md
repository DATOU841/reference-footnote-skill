# RAG Platform Interface Reference

ReferenceFootnote uses RAG only through reverse-lookup request and response packages.

## Before Ingestion

`build-rag-request.py` prepares reverse lookup requests for claims whose citation need is critical, important, or recommended. In 0.3.0-dev this remains offline.

## After Search Intake

After `检索入库` returns completion, `build-post-ingestion-rag-call.py` prepares a second lookup package for rows where:

```json
{
  "import_status": {
    "rag_indexed": true
  }
}
```

This prevents ReferenceFootnote from querying material that has not been confirmed as imported.

## Response Contract

RAG responses must use:

- `response_type: reverse_lookup_result`
- `batch_id`
- `results[].claim_id`
- `results[].candidates[]`
- `candidates[].support_assessment.strength`
- `candidates[].support_assessment.confidence`
- `candidates[].match_details.snippet_page`
- `candidates[].risks[]`

Missing page numbers, OCR uncertainty, secondhand citation, approximate concepts, temporal mismatch, cross-discipline use, and translation gaps must be preserved as risks.

RAG hits are candidates only. They become citation suggestions only after `validate-rag-response.py`, `build-evidence-map.py`, and `validate-citation-plan.py` pass.

## Offline Closure Fixture

`tests/fixtures/mocks/post-ingestion-rag-response.json` demonstrates a post-ingestion response for a previously unsupported claim. The fixture flow is:

1. Build post-ingestion call package.
2. Validate the returned RAG response.
3. Rebuild evidence map.
4. Confirm the claim moves from `no_support` to `strong_support`.
5. Rebuild footnote insertion plan.

This verifies closure mechanics without any live RAG query.
