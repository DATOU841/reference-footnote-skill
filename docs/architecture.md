# Architecture

ReferenceFootnote is a deterministic offline protocol skill in 0.3.0-dev. Scripts read and write JSON artifacts under a task directory. External systems are represented by request/response and collaboration-call files only.

Core layers:

- Stage scripts: produce one artifact per phase.
- Validators: check structure and evidence rules.
- Fixtures: simulate article, RAG, search intake, and quality outcomes.
- Handoffs: prepare requests for `检索入库` and task packages for `正文写作` or human editors.
