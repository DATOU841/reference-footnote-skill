# 参考文献补注 / ReferenceFootnote 公开介绍

`参考文献补注 / ReferenceFootnote` 是一个面向已完成初稿的学术文章辅助 skill。它不负责从零写论文，也不替代正文写作，而是专门处理一个高频、细碎且风险较高的环节：为既有文章系统诊断引用需求，寻找可支撑证据，规划脚注和参考文献补充方案，并把仍然缺证据的位置整理成交接任务。

## 它解决什么问题

很多文章在正文已经基本成型后，仍会遇到这些问题：

- 哪些句子必须补引用，哪些只是建议补引用？
- RAG 文献库里已有的材料能否真正支撑某个判断？
- 哪些 RAG 命中只是背景材料，不能直接作为脚注？
- 哪些 claim 没有证据，应该交给检索入库继续补库？
- 哪些句子属于作者原创观点、过渡句或常识句，不应该强行补注？
- 最后交给正文写作或人工处理时，如何形成清晰、可执行的补注任务包？

ReferenceFootnote 的目标不是“自动塞满参考文献”，而是建立一套可审查、可追踪、可交接的证据补注流程。

## 核心能力

### 1. 已写文章导入

对已经写好的文章进行结构化导入，识别标题、章节、段落、句子、已有引用和参考文献信息，为后续逐句分析建立基础数据。

### 2. Claim / Evidence Need 拆解

将正文中的句子拆解为可验证的 claim 单元，并区分事实陈述、理论主张、政策判断、学术判断、作者观点、常识句、过渡句等类型。

### 3. 引用需求诊断

判断每个 claim 是否需要引用，以及需要什么类型的引用。系统会区分：

- critical：必须补引用，否则存在明显学术风险
- important：强烈建议补引用
- recommended：建议补引用
- optional：可补可不补
- not_needed：不需要引用
- already_cited：已有引用但需要核验

### 4. RAG 文献反查协议

ReferenceFootnote 会把引用需求转化为结构化 RAG 反查请求。请求不仅包含关键词，还包括原句、概念、引用意图、章节上下文、学科背景和期望文献类型。

RAG 返回结果不会被直接采信。系统会进一步判断候选文献属于：

- strong_support：明确支撑
- partial_support：部分支撑
- background_only：仅提供背景
- conflict：与 claim 冲突
- no_support：未找到支撑

同时标记页码缺失、OCR 不确定、二手转述、概念近似匹配、时效性不匹配、跨学科语境差异等风险。

### 5. 证据映射表

为全文生成 evidence map，汇总每个 claim 的证据状态、支撑强度、候选文献、风险说明和缺口情况。这个映射表可以帮助作者或编辑快速判断文章的证据覆盖率。

### 6. 与“检索入库”的补库交接

对于 RAG 未能覆盖的关键缺口，ReferenceFootnote 会生成分批检索请求，交给 `检索入库` skill 处理。请求包含 claim 文本、关键词、作者线索、数据库建议、最低补库要求和理想补库目标。

补库请求会带上 `macro_round`、`gap_id`、`source_direction`、中英文关键词、作者线索、理论线索和目标知识库约束。第一大轮默认进入 B 库，第二大轮回流默认进入 C 库；回流必须是 gap 驱动补料，不是泛检或自由扩池。

ReferenceFootnote 本身不运行 CNKI、WoS、Zotero、PDF 获取或 RAG 导库。

### 7. 补库后二轮反查

0.5.0-dev 将该链条前移为 retrieval-first：先根据文章整体生成检索蓝图和初始文献库建设请求，待 `检索入库` 返回入库完成状态并通过质量验收后，再进行 RAG 反查。RAG 后仍无支撑的 critical/important claim 才进入二轮 gap 补库。

### 8. 脚注与参考文献补充计划

根据证据映射结果生成脚注插入计划。0.4.0-dev 明确规定：脚注是正文内容的必要补充，不是参考文献罗列。系统会先生成 15-25 个候选脚注，再删除空泛背景、重复来源、弱支撑、纯题录式内容和不必要说明，最终保留约 15 个真正有价值的脚注。

- 哪个句子后面应插入脚注
- 推荐使用哪篇文献
- 支撑的是哪一个 claim
- 支撑强度与置信度
- 脚注用途是补证、概念说明、制度背景、来源锚定还是对立观点
- 是否需要人工确认页码
- 是否建议改写原句
- 哪些位置不得强行补注

同时生成参考文献表补全建议，并把候选参考文献裁剪到约 25-30 篇重要文献，删除未消费、弱相关或重复来源。

### 8.5 真实性与契合性复核

脚注位置和文献确定后，ReferenceFootnote 会生成 Markdown/parsed text + RAG 复核请求，要求逐条检查文献是否真实存在、题录是否准确、RAG 片段是否能在 MinerU/MU Markdown 或等价解析文本中定位、脚注是否真正契合正文位置。PDF 不再作为默认核查层，只在页码映射冲突、OCR 不确定、表格图片竖排等复杂版式风险出现时作为 fallback。它本身不获取 PDF、不运行真实 RAG，只接收外部或人工给回的结构化核验结果，并把问题列入交付包。

### 9. 高风险清单与质量门禁

系统会输出高风险无据句、页码缺失引用、概念近似引用、证据冲突、仍需人工处理的 claim，并通过最终质量门禁检查 critical claim 覆盖率、高风险引用比例、页码缺失率、参考文献格式一致性等指标。

### 10. 最终交付包

最终输出可交给 `正文写作` skill 或人工处理的补注任务包，包括：

- 全文证据映射表
- 脚注插入计划
- 参考文献补全建议
- 质量报告
- 人工复核清单
- 交给正文写作的结构化任务包
- 本次补注变更摘要

交给 `正文写作` 的结构化任务包会附带证据类型、来源角色、建议消费深度、GB/T 7714 脚注字段、未闭合 critical claim 和既有参考文献合并状态，方便后续进入来源绑定、引用卫生扫描或人工复核。

## 阶段机

ReferenceFootnote 使用 A0 到 A11 的阶段机：

| 阶段 | 名称 | 目标 |
| --- | --- | --- |
| A0 | startup / boundary check | 检查运行环境和禁止动作边界 |
| A1 | article intake | 导入已写文章并解析结构 |
| A2 | claim segmentation | 拆解 claim 和 evidence need |
| A3 | citation-need diagnosis | 判断引用需求和引用类型 |
| A3.5 | search blueprint | 从文章反推检索方向和关键词 |
| A4 | initial library handoff | 生成初始文献库建设请求 |
| A5 | intake completion and quality gate | 接收入库完成状态并验收文献池质量 |
| A6 | RAG reverse lookup request | 在入库完成后构建 RAG 文献反查请求 |
| A6.6 | grounding resolution | 将 RAG chunk 对齐到 Markdown、parsed text、page map 或 PDF fallback |
| A7 | evidence map and gap handoff | 构建证据映射，并为剩余缺口生成二轮补库请求 |
| A8 | post-ingestion reverse lookup | 接收二轮入库完成状态并准备回流反查 |
| A9 | footnote/reference insertion plan | 生成脚注和参考文献补充计划 |
| A10 | final citation quality gate | 执行最终引文质量门禁 |
| A11 | delivery package | 构建最终补注交付包 |

## 不做什么

ReferenceFootnote 的边界很清楚：

- 不从零写论文
- 不替代 `正文写作`
- 不直接检索 CNKI 或 WoS
- 不直接操作 Zotero
- 不获取 PDF
- 不直接导入 RAG 库
- 不操作服务器生产环境
- 不给没有证据的句子伪造脚注
- 不对作者原创观点、常识句、过渡句强行补注

## 适用场景

- 已有文章初稿，需要系统补参考文献和脚注
- 文章已有部分参考文献，但需要核验证据是否真正支撑正文
- 需要把证据缺口交给检索入库团队或自动化流程
- 需要为正文写作阶段提供明确的脚注插入任务
- 需要在交付前形成 citation QA 和人工复核清单

## 当前版本状态

`0.5.1-dev` 是 retrieval-first + Markdown grounding 修正版。它先建设足量文献库，再做 RAG 反查，并把 RAG chunk 对齐到 MinerU/MU Markdown、parsed text、page map 或 PDF fallback；同时区分类比证据 `analogy_only`，避免把相邻格具或近似教学研究误当成直接支撑。它仍不直接运行真实检索、入库、PDF 获取或 RAG 查询。staging 和 production 默认保持 blocked。

这个版本适合用于展示 ReferenceFootnote 的工作流、协议边界和离线验证能力；正式文章补注和真实外部服务集成应在后续版本中逐步开放。
