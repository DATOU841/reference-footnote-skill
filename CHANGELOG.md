# Changelog

## 0.5.0-dev - 2026-05-18

- Reworked the workflow into a retrieval-first pipeline: article-derived search blueprint, initial library-building handoff to `检索入库`, intake completion, intake quality gate, then RAG reverse lookup.
- Added `build-search-blueprint.py`, `build-initial-search-handoff.py`, and `validate-intake-quality.py`.
- Made `build-rag-request.py` block pre-ingestion RAG unless the user declared an existing RAG library or a legacy fixture explicitly bypasses it.
- Added `search_intake_library_build` protocol fields and library quality requirements.
- Expanded offline fixtures from 29 to 41, including retrieval-first blocking, initial library quality pass/fail, round2 gap handoff, and delivery propagation.

## 0.4.0-dev - 2026-05-18

- Added material quality tracking for search-intake completion rows with `usable_text_chars`, `material_flag`, and pool average status.
- Added A9a/A9b/A9c scripts for footnote candidate pools, necessity pruning, and reference pruning.
- Added A10a/A10b/A10c scripts for authenticity verification requests, synthetic verification result application, and footnote/reference consistency gates.
- Updated insertion plans to distinguish `footnote`, `endnote`, and `reference_only`, and to carry annotation purpose, necessity score, material risk, authenticity status, and pruning audit data.
- Expanded offline fixtures from 19 to 29 to cover material thresholds, pruning, reference-only blocking, PDF/RAG authenticity risks, wrong insertion positions, unconsumed references, and delivery package propagation.

## 0.3.0-dev - 2026-05-17

- Added an offline post-ingestion RAG closure fixture that validates the returned RAG response, rebuilds the evidence map, and regenerates the insertion plan.
- Expanded coordinator and RAG interpreter agent guidance for A7.5/A8.5 collaboration stages.
- Documented search-intake and post-ingestion RAG call package schemas, including downstream-only server entry metadata.

## 0.2.0-dev - 2026-05-17

- Added offline collaboration call packages for invoking `检索入库` through structured JSON and a generated Chinese prompt.
- Added post-ingestion RAG reverse-lookup call package generation based on confirmed `rag_indexed` completion rows.
- Added collaboration flow documentation and RAG platform interface reference.
- Expanded offline fixtures for search-intake skill calls and post-ingestion RAG calls.

## 0.1.0-dev - 2026-05-16

- Initial offline ReferenceFootnote skill structure.
- Added stage machine, RAG reverse-lookup protocol, search-intake handoff protocol, and citation quality gates.
- Added deterministic offline scripts and fixtures for article intake through delivery package planning.
- Added a public Chinese introduction for feature display and updated README navigation.
- Aligned search-intake and writing handoff fields with upstream/downstream skill protocols before GitHub publication.
