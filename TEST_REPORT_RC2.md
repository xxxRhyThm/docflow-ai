> 【历史报告，已被替代】本文件是 v0.1 / RC / RC2 时期的历史报告，仅供对比，不得作为 RC3 的最新结论引用。RC3 最新结论见 FIXES_RC3.md、TEST_REPORT_RC3.md、TEST_LOG_RC3.txt。

# DocFlow AI RC2 最新测试报告（2026-10-29）

## 环境与锁定依赖复现

- Python 3.12.3，RC2 验收副本 `docflow-ai-rc2/`，独立虚拟环境 `.venv`
- 审计曾指出独立环境的依赖与锁定版本不同；本轮在 RC2 中用
  `requirements.txt` 锁定版本重新安装并实测，`pip freeze` 核对一致：
  fastapi==0.162.0、uvicorn==0.54.0、pydantic==2.14.1、PyMuPDF==2.0、
  python-multipart==0.0.32、pytest==9.2.0、httpx==0.28.1
- 冻结的 v0.1（`docflow-ai/app/main.py`）与上一版 RC（`docflow-ai-rc/app/main.py`）
  校验值在 RC2 前后均未变化；所有修复只在 RC2 副本内。

## 执行命令

```bash
cd docflow-ai-rc2
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -v
```

## 修复前复现：独立回归测试 5 failed

```
test_special_float_must_not_confirm_or_export[NaN] FAILED（200，confirmed，total_amount=null）
test_special_float_must_not_confirm_or_export[Infinity] FAILED（200，confirmed，仅 abnormal 警告）
test_whitespace_vendor_must_block_confirmation FAILED（200，confirmed，vendor=" \t "）
test_blank_vendor_not_filled_from_next_line FAILED（vendor="Invoice Date: 2026-10-15"）
test_noncanonical_date_rejected FAILED（200，confirmed，invoice_date="2026-1-2"）
```

与独立审计报告的“5 failed”结论一致。

## 修复后最终结果：30 passed，0 failed，0 未执行

- 原 RC 测试 25 个：全部通过，未删除、未放宽断言。
  构成：test_api 6、test_extraction 3、test_validation 5、test_rc_acceptance 11。
- 独立回归测试 5 个：全部通过，文件原文未改动地加入
  `tests/test_docflow_independent_regressions.py`（NaN、Infinity、空白供应商、
  空白供应商跨行、非零填充日期）。
- 唯一警告：Starlette TestClient 弃用提示（建议 httpx2），与业务逻辑无关，不是失败。

## 服务器实测（curl，RC2 副本，端口 8004）

- `GET /health` -> ok
- 上传 invoice_001：id 1，INV-2026-001，1240.5，无警告，pending
- 提交 NaN 金额审核：返回 400 `invalid_amount: total_amount must be a finite number`
- 提交日期 `2026-1-2` 审核：返回 400 `invalid_date: 2026-1-2 is not in YYYY-MM-DD format`
- 两次拒绝后文档仍为 pending，导出 CSV 只有表头，无数据行
- 用原值 1240.50 审核：confirmed，导出 CSV 含该行
- 服务器随后已停止（端口 8004 不再响应）

## 未执行 / 未验证项目（不虚构）

- 浏览器完整 UI 人工验收：未完成。开发环境（无头浏览器） headless Chrome 被策略阻止，
  独立审计环境同样报告浏览器被策略阻止。服务器 API、静态文件、测试均已实测，
  但点击式浏览器流程必须在 Windows 本机完成，见 MANUAL_ACCEPTANCE.md。
- Excel 实际打开 CSV 的公式注入验证：未做，列入 Windows 本机步骤 6。
- 依赖全量漏洞扫描：未做，审计原文亦未做。
- Windows Python 3.12 锁定依赖安装与运行：未在本环境做 Windows 实测，
  需在 Windows 本机按 MANUAL_ACCEPTANCE.md 执行。
