> 【历史报告，已被替代】本文件是 v0.1 / RC / RC2 时期的历史报告，仅供对比，不得作为 RC3 的最新结论引用。RC3 最新结论见 FIXES_RC3.md、TEST_REPORT_RC3.md、TEST_LOG_RC3.txt。

# DocFlow AI RC2 修复说明（针对 2026-10-29 独立审计）

审计对象：`docflow-ai-rc.zip`（SHA-256 3e362dd3b51b0eedab4a8317e2aa3561e449402e7d4f296609b33d6153f069d9），
审计报告原文随包附带：`INDEPENDENT_AUDIT_20261029.md`。
修复范围：只修复缺陷，不增加 LLM、RAG 或其他新功能；不修改、发布或推送任何 GitHub 仓库；
冻结的 v0.1（`docflow-ai/`）和上一版 RC（`docflow-ai-rc/`）均未改动。

## 修复前复现（真实结果，非推测）

在 RC2 副本（修复前代码 + 独立回归测试）上实测：

```
5 failed, 0 passed
- test_special_float_must_not_confirm_or_export[NaN]: 返回 200，confirmed，total_amount=null
- test_special_float_must_not_confirm_or_export[Infinity]: 返回 200，confirmed，仅 abnormal_amount 警告
- test_whitespace_vendor_must_block_confirmation: 返回 200，confirmed，vendor=" \t "
- test_blank_vendor_not_filled_from_next_line: vendor="Invoice Date: 2026-10-15"
- test_noncanonical_date_rejected: 返回 200，confirmed，invoice_date="2026-1-2"
```

## 修复清单：文件位置与修改说明

### RC2-1 金额校验绕过（P0，最高优先级）

- `app/main.py`：`review()` 入口，在 `validate_invoice()` 之前、任何数据库写入之前，
  增加显式检查：`total_amount` 为 float 且 `not math.isfinite(total)` 时返回
  HTTP 400 `invalid_amount: total_amount must be a finite number`。
  选择在接口层返回 400 而不是用 Pydantic validator 触发 422，是为了保持
  “校验错误 = 400” 的 API 约定，与独立测试的期望一致；Pydantic 本身接受
  JSON 的 NaN / Infinity 浮点字面量，不能只依赖模型层。
- `app/validation.py`：`validate_invoice()` 增加 `math.isfinite` 检查，
  非有限金额判为 `invalid_amount`，属于 `blocking_errors` 的 `invalid_` 前缀，
  即使接口层检查被绕过，校验层仍会阻塞确认。两层都做，不单靠一层。
- 影响：NaN 不再存为 SQLite NULL、Infinity 不再只凭警告放行；被拒绝后文档
  保持 pending，不进入 CSV / JSON 导出。未改动金额存储类型（仍为 float），
  审计建议的 Decimal 迁移属于数据模型变更，本轮按用户“只修复缺陷”范围未做，
  已在下方“未改动项”中注明。

### RC2-2 字段跨行误提取（P1）

- `app/extraction.py`：删除原来对整段文本做 `re.search` 的 `_PATTERNS`，
  改为 `_LINE_PATTERNS` 逐行解析：每行只匹配以该标签开头的一行，
  标签后分隔符从 `\s*`（可跨行吞换行）改为 `[ \t]*`（只允许空格/Tab）。
  `Vendor:` 单独占行时不再匹配，供应商保持 None，后续校验标注缺失。
  其他字段（发票号、日期、币种、金额）同样改为逐行匹配，统一审查。
  首次出现为准，与原行为一致；金额仍要求 `[\d,]+\.\d{2}` 格式。

### RC2-3 空白字段（P1）

- `app/validation.py`：新增 `_clean()`，所有字符串字段先 strip，strip 后为空
  即判为缺失（`missing_field`），属于阻塞错误。供应商、发票号、日期、币种均适用。
- `app/main.py`：`review()` 在校验和存储前统一 strip 四个字符串字段，
  strip 后为空转为 None，确保空白值不写入数据库。
- 另加合理长度上限：供应商 200 字符、发票号 50 字符，超长判为 `invalid_` 阻塞错误；
  日期长度由 YYYY-MM-DD 正则约束，币种由支持列表约束。

### RC2-4 日期格式（P2）

- `app/validation.py`：新增 `_DATE_RE = ^\d{4}-\d{2}-\d{2}$`，先正则要求
  零填充的 YYYY-MM-DD 格式，再用 `datetime.strptime` 检查真实日历日期。
  `2026-1-2` 现在返回 `invalid_date: ... is not in YYYY-MM-DD format` 并被阻塞；
  `2026-02-30` 仍返回真实日期无效错误。两者均为 `invalid_` 阻塞前缀。

### RC2-5 验收文档逻辑矛盾（P2）

- `MANUAL_ACCEPTANCE.md`：全部重写。旧版第 6 步在 001 未确认的情况下
  预期导出同时含 001 和 003；旧版第 7 步在 003 已确认后提交无效金额却预期
  “文档仍未确认”。新版按顺序：先确认 001，再上传 003 并在确认前导出
  （只含 001），确认 003 后再导出（同时含 001 和 003）；无效修改分 7a
  （未确认文档：保持 pending）和 7b（已确认文档：拒绝新修改、保留旧版）
  两种情况分别验证，明确系统没有“撤销确认”状态转移。
- `README.md` / `README_EN.md`：测试数量从旧的 14 项（v0.1）/ 25 项（RC）
  统一更新为 RC2 的 30 项，并新增 RC2 修复章节与状态/导出规则说明。
- `TEST_REPORT_RC2.md`：最新实测报告，替代旧版数字作为当前依据。

## 审计中明确未作为漏洞、且本轮未改动的项

- 重复发票号可同时确认并导出：审计原文明确这是原作者披露的产品约束，
  不是未知漏洞。本轮保持“标注警告、不拒绝、不唯一约束”，并在 README /
  MANUAL 中显式写清；若未来业务需要去重，需另外做唯一性策略。
- CSV 公式注入的表格软件实测：审计建议用目标表格软件打开、另存、重开验证。
  本环境无 Excel 实测条件，未虚构该结果，已列入 Windows 本机手工验收步骤 6。
- 浏览器点击验收：开发环境（无头浏览器）与独立审计环境均被策略阻止，未完成，未虚构，
  仍需 Windows 本机执行 MANUAL 中的步骤。
- LICENSE / PyMuPDF 授权：审计提示公开或闭源收费前需评估 AGPL v3 义务。
  本轮不做 GitHub 发布，不新增 LICENSE 文件，列为未来发布前待决策项。
- 依赖漏洞全量扫描：审计原文说明未做，本轮未做，只做了锁定依赖复现测试。
