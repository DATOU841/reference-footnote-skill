# 文衡原生接入协议

## 适用范围

本协议适用于 ReferenceFootnote 的补注诊断、检索入库交接、RAG 反查、证据地图、脚注/参考文献规划、写作池式审查和最终交付包。

## 启动前置

正式开工前必须已有文衡 B02 task packet，至少包含：

- `wenheng_task_id`
- `task_folder`
- `task_type = reference_footnote`
- `target_skill`
- `f06_routing_decision`
- `h08_evidence_stub`
- `e05_boundary`

缺少任一关键字段时，只能生成 `wenheng-intake-request`，不得进入 S00 正式 workflow、不得读取真实全文或 RAG 数据。

## F06/E05/G07

启动前读取 F06 routing decision，确认目标通道未 forbidden。S40/S45/S50/S65/S120 必须写 E05/B02/H08 脱敏状态。涉及注释措辞、正文契合性和风险表述时读取 G07 active rules；纯证据反查阶段可不适用，但必须写 `style_memory_not_applicable_reason`。

必须写入 `style_memory_source`、`style_memory_rules_applied`、`style_memory_rules_ignored`、`style_memory_conflicts`、`style_memory_not_applicable_reason`、`style_memory_feedback_candidate_id`。

## B02/H08 回写

S00-S120 关键节点必须回写 B02 timeline。失败进入 H08 error review；完成进入文衡 archive package；风险清理经验、用户反馈和交付复盘进入 G07 feedback candidate。

## 数据边界

进入文衡的字段只允许摘要、计数、占位 ID、风险、阶段、相对 task folder 引用和 next action。不得写真实全文、RAG chunk、PDF 内容、Zotero 底层数据、附件路径、绝对路径、cookie、token 或 key。
