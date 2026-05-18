# 参考文献补注 / ReferenceFootnote

`参考文献补注 / ReferenceFootnote` 是一个面向已写文章的 Codex skill，用于系统诊断引用需求、构建 RAG 文献反查请求、解释候选证据、生成 `检索入库` 补库交接、规划脚注/参考文献插入方案，并打包 citation QA 交付物。

版本：`0.5.0-dev`

公开展示版中文介绍见：[docs/public-introduction.zh.md](docs/public-introduction.zh.md)。

当前版本是离线优先开发版，不运行正式文章任务、CNKI/WoS/Zotero/PDF 获取、RAG 导库、写作池、推进池、mimo、服务器部署或 production 工作流。

`0.5.0-dev` 修正为 retrieval-first 管线：先从文章反推检索方向、关键词和来源类型，生成 `检索入库` 初始文献库建设请求；待入库完成并通过质量验收后，才允许 RAG 反查、证据映射、脚注候选和参考文献裁剪。没有已建库或用户声明已有 RAG 库时，不得直接拼凑参考文献。

本地校验：

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

发布必须经过 Claude 审查，且 P0/P1 问题修复后才允许进入发布流程。
