# DocFlow AI RC3 修复说明（针对 2026-10-29 第二轮独立审计）

审计对象：RC2 压缩包（SHA-256 fbca1e99d131f3c44f8fd15040c7f817174999526a8fabf19d48942db9d5c3cf，
35 个文件，56,281 字节），审计报告原文随包附带：`INDEPENDENT_AUDIT_RC2_20261029.md`。
修复范围：只修复缺陷，不增加 LLM、RAG、登录或其他新功能；不修改、发布或推送任何
GitHub 仓库；冻结的 v0.1、上一版 RC、上一版 RC2 均未改动，所有修复只在 RC3 副本内。
独立边界测试文件 `tests/test_rc2_audit_boundaries.py` 原样加入，未修改任何断言。

## 修复前复现（真实结果）

在 RC3 副本（修复前代码 + 独立边界测试）上实测：**57 passed, 4 failed**，与审计一致：

```
test_invalid_dates_rejected[２０２６-10-29] FAILED（200，confirmed，全角年份原样导出）
test_boolean_amount_is_not_money FAILED（200，confirmed，total_amount=1.0）
test_malformed_grouping_not_silently_changed FAILED（1,2,3.45 变成 123.45）
test_invalid_nan_string_field_returns_client_error FAILED（500 Internal Server Error）
```

其余 57 项在修复前已通过，修复后未被破坏。

## 修复清单：文件位置与修改说明

### RC3-1 布尔金额（F1，中）

- `app/main.py`：`ReviewRequest` 增加 `@field_validator("total_amount", mode="before")`，
  在 Pydantic 把布尔值转成浮点数之前拒绝：`isinstance(value, bool)` 时抛出
  ValueError，FastAPI 返回 422（审计测试接受 400/422），记录不被写入、不被确认。
  刻意不拒绝 NaN / Infinity：在此层放行，让它们进入 `review()` 的有限数检查，
  保持既有的 400 行为；整数金额仍可正常转为浮点数，字符串金额（如 "1e309"）
  仍按原有路径处理为非有限数并返回 400，避免无意改变协议。
- `app/validation.py`：`validate_invoice()` 增加布尔值检查，
  `total_amount` 为 bool 时判为 `invalid_amount`（阻塞前缀），作为直接调用校验层时的第二道防线。
  注意：Python 中 bool 是 int 的子类，`float(True) == 1.0`，不先检查类型就一定会被误认。

### RC3-2 错误千分位（F2，中）

- `app/extraction.py`：金额正则从 `[\d,]+\.[0-9]{2}`（逗号任意混排，随后删逗号转 float）
  改为严格分组：`(?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)\.[0-9]{2}`。
  只允许无分组（`1240.50`）或严格三位分组（`1,240.50`）。
  `1,2,3.45`、`12,34.56` 等不再匹配，金额保持 None，上传校验标注
  `missing_field: total_amount`（用户要求：标为缺失或格式错误，不要猜测金额），
  不再静默改成另一笔金额。

### RC3-3 日期字符范围（F3，低）

- `app/validation.py`：日期正则从 `\d` 改为 `[0-9]`，
  发票号正则同步改为 `[0-9]`；`datetime.strptime` 的真实日历检查保留。
  Python 正则的 `\d` 接受 Unicode 数字，全角年份 `２０２６` 曾因此通过；
  改为 ASCII 后，全角年份返回 `invalid_date: ... is not in YYYY-MM-DD format` 并被阻塞。
  阿拉伯数字日期等其他 Unicode 数字同样被拒绝，不再依赖 strptime 的宽松接受行为。
- `app/extraction.py`：日期与金额的数字同步改为 `[0-9]`，PDF 提取与审核校验保持一致。

### RC3-4 异常请求处理（F4，低）

- `app/main.py`：新增 `RequestValidationError` 处理器与 `_sanitize_for_json()`。
  原因：供应商字段传入裸 NaN 时，Pydantic 校验失败，默认错误处理器在序列化
  错误详情中的 `input: nan` 时，Starlette 的严格 JSON 序列化拒绝非有限浮点数，
  导致 500。处理器把非有限浮点转为字符串、其他不可 JSON 序列化值转为字符串后，
  返回 422。请求在校验阶段即被拒绝，数据库记录不变。
  金额字段的 NaN / Infinity 不走这条路径：它们是合法浮点输入，由 `review()` 的
  有限数检查返回既有的 400，两条路径互不干扰。

### RC3-5 提取到 inf 后数据库与 API 表示不一致（审计 §4.2）

- `app/extraction.py`：金额转 float 后增加 `math.isfinite` 检查，
  非有限结果（例如 309/310/400 位数字）不再返回 inf，改为 None 并保留警告
  `invalid_amount: total_amount must be a finite number`。
- `app/main.py`：`upload()` 在入库前再做一次防线，非有限金额一律置为 None。
  实测：310 位数字上传后，数据库原始值与 API 列表值均为 None，状态 pending，
  警告含 invalid_amount 与 missing_field，不可确认，与旧的“数据库存 inf、API 显示 null”
  不再一致。旧 RC2 数据库中的 inf 记录不会被自动迁移，应直接丢弃旧演示数据库，
  用新数据库重新上传，这是演示数据的正确处理方式，不是数据迁移。

### RC3-6 上传大小限制的实际作用范围（审计 §4.1，文档修正，非代码行为变更）

- `app/main.py`：`_read_upload_limited()` 的注释已修正；`README.md` / `README_EN.md` /
  `MANUAL_ACCEPTANCE.md` 同步修正。
- 准确描述：10 MB / 413 限制只作用于路由读取阶段（分块读取、累计超限即拒绝）
  和最终接受/拒绝决定；Starlette 会先解析 multipart 并把文件落盘到临时文件，
  因此不能声称“客户端超过 10 MB 时网络接收立即中断”或“磁盘和 CPU 全程都有同样上限”。
  本 Demo 没有入口请求总量限制、反向代理限制或 PDF 解析 CPU 隔离；公开服务需另行增加，
  本轮按“不增加新功能”范围未实现这些入口控制，已在文档中明确声明。

### RC3-7 文档与版本标识（审计 §5）

- `app/main.py`：统一版本标识为 `0.1-rc3`（FastAPI version 与 `/health` 均返回该值），
  不再使用旧的 `1.0.0`。
- `README_EN.md`：第 8 条功能列表的“14 tests”已改为 91 项；测试章节的 30 项已改为 91 项，
  与中文 README 一致；安装示例的目录已改为 `docflow-ai-rc3`。
- `README.md`：测试章节的 30 项已改为 91 项，安装示例目录已改为 `docflow-ai-rc3`。
- 历史报告标记：`SECURITY_CHECK.md`、`TEST_REPORT.md`（v0.1）、
  `SECURITY_REVIEW_RC.md`、`TEST_REPORT_RC.md`（RC）、`FIXES_RC2.md`、`TEST_REPORT_RC2.md`（RC2）
  顶部均已加“历史报告，已被替代”标记，仅供对比，不得作为 RC3 最新结论引用。
  独立审计报告原文（`INDEPENDENT_AUDIT_RC2_20261029.md`、`INDEPENDENT_AUDIT_20261029.md`）
  作为外部证据保持原文未改动，FILE_LIST 中已注明其为历史审计证据。
- `MANUAL_ACCEPTANCE.md`：已按 PowerShell 重写，Bash 反斜杠续行示例已删除；
  新增空白字段、非零填充日期的完整 PowerShell 请求示例；新增 RC3 四项回归的
  PowerShell 复验步骤；浏览器与 Excel 未执行的部分全部标为“未执行”。

## 本轮未改动、未虚构的项

- 独立边界测试文件未修改任何断言；原有 30 项测试未删除、未跳过、未放宽。
- 整数金额、字符串金额的协议未改变：整数仍可确认，字符串 "NaN" / "1e309" 仍返回 400，
  均由边界测试覆盖。
- 重复发票号政策未改变：仍为标注警告、可同时确认并导出，与已披露规则一致。
- 浏览器点击验收、Excel/WPS 打开保存重开验收：本环境未执行，审计环境亦未执行，
  均在手工验收步骤中标为“未执行”，没有用 API 测试代替 UI 验收结论。
- 许可证：未新增 LICENSE 文件，未宣称 MIT 已解决授权问题，单独建议见本仓库公开版 `NOTICE.md` 与 README（RC3 时的历史建议文件未收入公开仓库，原文另行保留）。
- 全依赖漏洞扫描、模糊测试、并发与资源耗尽测试：审计未做，本轮未做，不宣称不存在风险。
