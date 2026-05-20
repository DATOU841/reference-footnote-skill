# RAG Markdown Grounding 修复规划

版本目标：0.5.1-dev
日期：2026-05-20
状态：待 Codex 执行

---

## 一、问题诊断

### 1.1 核心误解

当前 skill（0.5.0-dev）对 RAG 入库解析链路的理解存在以下错误：

| 错误 | 表现 | 后果 |
|------|------|------|
| 把"任务目录没有显式 .md 文件"误判为"RAG 未解析" | validate-rag-response.py 不解析 chunk 来源路径 | 无法区分已解析/未解析状态 |
| 把"逐条回原 PDF"设为默认第一核查层 | authenticity-verification-request 默认要求 PDF 核验 | 浪费核验资源，忽略 Markdown 层 |
| 无 grounding resolver | 没有脚本解析 chunk_text → source_file → markdown_path → page_map → PDF 的链路 | 无法判断证据来源的可靠层级 |
| 无 grounding_status 分类 | evidence-map 只有 evidence_status（强度），没有 grounding_status（来源可靠性） | 无法区分 full_markdown_grounding 和 chunk_only_grounding |

### 1.2 正确语义

检索入库 skill 的 2.5 RAG 导库通常已完成：

```
PDF → MinerU/MU Markdown 或等价解析文本 → chunk 切片 → RAG 入库
```

ReferenceFootnote 消费的是 RAG response，其中 chunk_text 已经是解析后的文本。"当前任务目录没有显式导出每篇 PDF 的 .md 文件"不等于"RAG 未解析"。

### 1.3 正确核查层级

| 层级 | 角色 | 何时使用 |
|------|------|----------|
| RAG chunk_text | 快速定位层 | 始终可用（RAG response 必含） |
| MinerU/MU Markdown 或 parsed_text | 默认上下文、真实性、契合性核查层 | 有 markdown_path 或 parsed_text_path 时 |
| page_map | chunk/Markdown 到 PDF 页码的优先连接层 | 有 page_map 时 |
| 原 PDF | 兜底核验层 | Markdown 不存在、page_map 缺失/冲突、OCR/版面异常、表格/图片/脚注/公式/竖排不可靠、最终投稿需目视页码时 |

### 1.4 当前风险清单

1. 把没有显式 Markdown 文件误判为 RAG 未解析
2. 把逐条回 PDF 误设为默认主流程
3. 没有 grounding resolver 去解析 chunk_text、source_file、item_key、file_id、kb_id、markdown_path、parsed_text_path、page_map 等字段
4. 无法区分 full_markdown_grounding、chunk_only_grounding、page_mapped_grounding、pdf_fallback_required、unresolved_grounding
5. evidence_strength 和 grounding_status 混为一谈
6. 相邻格具证据可能被误升级为 strong_support
7. 权属信息无一手材料时可能被强行补注

---

## 二、目标流程修正版

### 2.1 ReferenceFootnote 标准流程（修正后）

```
1. 已写文章导入（A1）
2. claim / evidence need 拆解（A2-A3）
3. 反推检索方向，交给检索入库（A3.5-A4.5）
4. 检索入库完成 PDF 保存和 2.5 RAG 导库（外部）
5. ReferenceFootnote 消费 RAG response（A6-A6.5）
6. ★ grounding resolver 解析证据来源（A8.6 新增）
7. ★ Markdown/parsed text 核查（A8.7 新增）
8. ★ 必要时 PDF fallback 核验（A8.8 新增）
9. 脚注方案、参考文献表、风险清单和交付包（A9-A11）
```

### 2.2 grounding resolver 解析字段

grounding resolver 必须从 RAG response + 检索入库 handoff 中解析以下字段：

| 字段 | 来源 | 用途 |
|------|------|------|
| chunk_text | RAG response.results[].candidates[].snippet | 快速定位 |
| source_file | RAG response 或 intake completion | 原始文件名 |
| file_id | RAG response metadata | 文件唯一标识 |
| item_key | intake completion.results[].zotero_id 或 ref_id | 条目标识 |
| kb_id | intake completion.kb_routing.target_kb | 知识库标识 |
| markdown_path | intake completion 或 artifact-resolver-map.json | MinerU 解析输出路径 |
| parsed_text_path | intake completion 或 artifact-resolver-map.json | 等价解析文本路径 |
| page_map | intake completion 或 artifact-resolver-map.json | chunk→页码映射 |
| artifact-resolver-map.json | 检索入库 handoff 目录 | 全局解析产物索引 |
| batch manifest / source metadata | intake completion | 批次元数据 |

### 2.3 grounding 决策树

```
有 chunk_text?
├─ 否 → unresolved_grounding
└─ 是
   ├─ 有 markdown_path 或 parsed_text_path?
   │  ├─ 是 → full_markdown_grounding
   │  └─ 否
   │     ├─ 有 page_map 且可靠?
   │     │  ├─ 是 → page_mapped_grounding
   │     │  └─ 否 → chunk_only_grounding
   └─ 有 OCR/版面/表格/图片/脚注/公式/竖排风险?
      └─ 是 → pdf_fallback_required（覆盖上层结果）
```

---

## 三、阶段机修复

### 3.1 修正版阶段（A8-A11）

| 阶段 | 名称 | 输入 | 输出 | 门禁 |
|------|------|------|------|------|
| A8 | 补库完成应用 | round2 completion response | intake-status-round2.json | 可选 |
| A8.5 | post-ingestion RAG reverse lookup | intake completion + citation needs | rag-calls/*.json | RAG call package prepared |
| **A8.6** | **grounding resolver** | RAG response + intake completion + artifact-resolver-map | **grounding-resolution.json** | 每条证据有 grounding_status |
| **A8.7** | **Markdown/parsed text 核查** | grounding-resolution + markdown/parsed files | **markdown-verification.json** | full_markdown_grounding 条目已核上下文 |
| **A8.8** | **PDF fallback 核验** | grounding-resolution（pdf_fallback_required 条目） | **pdf-fallback-verification.json** | 仅 fallback 条目，非默认流程 |
| A9 | 脚注与参考文献初步方案 | evidence-map + grounding-resolution | insertion-plan.json | 同时报告 evidence_strength + grounding_status |
| A10 | citation quality gate | insertion plan + grounding | quality-report.json | 按 grounding_status 和 evidence_strength 双门禁 |
| A11 | 最终交付包 | all prior outputs | delivery/ | 包含 grounding-resolution.json |

### 3.2 A8.6 grounding resolver 详细规格

输入：
- `state/evidence-interpretations/*.json`（RAG response 解释结果）
- `state/intake-status.json`（检索入库完成回执）
- `state/intake-status-round2.json`（可选）
- `state/artifact-resolver-map.json`（可选，检索入库 handoff 产物索引）

输出：`state/grounding-resolution.json`

```json
{
  "batch_id": "...",
  "resolved_items": [
    {
      "claim_id": "...",
      "candidate_id": "...",
      "grounding_status": "full_markdown_grounding",
      "resolved_source": {
        "chunk_text": "...",
        "source_file": "example.pdf",
        "item_key": "zotero-ABC123",
        "file_id": "file-001",
        "kb_id": "A",
        "markdown_path": "/parsed/example.md",
        "parsed_text_path": null,
        "page_map": {"chunk_start": 3, "chunk_end": 3, "page": 42},
        "pdf_path": "/pdfs/example.pdf"
      },
      "risk_flags": [],
      "fallback_reason": null
    }
  ],
  "summary": {
    "full_markdown_grounding": 12,
    "page_mapped_grounding": 3,
    "chunk_only_grounding": 2,
    "pdf_fallback_required": 1,
    "unresolved_grounding": 0
  }
}
```

### 3.3 A8.7 Markdown/parsed text 核查

- 仅对 grounding_status 为 full_markdown_grounding 的条目执行
- 核查内容：上下文完整性、真实性（chunk 是否截断/拼接）、契合性（claim 与 Markdown 段落语义匹配）
- 输出 `state/markdown-verification.json`，标记 verified / context_mismatch / truncated / spliced
- 这是默认核查层，不是 fallback

### 3.4 A8.8 PDF fallback 核验

- 仅对 grounding_status 为 pdf_fallback_required 的条目执行
- 触发条件：page_map 缺失/冲突、OCR/版面异常、表格/图片/脚注/公式/竖排不可靠、最终投稿需目视页码
- **这是 fallback，不是默认主流程**
- 输出 `state/pdf-fallback-verification.json`

---

## 四、文件级修改计划

### 4.1 SKILL.md

- 工作流部分增加 A8.6/A8.7/A8.8 阶段描述
- 质量原则部分增加 grounding_status 相关规则
- 硬边界部分增加：不得把"没有显式 Markdown 导出"误判为"RAG 未解析"
- 何时读取参考文件部分增加 `docs/grounding-protocol.md`

### 4.2 docs/rag-protocol.md

- Response 部分增加 candidate 可选字段：source_file、file_id、markdown_path、parsed_text_path、page_map
- Evidence Rules 部分增加：chunk_text 是定位层不是最终证据门禁；Markdown/parsed text 是默认核查层
- 增加 grounding_status 与 RAG response 的关系说明

### 4.3 docs/handoff-protocol.md

- From 检索入库部分增加 results[].markdown_path、results[].parsed_text_path、results[].page_map 字段
- 增加 artifact-resolver-map.json 协议说明
- handoff_to_writing.json 增加 grounding_resolution_summary 字段

### 4.4 docs/collaboration-flow.md

- Flow 步骤 9 后增加 grounding resolution 步骤
- 增加 resolve-grounding.py 的调用说明
- 增加 validate-markdown-grounding.py 的调用说明（可选）
- 明确 PDF fallback 只在必要时触发

### 4.5 docs/evidence-classification.md

- 增加 grounding_status 与 evidence_strength 的正交关系说明
- 增加 analogy_only 强度等级
- 明确：相邻格具只能 analogy_only 或 background_only
- 明确：权属信息没有一手材料时不得强行补注
- 明确：RAG chunk 命中不能自动升级为 strong_support

### 4.6 docs/quality-gates.md

- 增加 grounding 相关门禁规则
- 增加：不得把"没有显式 Markdown 导出"误判为"RAG 未解析"
- 增加：不得把"逐条回 PDF"作为默认第一核查层
- 增加：final citation plan 必须同时报告 evidence_strength 与 grounding_status

### 4.7 docs/state-machine.md

- 在 A8.5 后增加 A8.6、A8.7、A8.8 行
- 更新 A9 输入为 evidence-map + grounding-resolution
- 更新 A10 门禁为双维度（evidence_strength + grounding_status）
- 更新 A11 输出包含 grounding-resolution.json

### 4.8 新增 docs/grounding-protocol.md

全新文档，内容：
- grounding_status 五级定义
- 核查层级优先级
- grounding 决策树
- artifact-resolver-map.json schema
- Markdown 核查规格
- PDF fallback 触发条件
- grounding_status 与 evidence_strength 正交矩阵

### 4.9 README.md

- 文档导航增加 `docs/grounding-protocol.md`
- 版本说明更新为 0.5.1-dev

### 4.10 RELEASE.md

- 增加 0.5.1-dev 发布说明
- staging/production 默认 blocked

### 4.11 CHANGELOG.md

- 增加 0.5.1-dev 条目，列出所有 grounding 修复内容

### 4.12 templates/ 新增

- `templates/grounding-resolution.template.json`
- `templates/markdown-verification.template.json`
- `templates/pdf-fallback-verification.template.json`
- `templates/artifact-resolver-map.template.json`

### 4.13 agents/rag-interpreter.md

- 增加 grounding resolver 职责说明
- 明确 chunk_text 是定位层，Markdown 是核查层

---

## 五、脚本修改计划

### 5.1 新增 scripts/resolve-grounding.py

核心新增脚本。

输入：
- `--task-dir`（任务目录）

读取：
- `state/evidence-interpretations/*.json`
- `state/intake-status.json`
- `state/intake-status-round2.json`（可选）
- `state/artifact-resolver-map.json`（可选）

输出：
- `state/grounding-resolution.json`

逻辑：
1. 遍历每条 evidence interpretation 的 candidates
2. 从 intake-status 中匹配 claim_id → results[] → 提取 source_file、zotero_id、kb_routing、import_status
3. 从 artifact-resolver-map.json 中查找 markdown_path、parsed_text_path、page_map
4. 如果 intake completion 自带 markdown_path/parsed_text_path/page_map，优先使用
5. 按决策树判定 grounding_status
6. 检查 risk_flags 中是否有 ocr_uncertain、表格/图片/竖排等，若有则覆盖为 pdf_fallback_required
7. 输出每条证据的完整 resolved_source 和 grounding_status
8. 输出 summary 统计

### 5.2 修改 scripts/validate-rag-response.py

- 在 candidate 解析中增加对 source_file、file_id、markdown_path、parsed_text_path、page_map 的提取（可选字段，不报错）
- 将这些字段透传到 evidence-interpretations 输出中
- 不再因为缺少这些字段而报 error（它们是可选的）

### 5.3 修改 scripts/build-evidence-map.py

- evidence-map 条目增加 grounding_status 字段（从 grounding-resolution.json 读取，如果存在）
- 如果 grounding-resolution.json 不存在，grounding_status 默认为 "not_resolved"
- summary 增加 grounding 统计

### 5.4 修改 scripts/plan-footnotes.py

- insertion 条目增加 grounding_status 字段
- evidence_basis 增加 grounding_status 和 resolved_source
- 对 chunk_only_grounding 条目自动设置 requires_rewrite=true 并附带 rewrite_suggestion

### 5.5 修改 scripts/validate-citation-plan.py

- 增加 grounding 相关门禁：
  - unresolved_grounding 条目不得进入 strong_support insertion（blocking）
  - chunk_only_grounding + strong_support 降级为 warning
  - pdf_fallback_required 条目必须有 pdf-fallback-verification 结果或进入 human_review
- metrics 增加 grounding_coverage 统计
- quality-report.json 增加 grounding_summary

### 5.6 修改 scripts/build-delivery.py

- delivery/ 增加 grounding-resolution.json 复制
- delivery/ 增加 markdown-verification.json 复制（如果存在）
- delivery/ 增加 pdf-fallback-verification.json 复制（如果存在）
- handoff_to_writing.json 增加 grounding_resolution_summary
- human_review_needed.json 增加 grounding_unresolved 和 pdf_fallback_pending

### 5.7 可选新增 scripts/validate-markdown-grounding.py

- 输入：grounding-resolution.json + markdown 文件路径
- 对 full_markdown_grounding 条目：读取 markdown_path，验证 chunk_text 是否存在于 Markdown 中
- 输出：markdown-verification.json
- 离线模式下：如果 markdown_path 不可访问，标记 markdown_not_accessible 而非报错

### 5.8 可选新增 scripts/validate-pdf-page-grounding.py

- **必须说明：这是 fallback，不是默认主流程**
- 输入：grounding-resolution.json（仅 pdf_fallback_required 条目）
- 输出：pdf-fallback-verification.json
- 离线模式下：生成验证请求包，不执行真实 PDF 读取
- 触发条件文档化：page_map 缺失/冲突、OCR/版面异常、表格/图片/脚注/公式/竖排不可靠

### 5.9 修改 scripts/reflib.py

- 增加 GROUNDING_STATUSES 常量集合
- 增加 resolve_grounding_status() 辅助函数
- 增加 LAYOUT_RISK_TRIGGERS 常量（ocr_uncertain、vertical_text、table_complex、figure_embedded、formula_inline、footnote_in_source）
- SUPPORT_STRENGTHS 增加 "analogy_only"

### 5.10 修改 scripts/build-authenticity-verification-request.py

- 默认核查层改为 Markdown/parsed text，不再默认要求 PDF
- 只有 pdf_fallback_required 条目才生成 PDF 核验请求
- checks_required[] 区分 markdown_check 和 pdf_check

---

## 六、grounding_status 规范

### 6.1 五级定义

| grounding_status | 条件 | 含义 |
|------------------|------|------|
| `full_markdown_grounding` | 有 chunk_text，且能定位到 markdown_path 或 parsed_text_path | 最可靠：可核上下文、真实性、契合性 |
| `page_mapped_grounding` | 有 chunk_text，且有可靠 page_map（无冲突） | 可靠：有页码连接但无全文核查 |
| `chunk_only_grounding` | 有 chunk_text，但无 markdown_path / parsed_text_path / page_map | 可用但受限：只能做初步定位 |
| `pdf_fallback_required` | chunk 或 Markdown 存在，但页码映射缺失/冲突，或 OCR/版面/表格/图片/脚注/公式/竖排风险需要 PDF 兜底 | 需要 PDF 目视核验 |
| `unresolved_grounding` | 无法从 RAG response 和 handoff 中解析可靠来源 | 不可用：必须进入人工复核 |

### 6.2 grounding_status 与 evidence_strength 正交

grounding_status 描述"来源可靠性"，evidence_strength 描述"支撑强度"。两者独立：

- strong_support + full_markdown_grounding = 最佳，可直接引用
- strong_support + chunk_only_grounding = 强度够但来源不够可靠，需标记风险
- partial_support + full_markdown_grounding = 来源可靠但支撑不完整，需限定表述
- strong_support + unresolved_grounding = 不可引用，必须人工复核

### 6.3 grounding_status 对流程的影响

| grounding_status | 允许的最高操作 |
|------------------|----------------|
| full_markdown_grounding | 直接进入 insertion plan，可标记 verified |
| page_mapped_grounding | 进入 insertion plan，附带页码但需标记 markdown_not_verified |
| chunk_only_grounding | 进入 insertion plan 但 requires_rewrite=true，附带 grounding_warning |
| pdf_fallback_required | 进入 insertion plan 但必须有 pdf-fallback-verification 或进入 human_review |
| unresolved_grounding | 不得进入 insertion plan，必须进入 human_review 或 gap handoff |

---

## 七、证据强度规范

### 7.1 强度等级（修正后）

| 强度 | 含义 | 引用用途 |
|------|------|----------|
| `strong_support` | 直接支撑 claim | 可引用（无 blocking risk 时） |
| `partial_support` | 部分支撑 | 需限定表述或改写 |
| `analogy_only` | 仅类比关系 | 只能作为旁证，不能替代直接实证 |
| `background_only` | 仅提供背景 | 背景引用，不能支撑具体论断 |
| `no_support_found` | 无候选支撑 | 进入 gap handoff 或人工复核 |
| `conflict` | 与 claim 矛盾 | 不能作为支撑；可作为反对观点 |

### 7.2 关键约束

1. **相邻格具只能 analogy_only 或 background_only**，不能替代书道格直接实证
2. **权属信息没有一手材料时不得强行补注**
3. **RAG chunk 命中不能自动升级为 strong_support**——必须经过 grounding resolver 和上下文核查
4. **Markdown/parsed text 可核上下文真实性契合性，但不能在页码映射不清时替代 PDF 页码**
5. analogy_only 条目的 insertion plan 必须标记 `source_role: "旁证类比"` 且 `requires_rewrite: true`

---

## 八、fixture 要求

### 8.1 新增或修复的离线 fixture

| # | fixture 名称 | 测试目标 |
|---|-------------|----------|
| 1 | `grounding-full-markdown-path` | 有 markdown_path 的 RAG response → full_markdown_grounding |
| 2 | `grounding-chunk-only` | 无 markdown_path 但有 chunk_text → chunk_only_grounding |
| 3 | `grounding-parsed-text-path` | 有 parsed_text_path → full_markdown_grounding |
| 4 | `grounding-page-map-reliable` | 有 page_map 且页码可靠 → page_mapped_grounding |
| 5 | `grounding-page-map-conflict` | page_map 冲突 → pdf_fallback_required |
| 6 | `grounding-source-file-garbled-itemkey-ok` | source_file 文件名乱码但 item_key 可解析 |
| 7 | `grounding-vertical-text-pdf-fallback` | 竖排旧刊 chunk 可读但需要 PDF fallback |
| 8 | `grounding-table-evidence-fallback` | 智能评价论文表格证据需要 Markdown 表格或 PDF fallback |
| 9 | `no-ownership-primary-no-force-insert` | 无权属一手材料，不得补注 |
| 10 | `adjacent-grid-analogy-only` | 相邻格具证据只能类比，不得强证据化 |

### 8.2 fixture 结构

每个 fixture 需要：
- `tests/fixtures/scenarios/<name>/input/` — 输入文件（RAG response、intake-status、artifact-resolver-map 等）
- `tests/fixtures/scenarios/<name>/expected/` — 期望输出（grounding-resolution.json 等）
- `tests/fixtures/scenarios/<name>/config.json` — fixture 元数据和断言规则

### 8.3 fixture-list.json 更新

fixture-list.json 从 41 个扩展到 51 个（+10 个 grounding fixtures）。

---

## 九、质量门禁

### 9.1 新增门禁规则

| 规则 | 类型 | 说明 |
|------|------|------|
| 不得把"没有显式 Markdown 导出"误判为"RAG 未解析" | blocking | chunk_text 存在即表示 RAG 已解析 |
| 不得把"逐条回 PDF"作为默认第一核查层 | blocking | PDF 是 fallback，Markdown 是默认 |
| RAG chunk 是定位层，不是最终证据门禁 | warning | chunk 命中不等于 strong_support |
| Markdown/parsed text 是默认上下文核查层 | info | 有 markdown_path 时必须优先使用 |
| page_map 是页码连接优先层 | info | 有 page_map 时优先于 PDF 目视 |
| PDF 是 fallback 和最终目视核验层 | info | 只在必要时使用 |
| final citation plan 必须同时报告 evidence_strength 与 grounding_status | blocking | quality-report.json 必须包含双维度 |
| unresolved_grounding 不得进入 strong_support insertion | blocking | 必须人工复核 |
| chunk_only_grounding + strong_support 需降级 warning | warning | 来源不够可靠 |

### 9.2 风险清单必须包含

- 权属信息缺一手材料
- 教学实证缺直接观察/实验数据
- 政策原文缺官方文本
- 页码缺失（page_missing）
- Markdown 缺失（markdown_not_available）
- page_map 冲突（page_map_conflict）
- OCR 异常（ocr_uncertain）
- 竖排/表格/图片/公式/脚注版面风险

---

## 十、版本与发布建议

### 10.1 版本号

**0.5.1-dev**

理由：这是流程语义和 grounding 修复，不是全新功能大版本。0.5.0-dev 的 retrieval-first 架构不变，只是补充了 grounding resolver 层和修正了核查层级理解。

### 10.2 发布状态

- staging: **blocked**
- production: **blocked**
- 只有 Codex 完成修复、本地离线测试通过、Claude 二次审查通过后，才允许发布

### 10.3 VERSION 文件

```
0.5.1-dev
```

---

## 十一、Codex 执行清单

### TODO（按顺序执行）

```
□ 1. 读本规划报告，确认理解所有修改点
□ 2. 修改 docs/
   □ 2.1 新增 docs/grounding-protocol.md
   □ 2.2 修改 docs/state-machine.md（增加 A8.6/A8.7/A8.8）
   □ 2.3 修改 docs/rag-protocol.md（增加 grounding 字段）
   □ 2.4 修改 docs/handoff-protocol.md（增加 markdown_path/parsed_text_path/page_map/artifact-resolver-map）
   □ 2.5 修改 docs/collaboration-flow.md（增加 grounding 步骤）
   □ 2.6 修改 docs/evidence-classification.md（增加 analogy_only、正交关系、约束）
   □ 2.7 修改 docs/quality-gates.md（增加 grounding 门禁）
□ 3. 修改 scripts/
   □ 3.1 修改 scripts/reflib.py（增加 GROUNDING_STATUSES、resolve_grounding_status、LAYOUT_RISK_TRIGGERS、analogy_only）
   □ 3.2 新增 scripts/resolve-grounding.py
   □ 3.3 修改 scripts/validate-rag-response.py（透传 grounding 字段）
   □ 3.4 修改 scripts/build-evidence-map.py（增加 grounding_status）
   □ 3.5 修改 scripts/plan-footnotes.py（增加 grounding_status 到 insertion）
   □ 3.6 修改 scripts/validate-citation-plan.py（增加 grounding 门禁）
   □ 3.7 修改 scripts/build-delivery.py（增加 grounding 产物复制）
   □ 3.8 修改 scripts/build-authenticity-verification-request.py（默认 Markdown 核查，PDF 仅 fallback）
   □ 3.9 可选新增 scripts/validate-markdown-grounding.py
   □ 3.10 可选新增 scripts/validate-pdf-page-grounding.py（标注为 fallback）
□ 4. 新增 templates/
   □ 4.1 templates/grounding-resolution.template.json
   □ 4.2 templates/markdown-verification.template.json
   □ 4.3 templates/pdf-fallback-verification.template.json
   □ 4.4 templates/artifact-resolver-map.template.json
□ 5. 新增 fixtures/
   □ 5.1-5.10 按第八节列表创建 10 个 fixture
   □ 5.11 更新 tests/fixtures/scenarios/fixture-list.json
□ 6. 修改顶层文件
   □ 6.1 SKILL.md（工作流、质量原则、硬边界）
   □ 6.2 README.md（导航）
   □ 6.3 CHANGELOG.md（0.5.1-dev 条目）
   □ 6.4 RELEASE.md（发布说明）
   □ 6.5 VERSION（改为 0.5.1-dev）
   □ 6.6 agents/rag-interpreter.md（grounding 职责）
□ 7. 跑结构校验
   □ python3 scripts/verify-structure.py --target reference-footnote
□ 8. 跑 offline fixtures
   □ python3 tests/run-fixtures.py --all
   □ 确认 51 个 fixture 全部通过
□ 9. 跑 local gate
   □ python3 scripts/run-local-gate.py --pre-review
□ 10. 生成 Claude 发布前审查提示词
   □ 写入 .handoff/claude/2026-05-20-pre-release-review-prompt.md
□ 11. 停在 Claude 审查前，不自行发布
```

---

## 十二、发布前审查清单

Claude 二次审查应检查以下内容：

### 12.1 语义正确性

- [ ] grounding_status 五级定义是否正确实现
- [ ] 决策树逻辑是否与规划一致
- [ ] "没有显式 Markdown 导出"不再被误判为"RAG 未解析"
- [ ] "逐条回 PDF"不再是默认第一核查层
- [ ] Markdown/parsed text 是默认核查层
- [ ] PDF 只在 fallback 条件下触发

### 12.2 阶段机完整性

- [ ] A8.6/A8.7/A8.8 在 state-machine.md 中正确定义
- [ ] A9 输入包含 grounding-resolution.json
- [ ] A10 门禁包含 grounding_status 维度
- [ ] A11 交付包包含 grounding 产物

### 12.3 脚本正确性

- [ ] resolve-grounding.py 能正确解析所有 fixture
- [ ] validate-rag-response.py 透传 grounding 字段不报错
- [ ] build-evidence-map.py 正确读取 grounding-resolution.json
- [ ] plan-footnotes.py 正确附加 grounding_status
- [ ] validate-citation-plan.py 正确执行 grounding 门禁
- [ ] build-delivery.py 正确复制 grounding 产物

### 12.4 fixture 覆盖

- [ ] 10 个新 fixture 全部通过
- [ ] 原有 41 个 fixture 无回归
- [ ] fixture-list.json 更新为 51 个

### 12.5 证据强度约束

- [ ] analogy_only 正确实现
- [ ] 相邻格具不能升级为 strong_support
- [ ] 权属无一手材料不补注
- [ ] RAG chunk 命中不自动升级

### 12.6 文档一致性

- [ ] SKILL.md、docs/、agents/ 三处描述一致
- [ ] CHANGELOG.md 条目完整
- [ ] README.md 导航正确
- [ ] 所有新增 template 有对应文档说明

### 12.7 边界安全

- [ ] 不执行真实 PDF 读取
- [ ] 不执行真实 Markdown 文件读取（离线模式）
- [ ] 不探测外部服务
- [ ] artifact-resolver-map.json 是可选输入，缺失时优雅降级

### 12.8 版本与发布

- [ ] VERSION = 0.5.1-dev
- [ ] staging = blocked
- [ ] production = blocked
- [ ] git worktree clean
- [ ] 无未提交的临时文件

---

## 附录 A：artifact-resolver-map.json schema

```json
{
  "protocol_version": "1.0",
  "generated_by": "检索入库",
  "batch_id": "...",
  "items": [
    {
      "item_key": "zotero-ABC123",
      "source_file": "example.pdf",
      "file_id": "file-001",
      "kb_id": "A",
      "markdown_path": "/parsed/example.md",
      "parsed_text_path": null,
      "page_map": [
        {"chunk_id": "chunk-001", "chunk_start_char": 0, "chunk_end_char": 512, "page": 1},
        {"chunk_id": "chunk-002", "chunk_start_char": 513, "chunk_end_char": 1024, "page": 2}
      ],
      "pdf_path": "/pdfs/example.pdf",
      "parse_method": "mineru",
      "parse_quality": "high",
      "layout_risks": []
    }
  ]
}
```

## 附录 B：grounding 与现有 risk_flags 的关系

| 现有 risk_flag | grounding 影响 |
|----------------|----------------|
| page_missing | 若无 page_map → chunk_only_grounding；若有 page_map 冲突 → pdf_fallback_required |
| ocr_uncertain | → pdf_fallback_required |
| pdf_rag_conflict | → pdf_fallback_required |
| secondhand_citation | 不影响 grounding_status，但影响 evidence_strength |
| concept_approximate | 不影响 grounding_status，但影响 evidence_strength |
| temporal_mismatch | 不影响 grounding_status |
| discipline_cross | 不影响 grounding_status |
| translation_gap | 不影响 grounding_status |

## 附录 C：新增 layout_risk_triggers

以下 risk 触发 pdf_fallback_required：

- `ocr_uncertain`
- `vertical_text`（竖排）
- `table_complex`（复杂表格）
- `figure_embedded`（图片内嵌文字）
- `formula_inline`（行内公式）
- `footnote_in_source`（原文脚注区域）
- `page_map_conflict`（页码映射冲突）
- `multi_column_layout`（多栏排版）

---

*规划完成。等待 Codex 执行。*
