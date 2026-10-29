# DocFlow AI 0.1-rc3 最终 GitHub 发布副本测试报告（2026-10-29）

## 本次重跑结果（本次实际执行，非引用他人结论）

- 执行目录：最终 GitHub 发布副本（独立副本，非冻结 RC3 原包、非上一轮发布候选目录）
- 环境：Python 3.12.3，RC3 虚拟环境的 pytest，锁定依赖与 `requirements.txt` 一致
- 结果：**91 passed，0 failed**，唯一警告为 Starlette TestClient 弃用提示
  （建议改用 httpx2，与业务逻辑无关）
- 组成（与 RC3 相同，未扩大测试范围）：
  test_api 6、test_extraction 3、test_validation 5、test_rc_acceptance 11、
  test_docflow_independent_regressions 5、test_rc2_audit_boundaries 61
- 本次整理为非功能性整理：文档、NOTICE、README 状态文字、前端页脚文字；
  代码功能、技术架构、版本标识 0.1-rc3 均未改动。
  前端页脚仅增加一行版权、AGPL-3.0-only 与源码提示文字，不改变接口与逻辑，
  上述 91 项测试已在该改动后重跑通过。

## 证据来源区分（不得混淆）

- **91 项：本次重跑。** 上述结果是本轮在最终副本中实际运行 pytest 得出的，
  可直接引用为本次结论。
- **125 项：Work 独立复核报告结论，不是本次重跑。**
  该结论由独立复核报告：原有 91 项 + 新增 34 项补充测试 = 125 项全部通过，
  以及 Windows Chrome 核心项与 Excel 公式样例验证。
  截至本报告撰写时，新增 34 项的测试文件与完整证据包尚未在本旁聊收到，
  因此 125 项、Windows Chrome 核心项、Excel 公式样例仍记为独立复核结论，
  **不得写成本次已重跑 125 项**。收到证据后需另行验证并更新本报告。

## 仍未执行（不得写成通过）

- 浏览器文件选择/上传流程
- 非法文件浏览器 UI 提示（空 PDF、伪造 PDF、txt 等；API 拒绝不等于 UI 提示验收）
- `MANUAL_ACCEPTANCE.md` 整体（仅核心项有独立复核结论）
- WPS CSV 打开/另存/重开
- 完整 Windows Python 3.12 锁定依赖安装记录 / `pip freeze`
- 全量依赖漏洞扫描、模糊测试、并发与资源耗尽测试

## 已知低优先级问题

- UI-20261029-01：确认成功后旧警告可能暂留显示；
  不影响保存值和导出值；复现细节与“披露或修复”的选择仍待作者决定，
  本轮未声称已修复。

## 许可与版本

- 版本：0.1-rc3（未升级为 0.1）
- 项目代码：GNU AGPL-3.0-only；`LICENSE` 为 GNU 官方原文，未改写
- PyMuPDF：按 AGPL 路径使用，未获得 Artifex 商业许可
- 作者版权：Copyright (C) 2026 Haoming Xu，见 `NOTICE.md` 与 README，
  不在 `LICENSE` 文件内（`LICENSE` 开头的 2007 年 FSF 声明属于许可证文档本身）

## 历史报告说明

- 本仓库保留的历史报告（RC、RC2、RC3）已做公开版清理：
  个人电脑用户名、绝对本地路径、内部环境名称已隐去或泛化；
  原始审计证据另行保留，未覆盖冻结 RC3 原包与上一轮发布候选 ZIP。
- 历史报告中“未公开”“未推送”等表述指撰写时的状态，不代表本仓库的
  当前公开状态；现行结论以 README、NOTICE 与本报告为准。
- 内部 staging 文件（发布候选说明、验收更新、历史许可证建议）未收入
  本公开仓库；对读者有实际价值的安装、使用、测试、限制、许可证信息
  已保留在 README、NOTICE、`MANUAL_ACCEPTANCE.md` 与本报告中。

## 推送前展示优化后重跑（2026-10-29）

- 仅展示改动：英文 README 为默认首页、中文版改为 README_CN.md 并互链；
  前端页脚由 DocFlow AI v1 改为 DocFlow AI 0.1-rc3，并增加仓库源码链接。
  业务代码、测试逻辑、技术架构、版本 0.1-rc3 均未改动。
- 重跑结果：**91 passed，0 failed**，唯一警告仍为 Starlette TestClient 弃用提示。
- 125 项仍为独立复核报告结论，不是本轮重跑；其余未执行项与已知问题见上文。
