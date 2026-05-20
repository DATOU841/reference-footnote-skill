# Writing Pool Review Protocol

版本：0.5.2-dev

## 定位

ReferenceFootnote 可以独立调用“写作池式审查”能力，但这不是 `正文写作` skill 的正式第三步，也不依赖 `03-writer`、guard、ledger、推进池或 mimo。

写作池审查只解决三类问题：

1. 注释是否放在全文正确位置。
2. 注释措辞是否和正文论证强度匹配。
3. 证据不足时是否应删除注释、移动注释，或把所在完整段落退回重写。

## 禁止事项

- 不从零写文章。
- 不替代检索、入库、RAG 或 PDF/MU 核查。
- 不把类比证据改写成直接证据。
- 不把一手权属缺失改写成已核实事实。
- 不抽句拼合正文；如需改正文，只能返回完整段落。

## 输入

`writing_pool_review_request` 至少包含：

- `article_id`
- `request_id`
- `execution_status: prepared_not_executed`
- `review_scope`
- `items`

每个 `item` 按全文顺序排列，包含：

- `order`
- `insertion_id`
- `claim_id`
- `paragraph_id`
- `sentence_id`
- `body_context`
- `current_note_text`
- `support_strength`
- `grounding_status`
- `known_risks`
- `references_consumed`
- `review_questions`

## 输出

写作池返回 `writing_pool_review_result`：

```json
{
  "status": "completed",
  "request_id": "writing-pool-review-01",
  "results": [
    {
      "insertion_id": "ins-001",
      "decision": "keep",
      "fit": "fits",
      "reason": "注释位置和证据边界匹配。",
      "revised_note_text": null,
      "new_target_location": null,
      "rewritten_paragraph": null,
      "risks": []
    }
  ]
}
```

允许的 `decision`：

- `keep`
- `revise_note`
- `move_note`
- `drop_note`
- `return_paragraph_for_rewrite`

## 门禁

- `drop_note` 和 `return_paragraph_for_rewrite` 必须进入最终交付风险清单。
- `move_note` 必须回写插入计划后重新跑位置一致性检查。
- `revise_note` 只能修改注释，不得改变正文论断。
- 若 `support_strength` 为 `analogy_only`，写作池不得输出会让读者理解为直接实证的注释。
- 若存在 `ownership_unverified`，写作池不得输出“已核实”口径。
