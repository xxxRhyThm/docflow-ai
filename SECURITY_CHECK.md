> 【历史报告，已被替代】本文件是 v0.1 / RC / RC2 时期的历史报告，仅供对比，不得作为 RC3 的最新结论引用。RC3 最新结论见 FIXES_RC3.md、TEST_REPORT_RC3.md、TEST_LOG_RC3.txt。

# GitHub 发布前安全与质量检查（2026-10-29，隔离工作区内完成）

## 结论：可以作为新仓库发布候选，但发布本身未执行，需你批准后才做

本检查只针对 `docflow-ai/` 隔离工作区，不涉及任何已有 GitHub 仓库。

## 检查项

- [x] 无硬编码密钥：全项目 grep 检索 api_key / password / secret / token / 私钥标记，
  唯一命中是 README_EN.md 中“无硬编码密钥”的说明文字，不是密钥本身。
- [x] 无 `.env` 文件、无凭证文件、无个人信息、无真实客户数据。
- [x] 演示数据全部虚构：Acme Supplies Ltd、Bright Office Co、Northwind Trading
  均为模拟名称，金额、日期均为演示值，PDF 第一行明确标注 MOCK INVOICE - DEMO ONLY。
- [x] 未向任何远程仓库 Push：本目录不是 git 仓库，`git status` / `git remote -v`
  均无远程记录；本次未创建远程仓库、未公开发布、未购买云服务。
- [x] 上传安全：扩展名 + `%PDF-` 头 + PyMuPDF 打开三重检查；非 PDF、伪造 PDF、
  空文件、超过 10 MB、超过 20 页、扫描无文本 PDF 均返回明确错误，不生成虚假结果。
- [x] 导出安全：仅导出已确认文档，未确认上传不会进入 CSV/JSON 导出（有测试覆盖）。
- [x] LLM 诚实性：`/api/llm` 返回 enabled=false，默认方法 rule；规则结果不冒充 LLM 结果。
- [x] 数据库不在交付包内：项目内无 `.db` 文件（实测数据库放在 /tmp），`.gitignore`
  已排除 `data/` 和 `*.db`，压缩包也排除了虚拟环境与缓存。

## 发布前仍需你确认的事（未执行）

1. 是否以新仓库名 DocFlow AI 发布（不要覆盖 EduSum-Lab 等已有仓库）。
2. 仓库设为公开还是私有；公开前请再确认 README 中的限制说明已保留。
3. 不要直接把本 Demo 暴露到公网：生产前必须加登录、权限、日志与备份。
4. 压缩包排除了 `.venv/`、`__pycache__/`、`.pytest_cache/`，接收方需按 README
   重新创建虚拟环境并安装依赖。

## 未解决问题（诚实记录）

- 运行截图未产出：本机 headless Chrome 因 浏览器平台 域名策略被阻止启动，
  未能生成真实界面截图。本次以 curl 实测（健康检查 200、首页 HTML、上传/审核/导出
  JSON 与 CSV）作为运行证据，截图需在你本地启动后自行截取，见 README。
- 仅 1 条测试警告：Starlette TestClient 弃用提示（建议 httpx2），不影响 14 个测试通过。
