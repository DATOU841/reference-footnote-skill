# Handoff Protocol

## To 检索入库

ReferenceFootnote creates offline `search_intake_request` payloads for claims whose evidence status is `no_support`, especially `critical` and `important` needs.

Required top-level fields:

- `handoff_id`
- `protocol_version`
- `request_type`: `search_intake_gap`
- `source_skill`: `参考文献补注`
- `target_skill`: `检索入库`
- `staging_status`: `blocked`
- `batch_id`
- `requests[]`

Each request includes claim text, citation purpose, search strategy, minimum requirement, ideal requirement, and priority. The skill does not execute the request.

## From 检索入库

`apply-intake-completion.py` accepts a completion payload containing:

- `completion_id`
- `handoff_id`
- `batch_id`
- `status`: `completed`, `partial`, or `failed`
- `results[]`

The completion only records intake status. It does not trigger live RAG queries.

## To 正文写作 Or Human

The final delivery package includes `handoff_to_writing.json` with insertion tasks, rewrite suggestions, no-insert zones, high-risk citations, and unresolved critical claims.
