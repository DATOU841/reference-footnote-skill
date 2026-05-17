# Changelog

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
