# 检索入库接口参考

本文件说明 ReferenceFootnote 如何只通过结构化交接复用 `检索入库` 能力。ReferenceFootnote 不执行真实 CNKI/WoS 检索、Zotero 保存、PDF 获取或 RAG 导库。

## 检索入库职责边界

`检索入库` 只负责正式第 `1 / 2 / 2.5` 步：

- 第 1 步：CNKI 主检索和必要 WoS 外文补检。
- 第 2 步：服务器侧 Zotero 保存、PDF 获取和正式验收。
- 第 2.5 步：RAG 导库、库状态回写和正式交接物生成。

固定停点是 `2.5 ready`。达到该状态后，`检索入库` 必须停止并把交接物留给第三步或后续 skill 消费。

## 2.5 Ready 交接产物

ReferenceFootnote 只记录这些产物的存在、用途和回填字段，不自行生成或修改真实产物：

| 产物 | 用途 |
| --- | --- |
| `kb-state.json` | 当前知识库状态、ready 状态和导库摘要 |
| `kb-routing-map.json` | A/B/C 库路由、任务库和消费顺序 |
| `rag-import-summary.md` | 第 2.5 步导库摘要和异常说明 |
| `kb-usage-brief.md` | 给后续写作或补注使用的知识库消费说明 |
| `hss-handoff-v2.md` | 前两步交给第三步的正式总交接 |
| `zotero-reference-master.md` | Zotero 参考文献总表 |
| `zotero-reference-citation-export.md` | 可用于脚注/参考文献的格式化导出 |
| `source-concentration-report.md` | 来源集中度与 RED 风险 |
| `source-consumption-priority-map.md` | 来源消费优先级 |
| `kb-argument-function-brief.md` | 来源对应的论证功能说明 |

第二大轮回流还应有：

- `第二大轮新增导库说明.md`
- `第二大轮交给正文写作的正式交接.md`
- `第二大轮增量证据优先消费说明.md`

## A / B / C 库语义

| 库 | 语义 | 默认消费 |
| --- | --- | --- |
| A | 主库，任务长期基线库 | 第一大轮与第二大轮都默认消费 |
| B | 第一大轮增补库 | 第一大轮与 A 联合消费 |
| C | 第二大轮增补库 | 第二大轮与 A 联合消费 |

ReferenceFootnote 生成补库请求时应带 `macro_round` 和 `target_kb`。第一大轮默认写向 `B`，第二大轮回流默认写向 `C`。

## Search Intake Request 映射

ReferenceFootnote 的 `search_intake_request` 对应 `检索入库` 或 writer 侧 `round2-search-plan.md` 的结构化来源需求。每条请求必须能回答：

- 这是第几大轮：`macro_round`
- 对应哪个 gap：`gap_id`
- 对应哪个 claim：`claim_id`
- 需要什么来源：`source_need`
- 来源方向是什么：`source_direction`
- 最低与理想补库标准是什么：`minimum_requirement`、`ideal_requirement`
- 检索策略是什么：中文/英文关键词、作者线索、理论线索、数据库、来源类型、学科和约束

第二大轮回流必须是 gap 驱动补料，不是泛检，不是自由扩池。

## Intake Completion 返回字段

`检索入库` 完成后，ReferenceFootnote 期望每条 `results[]` 至少包含：

- `request_id`
- `claim_id`
- `status`: `completed`、`partial`、`failed` 或 `ingested`
- `sources_found[]`
- `kb_routing`: `macro_round`、`target_kb`、`rag_index`
- `pdf_status`: `required`、`available`、`verified`
- `import_status`: `stage25_ready`、`rag_indexed`、`import_batch_id`
- `zotero_id`
- `ref_metadata`: title、authors、year、source、pages

ReferenceFootnote 只记录 completion 状态，不触发真实 RAG 查询或导库。

## Zotero 与 GB/T 7714

当 `zotero-reference-master.md` 或 `zotero-reference-citation-export.md` 提供 GB/T 7714 双语脚注成品时，ReferenceFootnote 应优先透传到 `insertion_plan` 和 `handoff_to_writing.json`。若只有模拟或候选 metadata，则只能标为待人工核验。
