> 【历史报告，已被替代】本文件是 v0.1 / RC / RC2 时期的历史报告，仅供对比，不得作为 RC3 的最新结论引用。RC3 最新结论见 FIXES_RC3.md、TEST_REPORT_RC3.md、TEST_LOG_RC3.txt。

# DocFlow AI v0.1 RC 最新测试报告（2026-10-29）

## 环境

- Python 3.12.3，RC 验收副本 `docflow-ai-rc/`，独立虚拟环境 `.venv`
- 依赖已固定：fastapi==0.162.0、uvicorn==0.54.0、pydantic==2.14.1、
  PyMuPDF==2.0、python-multipart==0.0.32、pytest==9.2.0、httpx==0.28.1
- 冻结的 v0.1 原目录 `docflow-ai/` 未被修改（`app/main.py` 校验值在 RC 前后不变）

## 执行命令

```bash
cd docflow-ai-rc
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -v
```

## 最终结果：25 passed，0 failed，0 未执行

- 原有测试 14 个：全部通过（API 6、抽取 3、校验 5）
- 新增 RC 验收测试 11 个：全部通过，见下表

| RC 测试 | 覆盖点 | 结果 |
|---|---|---|
| test_field_order_changed_still_extracts | 字段顺序变化（供应商在前、金额在日期前）仍能抽取 | 通过 |
| test_missing_vendor_flagged_and_blocks_confirmation | 缺失供应商被标注，审核直接拒绝 400，仍未确认、不导出 | 通过 |
| test_invalid_date_and_amount_format | 2026-02-30 无效日期、金额 abc 无法解析 | 通过 |
| test_duplicate_invoice_number_flagged | 同一发票号第二次上传被标注 duplicate | 通过 |
| test_illegal_empty_and_corrupt_pdf_rejected | 非 PDF、空文件、伪造 PDF、截断 PDF 均 400 | 通过 |
| test_encrypted_pdf_rejected_with_400_not_500 | 加密 PDF 返回 400，不是 500 | 通过 |
| test_export_without_review_excludes_document | 未审核文档不在 CSV/JSON 导出中 | 通过 |
| test_api_cannot_confirm_invalid_amount | API 提交 0、-5 金额确认均 400，仍未确认、不导出 | 通过 |
| test_csv_formula_injection_neutralised | 供应商 `=2+2` 在 CSV 中变为 `'=2+2` | 通过 |
| test_frontend_does_not_use_innerhtml_for_untrusted_data | 前端无 innerHTML 赋值，全部 textContent | 通过 |
| test_oversized_upload_rejected | 10 MB + 1 字节上传被拒绝（400/413） | 通过 |

唯一警告：Starlette TestClient 弃用提示（建议 httpx2），与业务逻辑无关，不是失败。

## 测试过程中的真实失败记录（不隐瞒）

- 第一轮 RC 运行：24 通过，1 失败。失败项是前端测试：`app.js` 中
  `tbody.innerHTML = ""` 虽然只是清空，但仍属于 innerHTML 赋值。
  修复：改为 `replaceChildren()`。
- 第二轮运行：仍有 1 失败，原因是测试断言把注释里提到的 innerHTML 一词
  也算作违规。修复测试断言：只检查 `innerHTML =` / `innerHTML +=` 赋值，
  注释不算。此处改的是测试断言的严格程度，不是改业务代码来迁就测试，
  业务代码本身已无 innerHTML 赋值。
- 第三轮运行：25 全部通过，即本报告的最终结果。

RC 测试输入说明：`tests/test_rc_acceptance.py` 内的 PDF 全部用 PyMuPDF
现场生成，没有 import、没有复用 `samples/generate_samples.py`，
字段顺序、缺失字段、错误格式均为独立构造。

## 服务器实测（curl，RC 副本，端口 8003）

- `GET /health` -> ok
- 上传 invoice_001：id 1，INV-2026-001，1240.5，无警告，pending
- 再次上传同一文件：id 2，标注 duplicate_invoice_number（已存在文档 [1]）
- 对 id 1 用总金额 0 提交审核：返回 400 invalid_amount，文档仍 pending，
  导出 CSV 只有表头，无数据行
- 对 id 1 用原值 1240.50 提交审核：confirmed，导出 CSV 含该行
  （同时带有 duplicate 警告，因为 id 2 存在同号文档，属预期标注行为）
- 静态文件：`GET /` 200，`GET /static/app.js` 200，实测返回的 app.js
  中无 `innerHTML =` 赋值
- 服务器随后已停止（端口 8003 不再响应）

## 未执行 / 未验证项目

- 浏览器完整 UI 人工验收：未完成，原因见 MANUAL_ACCEPTANCE.md。
  本环境 headless Chrome 仍被 浏览器平台 域名策略阻止启动。
  服务器 API、静态文件内容、测试均已实测，但点击式浏览器流程
  必须在 Windows 本机完成，不得声称已通过完整 UI 验收。
