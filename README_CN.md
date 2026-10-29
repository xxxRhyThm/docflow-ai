# DocFlow AI（中文）

English version: [README.md](README.md)

## 公开作品集 Demo 声明（0.1-rc3）

- 作者：Haoming Xu；版权：Copyright (C) 2026 Haoming Xu。
- 许可：项目代码仅按 GNU AGPL-3.0（only）许可，不适用 or-later；完整文本见 `LICENSE`（GNU 官方原文，未改写）。作者版权见本声明与 `NOTICE.md`，不在 `LICENSE` 文件内（`LICENSE` 开头的 2007 年 FSF 声明属于许可证文档本身）。
  PyMuPDF 按 AGPL 路径使用；**本项目没有获得 Artifex 商业许可，不得宣称已获得。**
- 第三方依赖完整清单见 `NOTICE.md`，现行结论以 `NOTICE.md` 与本声明为准。
- 测试与验收：本仓库内 91 项自动化测试见 `TEST_REPORT_FINAL.md`；
  独立复核新增 34 项、合计 125 项为独立复核结论（用户报告），新证据包补交并重跑后更新，
  本次不得写成已重跑 125 项。Windows Chrome 核心项与 Excel 公式样例为独立复核结论；
  浏览器文件选择/上传、非法文件 UI 提示、WPS 等仍未执行，详见本文件“技术限制”与 `TEST_REPORT_FINAL.md`。
- 已知低优先级界面问题 UI-20261029-01：确认成功后旧警告可能暂留显示，
  不影响保存值和导出值；复现细节待补记，处理方式待作者决定。
- 浏览器归属修正：第二轮（RC2）审计并未报告新的浏览器策略阻止，它是未尝试；
  第一轮是本地 Chromium 打开 127.0.0.1 被 ERR_BLOCKED_BY_ADMINISTRATOR 阻止；
  开发环境（无头浏览器）是 headless Chrome 被 浏览器平台 策略阻止；三者不得混写。
- 本仓库为公开作品集 Demo；服务本身仍只应在本地 127.0.0.1 运行，不直接暴露公网。

基于 Python + FastAPI 的智能文档抽取、校验与人工审核系统（版本标识：0.1-rc3）。

**版本标识统一说明：** 本包统一使用 `0.1-rc3` 作为版本标识，`/health` 与 FastAPI
版本字段均返回 `0.1-rc3`，不再使用旧的 `1.0.0`。旧报告中出现的 `1.0.0` 均为历史版本标识。

**定位：** 技术作品集 Demo，不是生产系统。第一版只针对**单一模拟发票格式**开发，
不声称支持任意复杂文档。

## RC 验收版声明（必读）

- v0.1 是一个单格式发票处理演示系统。
- 默认不调用 LLM。LLM 接口仅设计，未启用，`/api/llm` 返回 `enabled: false`。
- 不支持任意格式 PDF 或扫描件 OCR。扫描图片 PDF、其他版式会返回缺失字段或明确错误，不编造结果。
- 未实现用户认证，不应直接暴露公网。只能在本机 `127.0.0.1` 运行，不要用 `--host 0.0.0.0` 对外提供服务。
- 当前项目不能宣称为生产级 SaaS。没有登录、权限、备份、日志审计、高并发与生产部署设计。

## RC3 修复（相对 RC2，针对 2026-10-29 第二轮独立审计，详见 FIXES_RC3.md）

1. 布尔金额（F1）：`total_amount: true` 曾被 Pydantic 转成 1.0 并确认导出。现已在类型转换前用 `field_validator(mode="before")` 拒绝布尔值，返回 422，记录不变；NaN / Infinity 金额仍按既有规则返回 400。
2. 错误千分位（F2）：`Total Amount: 1,2,3.45` 曾被静默抽成 123.45。现只允许无分组或严格三位分组（`1240.50` 或 `1,240.50`），错误分组不再匹配，金额保持 None，标注缺失/格式错误，不猜测金额。
3. 日期字符范围（F3）：全角年份 `２０２６-10-29` 曾通过确认。现日期、发票号、金额的数字一律只认 ASCII `[0-9]`，不再用 Unicode `\d`，同时保留真实日历检查。
4. 异常请求处理（F4）：供应商字段传入裸 NaN 曾返回 500。现增加 `RequestValidationError` 处理器，把非有限浮点等不可严格序列化值转为字符串后返回 422，记录不变；金额字段 NaN / Infinity 仍返回 400。
5. inf 表示不一致：超大金额（如 310 位数字）抽成 inf 后，数据库曾存 inf 而 API 显示 null。现抽取阶段就把非有限金额转为 None 并保留警告，上传入库前再做一次防线，数据库与 API 均为 None，记录保持 pending，不可确认。
6. 上传大小限制的实际作用范围（已修正说明）：10 MB / 413 限制只作用于路由读取阶段和最终接受/拒绝决定；Starlette 会先解析 multipart 并落盘临时文件，不能声称网络接收立即中断或全程磁盘/CPU 都有同样上限。公开服务需另加入口请求总量限制，本 Demo 没有。

## 历史报告标记说明

- `SECURITY_CHECK.md`、`TEST_REPORT.md` 是冻结 v0.1 的历史报告，`SECURITY_REVIEW_RC.md`、`TEST_REPORT_RC.md` 是 RC 历史报告，`FIXES_RC2.md`、`TEST_REPORT_RC2.md` 是 RC2 历史报告；以上文件顶部均已加“历史报告，已被替代”标记，仅供对比，**不得作为 RC3 的最新结论引用**。
- RC3 的最新结论见 `FIXES_RC3.md`、`TEST_REPORT_RC3.md`、`TEST_LOG_RC3.txt`。
- 许可证：本项目代码仅按 GNU AGPL-3.0（only）许可，`LICENSE` 为 GNU 官方原文，`NOTICE.md` 为完整第三方清单；作者版权见本文件顶部声明与 `NOTICE.md`。

## RC2 修复（相对 RC，针对 2026-10-29 独立审计，详见 FIXES_RC2.md）

1. 金额校验绕过（P0）：JSON 提交 NaN / Infinity 曾返回 200 并确认，金额在 SQLite 中存为 null。现已在写入数据库之前拒绝非有限数值：审核接口显式检查 `math.isfinite`，校验层把非有限金额判为 `invalid_amount`，返回 400，文档保持未确认且不导出。
2. 字段跨行误提取（P1）：`Vendor:` 单独占行时，下一行日期曾被误抽为供应商。现改为逐行解析，标签后只允许空格/Tab，不允许跨行，空白值返回 None 并标注缺失。
3. 空白字段（P1）：供应商只有空格、Tab 时曾通过确认。现审核前统一 strip，strip 后为空即判缺失并拒绝确认；字符串字段同时加了合理长度上限（供应商 200、发票号 50）。
4. 日期格式（P2）：`2026-1-2` 曾通过确认。现先用正则严格要求 `YYYY-MM-DD`（零填充），再用日历检查真实日期，两项任一不符即拒绝。
5. 验收文档矛盾（P2）：MANUAL_ACCEPTANCE.md 已重写，见下文“手工验收逻辑说明”。

## 手工验收逻辑说明（修正后的明确规则）

- 对**未确认文档**提交无效修改：拒绝 400，文档**保持未确认**，不进入导出。
- 对**已确认文档**提交无效修改：拒绝 400，**保留旧的已确认版本**，不撤销确认、不写入无效值，导出中仍是旧值。系统没有“撤销确认”状态转移，这是当前设计的明确选择，不是缺陷。
- 重复发票号**不是唯一约束**：两个同号文档都可以确认并导出，系统只标注警告。审计报告已明确这是原作者披露的产品约束，不是未知漏洞；若未来业务需要去重，必须另外做唯一性策略，本轮不改。

## RC 修复（相对冻结的 v0.1，详见 SECURITY_REVIEW_RC.md）

1. 加密 PDF 从原来的未处理异常（HTTP 500）改为明确的 400 拒绝。
2. 上传改为分块读取，超过 10 MB 在读取时即拒绝，不再先把整个文件读入内存。
3. 审核时缺失字段、无效日期/金额、不支持币种会直接拒绝确认（400），文档保持未确认且不进入导出；以前会照样确认，这是本次最关键的修复。
4. 前端不再用 innerHTML 拼接 PDF 文本，全部改用 textContent，消除 PDF 文本注入 HTML 的 XSS 风险。
5. CSV 导出对 `=`、`+`、`-`、`@`、制表符、回车开头的单元格加单引号前缀，防止公式注入。
6. 重复发票号在上传和审核时都会标注警告（不直接拒绝，因为重新上传/修正是合理场景）。
7. 上传文件名只保留 basename，防止客户端传入带目录的文件名；PDF 打开失败不再把库异常原文返回给 API。
8. 依赖从 `>=` 范围固定为 RC 实测版本，见 `requirements.txt`。

## 功能

1. PDF 上传与安全检查：只接受 `.pdf`、文件非空、最大 10 MB、必须以 `%PDF-` 开头、最多 20 页。
2. PDF 文本提取（PyMuPDF），记录原始文件名与处理状态。
3. 抽取字段：发票号、供应商、发票日期、币种、总金额。
4. 校验：缺失字段、无效日期（如 2026-02-30）、金额 <= 0、异常大额（> 1,000,000）、不支持币种、发票号格式。
5. 人工审核页面：可修正字段后确认，确认后状态变为 `confirmed`。
6. SQLite 保存确认结果与审核状态。
7. 导出：仅导出已确认文档，支持 CSV 和 JSON。
8. 自动化测试：共 91 个测试（原 RC2 的 30 个 + 第二轮独立边界测试 61 个），详见 TEST_REPORT_RC3.md。
9. LLM 接口：仅设计，未接入。`/api/llm` 明确返回 `enabled: false, default_method: "rule"`，
   规则提取结果绝不冒充 LLM 结果。

## 安装与运行（已在 Python 3.12.3 实测）

```bash
cd docflow-ai
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python samples/generate_samples.py
.venv/bin/uvicorn app.main:app --port 8000
```

打开 http://127.0.0.1:8000/ ，上传 `samples/` 下的 PDF 即可演示。

## 测试（实测结果）

```bash
.venv/bin/python -m pytest -v
```

2026-10-29 RC3 实测：**91 passed，0 failed**，仅 1 条与测试无关的警告
（Starlette 建议用 httpx2 的 TestClient 弃用提示，不影响结果）。
测试文件：`tests/test_api.py`（6）、`tests/test_extraction.py`（3）、`tests/test_validation.py`（5）、
`tests/test_rc_acceptance.py`（11）、`tests/test_docflow_independent_regressions.py`（5）、
`tests/test_rc2_audit_boundaries.py`（61）。
旧的 14 项是 v0.1 冻结版的数字，RC 为 25 项，RC2 为 30 项，RC3 为 91 项，详见 TEST_REPORT_RC3.md。

## 演示数据与预期结果

全部为虚构数据，不涉及任何真实客户。详见 `samples/EXPECTED_RESULTS.md`。

| 文件 | 发票号 | 供应商 | 日期 | 币种 | 总金额 | 预期校验 |
|---|---|---|---|---|---|---|
| invoice_001.pdf | INV-2026-001 | Acme Supplies Ltd | 2026-10-15 | USD | 1240.50 | 无 |
| invoice_002.pdf | INV-2026-002 | Bright Office Co | 2026-10-20 | EUR | 875.00 | 无 |
| invoice_003.pdf | INV-2026-003 | Northwind Trading | 2026-10-28 | USD | 0.00 | 金额必须大于 0（需人工修正后确认） |

实测服务器验证（2026-10-29）：上传 001 得到 1240.5、无警告；上传 003 得到 0.0
并提示金额错误；将 003 修正为 320.00 后确认成功；导出 CSV/JSON 仅包含已确认文档。

## 架构

```
static/index.html + style.css + app.js   前端：上传、列表、审核、导出
app/main.py                              FastAPI 路由：上传/列表/详情/审核/导出/健康检查
app/pdf.py                               PDF 安全检查与 PyMuPDF 文本提取
app/extraction.py                        确定性规则抽取（单一发票格式）
app/validation.py                        校验规则
app/database.py                          SQLite（data/docflow.db，测试用临时库）
app/llm.py                               LLM 接口设计（默认关闭，无密钥、无网络调用）
samples/generate_samples.py              生成 3 份模拟发票 PDF
tests/                                   pytest 测试
```

## 技术限制（必须如实说明）

- 只支持本项目定义的单一发票格式；换格式、换字段名、扫描图片 PDF 都会失败或返回缺失字段，不会编造结果。
- 不支持 OCR、不支持 FAISS/RAG、不支持 Docker 集群、云部署、多租户。
- 没有用户登录与权限系统，**不要直接把本 Demo 暴露到公网**；生产使用前必须加认证、授权、日志与备份。
- SQLite 适合演示与小量数据，不适合高并发生产。
- 本仓库为公开作品集 Demo，不购买云服务；服务本身仍只应在本地运行。
  使用前请先阅读 `SECURITY_CHECK.md` 与 `NOTICE.md`。

## 安全说明

- 代码中无任何硬编码密钥；无 `.env`、无凭证、无个人信息。
- 上传文件只按扩展名 + `%PDF-` 头 + PyMuPDF 打开三重检查，失败返回明确错误，不生成虚假结果。
- 导出仅限已确认文档，未确认的上传不会被导出。
