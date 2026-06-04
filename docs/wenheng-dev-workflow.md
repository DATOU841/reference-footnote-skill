# 参考文献补注接入文衡开发流程

版本：wenheng-dev-workflow-v1
skill：reference-footnote-skill
声明日期：2026-06-05

## 1. 协议对齐声明

`reference-footnote-skill` 自 `0.5.3-dev` 协议适配批次起接入文衡云枢 `wenheng-dev-workflow-v1`。后续开发、修复、审查、发布和跨 skill 协作必须遵守文衡统一的规划、执行、复盘、审查、发布和回写流程。

本文件只定义开发治理协议，不改变参考文献补注的诊断、RAG 解释、注释规划、质量门禁和交付行为。真实论文全文、正式补注任务材料、RAG 数据库、Zotero 数据库、PDF 正文、密钥、token、cookie 和浏览器 profile 不进入 Git 或文衡 fixtures。

## 2. Git 权威源与运行端同步

- Git 权威源：`DATOU841/reference-footnote-skill`
- 本地工作区：`/Users/a13497/Desktop/skill工作区/reference-footnote-skill`
- 运行端副本：`$CODEX_SKILLS/参考文献补注`（存在性以现场确认为准）
- 服务器部署路径：当前无登记

同步原则：

1. Git 权威源是唯一可信代码来源。
2. 运行端副本只能从已审查的 Git commit 或 tag 同步。
3. 禁止直接热修运行端副本后再反向覆盖 Git。
4. dirty 改动、临时交接文件和正式任务材料不得作为发布依据。
5. 发布、tag、push 或运行端同步必须等待 Claude Review 返回 `STATUS: PASS`。

## 3. 文衡开发流程

任何真实开发必须按以下顺序执行：

1. 检查文衡 open issue。
2. Claude Planning 写入指定 outputs 路径。
3. Codex 按 Planning 执行，只处理一个批次。
4. 第一轮实现后反思并记录问题。
5. 第二轮完善。
6. 生成 diff、终端输出、错误日志和本地门禁证据。
7. Claude Review，第一行必须是 `STATUS: PASS / PATCH / REBUILD`。
8. 只有 `STATUS: PASS` 后才允许 `git commit / tag / push`。
9. 发布后执行本仓库 release gate 或等价 `release:check`。
10. 发布反馈回写文衡台账。

规划前 issue 检查示例：

```bash
node /Users/a13497/Documents/Codex/2026-06-03/new-chat/work/scholarops-console/scripts/check-related-issues.mjs --module "reference-footnote-skill" --status open
```

## 4. 本批协议适配边界

当前批次只允许建立文衡开发流程文档和脱敏登记，不做深度自动化集成。

允许：

- 新增或维护 `docs/wenheng-dev-workflow.md`
- 在文衡 fixtures 中登记协议状态、批次状态和后续待办
- 运行离线结构检查、fixture 测试和本地门禁
- 生成 Claude Review 提示词和证据包

禁止：

- 修改补注核心逻辑脚本
- 修改 RAG 查询脚本或触发真实 RAG 查询
- 操作 Zotero
- 修改运行端副本
- 读取或写入正式任务材料
- 发布、部署或同步运行端，除非 Claude Review 已 PASS

## 5. 任务进度汇报规范

参考文献补注任务在文衡中应以脱敏任务记录登记。建议任务类型为 `citation_support`。

允许登记字段：

```json
{
  "taskId": "MAN-YYYYMMDD-XXX",
  "taskType": "citation_support",
  "status": "planned | in_progress | blocked | under_review | completed",
  "progress": "S20 citation diagnosis completed",
  "nextAction": "next sanitized action",
  "responsibleSkill": "参考文献补注",
  "collaborativeSkills": ["检索入库", "正文写作", "HSS RAG 平台"]
}
```

禁止登记：

- 真实论文全文
- 作者、机构、未脱敏题名
- 真实检索词、文献清单、RAG chunk、Zotero item 数据
- PDF 正文和页码截图
- 任务目录中的 draft、material、review、delivery 原文

建议进度节点：

- S20：补注需求诊断完成
- S40：检索入库请求已形成
- S50：RAG 反查状态已回收
- S70：注释规划完成
- S110：质量门禁完成
- S120：交付包完成

## 6. 错误复盘上报规范

以下问题应登记到文衡错误复盘入口：

- RAG executor 配置缺失或返回格式异常
- 检索入库 handoff 缺失、格式错误或未闭合
- 写作池审查交接失败
- 补注规划无法通过质量门禁
- 本地门禁、fixture 或结构检查失败
- 发布流程缺少 Claude Review 或证据包

建议 issue ID：

```text
issue_YYYYMMDD_reference-footnote_<short-name>
```

建议字段：

```json
{
  "issue_id": "issue_YYYYMMDD_reference-footnote_example",
  "found_phase": "planning | execution | review | post_release",
  "module": ["参考文献补注", "文衡协议适配"],
  "feature": "short feature name",
  "symptom": "sanitized symptom",
  "root_cause": "sanitized root cause",
  "severity": "low | medium | high | critical",
  "priority": "low | medium | high | critical",
  "status": "open | found_fixed_before_release | released",
  "related_batch": "batch id",
  "next_action": "sanitized next action"
}
```

错误复盘只记录开发症状和脱敏根因，不记录真实文章内容、真实文献内容、Zotero 数据、RAG chunk 或密钥。

## 7. 版本号协调规范

版本号由文衡批次登记和 skill 端 `VERSION` 文件共同约束。

当前阶段：

- 本协议文件适配不强制修改 `VERSION`
- 不自动发放版本号
- 不改 release 脚本
- 不改变现有 tag 策略

后续版本号深度集成批次应规划：

- 文衡 `version_registry.json` 中登记 skill 目标版本
- 本仓库 `VERSION` 与文衡登记一致性检查
- 发布前 release gate 校验版本登记
- 发布后回写 commit、tag 和 review 结果

## 8. 跨 skill 协作入口

参考文献补注不直接执行检索、Zotero、PDF 获取或正式 RAG 导库。跨 skill 协作必须通过结构化 handoff 或脱敏状态登记。

### 8.1 检索入库

适用场景：

- 形成检索计划
- 请求 CNKI/WoS 检索
- 请求 Zotero 保存
- 请求 PDF 获取和 RAG 导库
- 二轮补库

记录字段建议：

```json
{
  "from_skill": "reference-footnote-skill",
  "to_skill": "jiansuo-ruku-skill",
  "handoff_type": "initial_search | supplementary_search",
  "status": "pending | completed | blocked",
  "created_at": "ISO-8601",
  "completed_at": "ISO-8601 or null"
}
```

### 8.2 正文写作

适用场景：

- 注释位置审查
- 补注措辞审查
- 与正文论证功能的边界判断

参考文献补注只调用独立写作池式审查能力，不接管正文写作正式第三步状态。

### 8.3 文章润色

适用场景：

- 终稿润色前的引用完整性提示
- 润色后引文、注释和参考文献一致性复核

不得把真实润色稿全文写入文衡 fixtures。

### 8.4 HSS RAG 平台 / ScholarFlow

适用场景：

- RAG 反查状态记录
- RAG 失败复盘
- 入库质量边界确认

只登记脱敏状态，不登记真实 RAG 数据库内容、chunk、embedding、连接串或密钥。

## 9. RAG / Zotero / 文献材料边界

绝对不能进入 Git 或文衡 fixtures：

- 真实论文全文
- 正式补注任务目录中的 draft、material、review、delivery 原文
- RAG 数据库、向量库、索引、连接串和真实 executor 配置
- Zotero 数据库、PDF 缓存和完整文献数据
- PDF 正文
- CNKI/WoS 浏览器 profile、cookie、session
- `.env`、密钥、token、账号密码、服务器环境变量

允许进入 Git：

- 脱敏协议文档
- 模板文件
- 离线 fixtures
- 不含真实任务数据的测试脚本
- mock 配置或配置模板

允许进入文衡 fixtures：

- 脱敏任务状态
- 脱敏错误复盘
- 脱敏跨 skill handoff 状态
- 批次、版本、review 和发布元数据

## 10. 本地门禁和证据包

后续实现后建议运行：

```bash
python3 scripts/verify-structure.py --target reference-footnote
python3 scripts/startup.py
python3 tests/run-fixtures.py --all
python3 scripts/run-local-gate.py --pre-review
```

证据包应包含：

- `git diff HEAD`
- 本地门禁完整终端输出
- 错误日志，如有
- 新增文件清单
- Claude Review 提示词路径
- Claude Review 结果路径

本 skill 无前端，本批不需要浏览器截图。不需要真实任务运行证据。

## 11. Claude Review 要求

Review 第一行必须是：

```text
STATUS: PASS / PATCH / REBUILD
```

Review 必须判断：

- 是否只做 docs / fixtures 级适配
- 是否符合 `wenheng-dev-workflow-v1`
- 是否未触发真实补注任务
- 是否未触发真实 RAG 查询
- 是否未操作 Zotero
- 是否未修改运行端副本
- 是否未改变 S00-S120 工作流行为
- 证据包是否完整

`PATCH` 和 `REBUILD` 不允许进入 Git 发布流程。

## 12. PASS 后发布与文衡回写

只有 Claude Review 返回 `STATUS: PASS` 后才允许：

- `git add`
- `git commit`
- `git tag`
- `git push`
- 运行端同步

发布后必须回写：

- 文衡 `protocol-sync-registry.json`
- 文衡 `skill_registry.json`
- 文衡 `dev_batch_registry.json`

本批回写应体现：

- `protocol_status: adapted`
- `current_ref: docs/wenheng-dev-workflow.md`
- `integration_status: partial`
- 深度自动化回写、版本号协调和跨 skill 自动记录仍为后续待办

## 13. 后续深度集成批次

以下能力不属于本批，应另开 Claude Planning：

1. 版本号由文衡统一发放和校验。
2. 错误复盘自动写入文衡。
3. 任务进度自动回写文衡。
4. 跨 skill 协同 ledger 自动生成。
5. RAG 查询状态脱敏回写。
6. 发布后运行端同步自动校验。

