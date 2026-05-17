# 参考文献补注 / ReferenceFootnote

`参考文献补注 / ReferenceFootnote` 是一个面向已写文章的 Codex skill，用于系统诊断引用需求、构建 RAG 文献反查请求、解释候选证据、生成 `检索入库` 补库交接、规划脚注/参考文献插入方案，并打包 citation QA 交付物。

版本：`0.2.0-dev`

公开展示版中文介绍见：[docs/public-introduction.zh.md](docs/public-introduction.zh.md)。

当前版本是离线优先开发版，不运行正式文章任务、CNKI/WoS/Zotero/PDF 获取、RAG 导库、写作池、推进池、mimo、服务器部署或 production 工作流。

`0.2.0-dev` 增加协同调用层：ReferenceFootnote 可以为必要文献检索和入库生成 `检索入库` skill 调用包，并在入库完成后生成二轮 RAG 文献反查调用包。调用包只负责准备 JSON 和提示词，真实执行仍由对应 skill 或平台完成。

本地校验：

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

发布必须经过 Claude 审查，且 P0/P1 问题修复后才允许进入发布流程。
