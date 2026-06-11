# 参考文献补注 / ReferenceFootnote

`参考文献补注 / ReferenceFootnote` 是一个面向已写文章的 Codex skill，用于系统诊断引用需求、构建 RAG 文献反查请求、解释候选证据、生成 `检索入库` 补库交接、规划脚注/参考文献插入方案，并打包 citation QA 交付物。

版本：`0.5.3-dev`

公开展示版中文介绍见：[docs/public-introduction.zh.md](docs/public-introduction.zh.md)。

当前版本不运行正式文章任务、CNKI/WoS/Zotero/PDF 获取、RAG 导库、推进池、mimo、服务器部署或 production 工作流。2.5 导库完成后的只读 RAG 反查由 ReferenceFootnote 的 executor 执行。

`0.5.3-dev` 修复 S50：不再要求用户提供 RAG 回执，而是由 `scripts/run-rag-reverse-lookup.py` 写入内部 `state/rag-calls/<batch>.response.json` 后继续 validate、grounding、ledger 和插注流程。写作池能力只用于注释位置/措辞/正文契合性审查，不依赖 `正文写作` skill。

本地校验：

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

发布必须经过 Claude 审查，且 P0/P1 问题修复后才允许进入发布流程。
