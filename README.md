# 参考文献补注 / ReferenceFootnote

`参考文献补注 / ReferenceFootnote` 是一个面向已写文章的 Codex skill，用于系统诊断引用需求、构建 RAG 文献反查请求、解释候选证据、生成 `检索入库` 补库交接、规划脚注/参考文献插入方案，并打包 citation QA 交付物。

版本：`0.5.2-dev`

公开展示版中文介绍见：[docs/public-introduction.zh.md](docs/public-introduction.zh.md)。

当前版本是离线优先开发版，不运行正式文章任务、CNKI/WoS/Zotero/PDF 获取、RAG 导库、推进池、mimo、服务器部署或 production 工作流。

`0.5.2-dev` 在 retrieval-first 和 Markdown-first grounding 基础上重构全流程：新增全文顺序 evidence trace ledger、独立写作池式审查、风险清单到清理到清理后重建的闭环、完整全文插入、全文顺序核查和最终交付 gate。写作池能力只用于注释位置/措辞/正文契合性审查，不依赖 `正文写作` skill。

本地校验：

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

发布必须经过 Claude 审查，且 P0/P1 问题修复后才允许进入发布流程。
