# DocFlow AI 0.1-rc3 GitHub 发布副本目录清单（2026-10-29，推送版）

仓库内共 44 个文件，不含虚拟环境、缓存、数据库文件。
路径以压缩包内为准：docflow-ai/...

```
docflow-ai/.gitignore
docflow-ai/FILE_LIST.md
docflow-ai/FIXES_RC2.md
docflow-ai/FIXES_RC3.md
docflow-ai/INDEPENDENT_AUDIT_20261029.md
docflow-ai/INDEPENDENT_AUDIT_RC2_20261029.md
docflow-ai/LICENSE
docflow-ai/MANUAL_ACCEPTANCE.md
docflow-ai/NOTICE.md
docflow-ai/README.md
docflow-ai/README_CN.md
docflow-ai/SECURITY_CHECK.md
docflow-ai/SECURITY_REVIEW_RC.md
docflow-ai/TEST_LOG_RC3.txt
docflow-ai/TEST_REPORT.md
docflow-ai/TEST_REPORT_FINAL.md
docflow-ai/TEST_REPORT_RC.md
docflow-ai/TEST_REPORT_RC2.md
docflow-ai/TEST_REPORT_RC3.md
docflow-ai/WINDOWS_UI_MANUAL_RC2_AUDIT.md
docflow-ai/app/__init__.py
docflow-ai/app/database.py
docflow-ai/app/extraction.py
docflow-ai/app/llm.py
docflow-ai/app/main.py
docflow-ai/app/pdf.py
docflow-ai/app/validation.py
docflow-ai/requirements.txt
docflow-ai/samples/EXPECTED_RESULTS.md
docflow-ai/samples/generate_samples.py
docflow-ai/samples/invoice_001.pdf
docflow-ai/samples/invoice_002.pdf
docflow-ai/samples/invoice_003.pdf
docflow-ai/static/app.js
docflow-ai/static/index.html
docflow-ai/static/style.css
docflow-ai/tests/__init__.py
docflow-ai/tests/conftest.py
docflow-ai/tests/test_api.py
docflow-ai/tests/test_docflow_independent_regressions.py
docflow-ai/tests/test_extraction.py
docflow-ai/tests/test_rc2_audit_boundaries.py
docflow-ai/tests/test_rc_acceptance.py
docflow-ai/tests/test_validation.py
```

说明：本清单对应最终 GitHub 发布副本，不是冻结 RC3 原始包（42 个文件），
也不是上一轮发布候选（47 个文件）。
相对上一轮发布候选，移除 4 个内部文件，新增 1 个最终测试报告：
移除 `PUBLISH_CANDIDATE_NOTES.md`、`ACCEPTANCE_UPDATE_20261029.md`、
`LICENSE_ADVICE.md`、`TEST_REPORT_PUBLISH_CANDIDATE.md`；
新增 `TEST_REPORT_FINAL.md`。
对读者有实际价值的安装、使用、测试、限制、许可证信息已保留在
README、NOTICE、`MANUAL_ACCEPTANCE.md` 与 `TEST_REPORT_FINAL.md` 中。

公开版清理（仅本副本，原始证据未覆盖）：
历史报告中的个人电脑用户名、绝对本地路径、内部环境名称已隐去或泛化；
历史报告中“未公开”“未推送”等表述指撰写时的状态，不代表本仓库当前公开状态；
现行结论以 README、NOTICE 与 `TEST_REPORT_FINAL.md` 为准。

推送前展示优化（仅展示，不改业务代码与测试逻辑）：
`README.md` 为英文默认首页，`README_CN.md` 为中文版，两文件顶部互链；
前端页脚由 `DocFlow AI v1` 改为 `DocFlow AI 0.1-rc3`，并增加指向
`https://github.com/xxxRhyThm/docflow-ai` 的源码链接。

许可与版本：
`LICENSE` 为 GNU AGPL-3.0 官方原文，661 行、34,523 字节，
SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0`，
未改写法律条款；项目代码仅按 AGPL-3.0-only 许可；
版权：Copyright (C) 2026 Haoming Xu，见 NOTICE 与 README，
不在 `LICENSE` 文件内（`LICENSE` 开头的 2007 年 FSF 声明属于许可证文档本身）；
PyMuPDF 按 AGPL 路径使用，未获得 Artifex 商业许可；版本 0.1-rc3。

`SECURITY_CHECK.md` / `TEST_REPORT.md` 是冻结 v0.1 的历史报告，
`SECURITY_REVIEW_RC.md` / `TEST_REPORT_RC.md` 是 RC 历史报告，
`FIXES_RC2.md` / `TEST_REPORT_RC2.md` 是 RC2 历史报告；以上文件顶部均已加
“历史报告，已被替代”标记，仅供对比，不得作为 RC3 最新结论引用。
RC3 的最新报告是 `FIXES_RC3.md` / `TEST_REPORT_RC3.md` / `TEST_LOG_RC3.txt`，
最终发布副本的最新测试报告是 `TEST_REPORT_FINAL.md`。
`INDEPENDENT_AUDIT_20261029.md` 与 `INDEPENDENT_AUDIT_RC2_20261029.md` 是
用户提供的独立审计报告（公开版清理后版本，原文另行保留）。
`WINDOWS_UI_MANUAL_RC2_AUDIT.md` 是第二轮审计附带的 Windows 手工步骤（历史文件，
不代表已通过），现行手工验收说明是 `MANUAL_ACCEPTANCE.md`。
`data/docflow.db`、`.venv/`、`__pycache__/`、`.pytest_cache/` 不在包内，
接收方需按 README 重建虚拟环境。
