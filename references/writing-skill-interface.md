# 正文写作接口参考

本文件说明 ReferenceFootnote 如何把补注结果交给 `正文写作` 或人工编辑。ReferenceFootnote 不生成正文、不直接改写文章、不运行写作池、推进池或 mimo。

## 正文写作职责边界

`正文写作` 只负责正式第三步：

- 第一大轮正文生成、强终审和整改计划。
- 第二大轮 `R2-A1 / R2-A2 / R2-A5` 来源治理。
- 第二大轮正文修订、来源绑定、终审闭环和最终交付包。

`R2-A3 / R2-A4` 的真实补检、Zotero 保存、PDF 获取和增量导库属于 `检索入库`。

## Writer 可消费字段

ReferenceFootnote 的 `handoff_to_writing.json` 每条 insertion 应包含：

- `claim_id`
- `claim_type`
- `need_level`
- `support_strength`
- `risks`
- `evidence_type`
- `source_role`
- `consumption_depth_suggestion`
- `gbt7714_footnote`
- `requires_rewrite`
- `rewrite_suggestion`
- `target_location`
- `source_ref_id`

这些字段用于 writer 的来源绑定、引用卫生扫描、论断强度治理和最终交付包整理。

## 证据类型体系

| Writer 证据类型 | 含义 | 对补注的影响 |
| --- | --- | --- |
| 师承证据 | 直接证明授受、交往或影响渠道 | 可支持师承/影响类强关系 |
| 文本证据 | 原典、文本细读、版本差异和概念用法 | 可支持相近、相通、文本呼应 |
| 后设归纳 | 二手研究、综述和学术史判断 | 支持学术史定位，不宜直接支撑强事实链 |
| 经验材料 | 数据、案例、实证研究 | 支持事实或政策效果判断 |
| 一手材料 | 法条、判例、档案、原始数据 | 支持事实和制度描述 |

ReferenceFootnote 必须把证据类型传给 writer，不能只传文献标题。

## 论断类型与可写强度

| 论断类型 | 最低主证据 | 可写强度 |
| --- | --- | --- |
| 师承 / 授受 | 师承证据 | 可写明确关系 |
| 影响 / 深刻影响 | 师承证据 + 文本证据 | 否则应降为审慎表述 |
| 相通 / 相近 | 文本证据 | 可写审慎判断 |
| 一脉相承 / 理论承续 | 师承证据 + 文本证据 + 后设归纳 | 缺任一层需补证、改题或降强度 |
| 学界常见看法 | 后设归纳 | 只宜写为学术史定位 |
| 强机制链 | 文本证据或经验材料 + 明确中介链 | 不得只靠后设归纳强写 |

## 来源角色

`source_role` 建议使用以下枚举：

- 理论锚点
- 概念界定
- 学术史定位
- 关键争议
- 材料依据
- 方法参照
- 旁证补充
- 风险限定

## 来源消费深度

- `深度消费`：适合进入正文论证骨架，应有明确页码、片段和较高支撑强度。
- `浅要参考`：适合作为背景、旁证或风险限定，不应承载强 claim。

## Round2 来源治理映射

ReferenceFootnote 的高风险无据句和 no-support critical claim 可进入 writer 的 `R2-A1` gap 分类：

- `gap-routing-table.md`：记录 `gap_id`、claim、source_requirement、source_direction、priority。
- `round2-search-plan.md`：把 `需补充来源` 的 gap 转成回流检索计划。
- `round2-source-readiness-report.md`：回流后确认来源就绪率和是否可进入修订。

ReferenceFootnote 输出的 `search_intake_request` 可以作为 `round2-search-plan.md` 的结构化素材，但不能伪装成真实检索完成。

## Writer 侧扫描兼容

ReferenceFootnote 不运行 writer 扫描脚本，但输出应便于后续兼容：

- `scan-citation-hygiene.py`：需要 claim、脚注、风险、页码和引用格式信息。
- `scan-critical-claim-citations.py`：需要 critical/important claim 的支撑状态。
- `validate-gbt7714-bibliography.py`：需要 GB/T 7714 脚注或参考文献格式字段。

## Annotation Purpose Ledger

ReferenceFootnote 应区分“脚注用于支撑 claim”与“参考文献仅作背景”。`background_only` 和 `partial_support` 不得被写成 direct support；必要时进入 writer 的改写建议或人工复核清单。
