# Grounding Protocol

0.5.1-dev uses Markdown-first grounding for citation evidence.

## Layers

1. `chunk_text`: RAG returned text. This proves the source was parsed enough to retrieve a candidate, but it is not enough for final citation by itself.
2. `markdown_path` or `parsed_text_path`: default verification layer, usually produced by MinerU/MU or an equivalent PDF parsing step during RAG ingestion.
3. `page_map`: preferred bridge between parsed text and source pagination.
4. `pdf_path`: fallback only for layout-sensitive or page-map-risk cases.

## Status Values

| Status | Meaning | Citation handling |
|---|---|---|
| `full_markdown_grounding` | chunk is linked to Markdown/parsed text | may proceed through normal quality gates |
| `page_mapped_grounding` | chunk has reliable page map but no Markdown path | may proceed with page-map consistency check |
| `chunk_only_grounding` | only RAG chunk is available | warning; verify against Markdown/parsed text before final insertion |
| `pdf_fallback_required` | page map or layout/OCR risk requires visual/source fallback | blocks final citation until fallback review |
| `unresolved_grounding` | no usable source locator | blocks strong support |
| `not_resolved` | resolver has not been run | allowed in legacy fixtures, not acceptable for release-quality article output |

## Risk Triggers

PDF fallback is triggered by `ocr_uncertain`, `vertical_text`, `table_complex`, `figure_embedded`, `formula_inline`, `footnote_in_source`, `page_map_conflict`, or `markdown_page_map_missing`.

## Evidence Strength

`analogy_only` is separate from `partial_support`. Adjacent grid, similar product, or neighboring teaching method evidence cannot become direct support for the article object. Ownership or product-origin claims require primary materials; otherwise use `ownership_unverified` and no automatic insertion.
