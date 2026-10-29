# DocFlow AI RC3 最新测试报告（2026-10-29）

## 环境、Python 版本与锁定依赖

- Python：3.12.3（本环境实测；审计环境为 Windows CPython 3.12.14，两者补丁版本不同，
  本报告不冒充与审计环境完全相同的 Python 补丁版本）
- RC3 验收副本 `docflow-ai-rc3/`，独立虚拟环境 `.venv`
- `requirements.txt` 只锁定 7 项直接依赖，实测安装版本与之完全一致：
  fastapi==0.162.0、uvicorn==0.54.0、pydantic==2.14.1、PyMuPDF==2.0、
  python-multipart==0.0.32、pytest==9.2.0、httpx==0.28.1
- 间接依赖未在 requirements.txt 中完整锁定，也没有 wheel 哈希；本环境实测
  Starlette==1.10.0，与审计环境一致，但不能据此声称复现了全部间接依赖。
  完整 pip freeze 见 `TEST_LOG_RC3.txt` 开头。
- 冻结的 v0.1、上一版 RC、上一版 RC2 均未改动；所有修复只在 RC3 副本内。
  原始 RC2 ZIP 校验值在 RC3 前后均为 fbca1e99d131f3c44f8fd15040c7f817174999526a8fabf19d48942db9d5c3cf。

## 执行命令

```bash
cd docflow-ai-rc3
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -v
```

完整输出见 `TEST_LOG_RC3.txt`。

## 修复前复现：独立边界测试 57 passed, 4 failed

```
test_invalid_dates_rejected[２０２６-10-29] FAILED（200，confirmed）
test_boolean_amount_is_not_money FAILED（200，confirmed，total_amount=1.0）
test_malformed_grouping_not_silently_changed FAILED（1,2,3.45 变成 123.45）
test_invalid_nan_string_field_returns_client_error FAILED（500）
```

与第二轮独立审计报告的“57 passed, 4 failed”结论一致。

## 修复后最终结果：91 passed，0 failed，0 未执行

- 原有测试 30 个：全部通过，未删除、未跳过、未放宽断言。
  构成：test_api 6、test_extraction 3、test_validation 5、test_rc_acceptance 11、
  test_docflow_independent_regressions 5。
- 独立边界测试 61 个：全部通过，文件原样加入，未修改任何断言。
  构成：非有限金额状态组合 14、空白字段 12、日期拒绝 8、有效日历日期 3、
  长度限制 2、空白标签不吞行 5、CSV 往返 8、重复号 1、页数限制 2、
  精确上传大小 1、SQL 元字符 1、超大金额不污染数据库 1、布尔金额 1、
  错误千分位 1、裸 NaN 字符串字段 1。
- 唯一警告：Starlette TestClient 弃用提示（建议 httpx2），与业务逻辑无关，不是失败。

## 服务器实测（curl，RC3 副本，端口 8005，版本 0.1-rc3）

- `GET /health` -> `{"status":"ok","service":"DocFlow AI","version":"0.1-rc3"}`
- 上传 invoice_001：id 1，INV-2026-001，1240.5，无警告，pending
- 提交 `total_amount: true`：返回 422（布尔值不是金额），记录保持 pending
- 提交供应商裸 NaN：返回 422（不是 500），记录保持 pending
- 两次拒绝后数据库原始查询：`(1, 1240.5, 'pending')`，与 API 一致，未被修改
- 用原值 1240.50 确认：confirmed；再提交 `total_amount: true`：返回 422，
  记录保持 confirmed，数据库与导出均为 1240.5，未被改写
- 超大金额上传（310 位数字，TestClient + 数据库原始查询）：
  上传 200，API 与数据库原始值均为 None，状态 pending，
  警告含 invalid_amount 与 missing_field，不可确认
- 静态文件：`GET /static/app.js` 200
- 服务器随后已停止（端口 8005 不再响应）

## pending / confirmed 无效修改核对（已实测，非仅测试断言）

- pending 文档的无效修改：拒绝，数据库与 API 均保持 pending 与原值，导出不含该文档。
- confirmed 文档的无效修改：拒绝，数据库与 API 均保持 confirmed 与旧值，导出仍为旧值。
  系统没有“撤销确认”状态转移，这是当前设计的明确选择。

## 未执行 / 未验证项目（不虚构）

- 浏览器完整 UI 点击与 DOM 执行验收：未执行。本环境 headless Chrome 被策略阻止，
  审计环境亦报告浏览器被策略阻止。必须在 Windows 本机完成，见 MANUAL_ACCEPTANCE.md。
- Excel / WPS 打开、另存、重开 CSV 验收：未执行。CSV 单引号防护只经 API 与 csv 模块
  往返验证，不能称为所有表格软件的绝对保证。
- 全依赖漏洞扫描、模糊测试、并发与资源耗尽测试：未执行。
- Windows Python 3.12 锁定依赖安装与运行：未在本环境做 Windows 实测，
  需在 Windows 本机按 MANUAL_ACCEPTANCE.md 执行。
