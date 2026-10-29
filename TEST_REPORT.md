> 【历史报告，已被替代】本文件是 v0.1 / RC / RC2 时期的历史报告，仅供对比，不得作为 RC3 的最新结论引用。RC3 最新结论见 FIXES_RC3.md、TEST_REPORT_RC3.md、TEST_LOG_RC3.txt。

# 测试报告（实际执行记录，2026-10-29）

## 环境

- Python 3.12.3（要求 3.11+，满足）
- 虚拟环境：`docflow-ai/.venv`（交付压缩包中已排除，接收方需重建）
- 依赖安装命令：`.venv/bin/pip install -r requirements.txt`（实测成功，
  fastapi 0.162.0，pytest 9.2.0）

## 实际执行的命令

```bash
cd docflow-ai
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
.venv/bin/python samples/generate_samples.py
.venv/bin/python -m pytest -v
.venv/bin/uvicorn app.main:app --port 8000
```

## pytest 结果：14 passed，0 failed，0 未执行

```
tests/test_api.py::test_health PASSED
tests/test_api.py::test_upload_extract_and_review_flow PASSED
tests/test_api.py::test_upload_rejects_non_pdf PASSED
tests/test_api.py::test_upload_rejects_fake_pdf_header PASSED
tests/test_api.py::test_export_only_confirmed PASSED
tests/test_api.py::test_llm_status_is_honest PASSED
tests/test_extraction.py::test_extract_all_fields PASSED
tests/test_extraction.py::test_extract_missing_fields_are_none_not_fabricated PASSED
tests/test_extraction.py::test_extract_empty_text_warns PASSED
tests/test_validation.py::test_valid_invoice_has_no_warnings PASSED
tests/test_validation.py::test_missing_fields_reported PASSED
tests/test_validation.py::test_invalid_date_reported PASSED
tests/test_validation.py::test_zero_amount_reported PASSED
tests/test_validation.py::test_abnormal_amount_flagged_not_silently_accepted PASSED
14 passed, 1 warning in 1.57s
```

唯一警告：Starlette TestClient 弃用提示（建议改用 httpx2），与业务逻辑无关，
不是失败项。

## 服务器实测（curl，非测试替身）

- `GET /health` -> `{"status":"ok","service":"DocFlow AI","version":"1.0.0"}`
- `GET /` -> 首页 HTML 200
- `POST /api/upload samples/invoice_001.pdf` -> id 1，INV-2026-001，
  Acme Supplies Ltd，2026-10-15，USD 1240.5，warnings []
- `POST /api/upload samples/invoice_003.pdf` -> id 2，INV-2026-003，
  Northwind Trading，2026-10-28，USD 0.0，
  warnings ["invalid_amount: total_amount must be greater than 0"]
- 直接抽取三份样本（不经过服务器）与 EXPECTED_RESULTS.md 完全一致：
  001 1240.5 无警告；002 875.0 无警告；003 0.0 金额错误警告。
- `POST /api/documents/2/review`（将 003 总金额修正为 320.00）-> confirmed，warnings []
- `POST /api/documents/1/review`（001 原值确认）-> confirmed
- `GET /api/export?format=csv` -> 仅含已确认的 001、003 两行
- `GET /api/export?format=json` -> 仅含已确认文档
- `GET /api/llm` -> enabled=false，default_method=rule
- `GET /static/app.js` -> 200，3627 字节

## 未执行项目

- 无。14 个测试全部实际执行，无跳过、无标记 xfail。
- 未产出运行截图：原因见 SECURITY_CHECK.md（本机 headless Chrome 被策略阻止）。
  这不是测试失败，是截图工具限制；运行证据以上述 curl 结果为准。

## 已知限制

- 仅单一发票格式；扫描图片 PDF、其他版式会返回缺失字段或明确错误，不编造。
- 无登录权限；不要直接暴露到公网。
- SQLite 适合演示，不适合高并发生产。
