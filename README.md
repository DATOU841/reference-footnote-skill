# ReferenceFootnote / 参考文献补注

`参考文献补注 / ReferenceFootnote` 是一个面向已写文章的 Codex skill，用于系统诊断引用需求、构建 RAG 文献反查请求、解释候选证据、生成 `检索入库` 补库交接、规划脚注/参考文献插入方案，并打包 citation QA 交付物。

Version: `0.1.0-dev`.

公开展示版中文介绍见：[docs/public-introduction.zh.md](docs/public-introduction.zh.md)。

This version is offline-first. It must not run formal article tasks, CNKI/WoS/Zotero/PDF retrieval, RAG ingestion, writing-pool, advance-pool, mimo, server deployment, or production workflows.

Local gates:

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

Publication stays blocked until Claude review exists and P0/P1 findings are fixed.
