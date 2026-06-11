# Footnote Thinking Protocol

版本：0.6.0-dev

## 定位

S66-S68 是 RAG 证据与脚注候选池之间的必经思考层。RAG chunk 只提供材料，不能直接成为脚注；脚注必须由 thinking layer 判断正文是否存在“文中未尽而必要解释”，再生成独立可读的说明性文字。

## S66 请求

`footnote-thinking-request.json` 按全文顺序排列，每个 item 只对应一个 claim 或一个小段。每条必须包含：

- `body_context`：目标句、前后文、段落文本。
- `claim_metadata`：claim 类型、need level、citation type。
- `rag_evidence`：support strength、chunk text、chunk id、grounding status、source ref id。
- `known_risks`：RAG、grounding、材料风险。

## S67 结果

`footnote-thinking-result.json` 的每条结果必须给出 `decision`：

- `no_note`：正文已足够或该处不应脚注。
- `footnote_needed`：确有必要脚注。
- `reference_only`：只需要参考文献消费。
- `rewrite_needed`：正文需要改写，只进入风险建议。
- `human_review`：自动判断不足。

`footnote_needed` 必须包含 `proposed_note_text`、`footnote_type`、`evidence_used`、`why_not_reference_only`、`why_not_body_rewrite`。

## S68 验证

验证层拒绝以下内容：

- 空脚注、过短或过长脚注。
- 参考文献格式、作者题名出处页码组合、参考文献编号。
- “只能说明”“不能证明”“仍需验证”“属于类比判断”等 AI 防御式表述。
- “支撑本文”“印证本文”“可作为依据”等证据关系话术。
- 无 RAG chunk 或 grounding trace 的脚注。
- 未说明为什么不是 reference only 或 body rewrite 的脚注。

通过验证的 `validated_footnotes` 才能进入 `footnote-candidate-pool.json`。
