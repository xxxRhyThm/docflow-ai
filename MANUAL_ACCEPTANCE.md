# 本地运行与 Windows 手工验收操作说明（RC3）

## 一、本地运行（Windows，PowerShell）

```powershell
# 1. 解压 docflow-ai-rc3.zip，得到 docflow-ai-rc3 文件夹
#    先核对交付消息中给出的 SHA-256，与下载的 ZIP 文件比对（不要只看文件名）：
#    (Get-FileHash -LiteralPath .\docflow-ai-rc3.zip -Algorithm SHA256).Hash

# 2. 进入新目录（不要在旧 RC2 目录上覆盖，避免混淆两个版本的数据）
Set-Location .\docflow-ai-rc3

# 3. 创建虚拟环境并安装锁定依赖（需要 Python 3.11+，建议 Python 3.12）
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip check

# 4. 生成演示 PDF（可选，已随包附带 3 份）
& .\.venv\Scripts\python.exe samples\generate_samples.py

# 5. 启动服务器（只监听本机，不要加 --host 0.0.0.0）
$env:DOCFLOW_DB_PATH = "$PWD\manual-acceptance.db"
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 6. 打开浏览器
# http://127.0.0.1:8000/
```

停止：Ctrl+C。删除 `manual-acceptance.db` 可清空本次演示数据。
记录：验收日期、Windows 版本、Python 版本、浏览器名称/版本、
Excel/WPS 名称与版本、各步结果和截图。只使用虚构数据。

## 二、自动化测试（Windows，PowerShell）

```powershell
& .\.venv\Scripts\python.exe -m pytest -v
```

预期：91 passed，0 failed（原 RC2 的 30 个 + 第二轮独立边界测试 61 个）。
唯一警告是 Starlette TestClient 弃用提示，不影响结果。
依赖必须与 `requirements.txt` 锁定版本一致（fastapi 0.162.0、uvicorn 0.54.0、
pydantic 2.14.1、PyMuPDF 2.0、python-multipart 0.0.32、pytest 9.2.0、httpx 0.28.1）；
间接依赖未完整锁定，本环境实测 Starlette 1.10.0，Windows 环境请在测试日志中
记录实际 `pip freeze` 输出以便比对。

## 三、浏览器手工验收步骤（公开版：部分已验证，部分仍未执行）

**公开版修正（2026-10-29）：** 下一段旧表述已被本段取代。
旧表述“第二轮独立审计环境同样报告浏览器被策略阻止”不准确：
第二轮（RC2）审计并未报告新的浏览器策略阻止，它是未尝试完整浏览器/Excel 验收，
且原文明确指出此前限制属于历史记录，不能用来描述本次未尝试的操作。
第一轮是本地 Chromium 打开 `http://127.0.0.1` 被 `ERR_BLOCKED_BY_ADMINISTRATOR` 阻止；
开发环境（无头浏览器）是 headless Chrome 被 浏览器平台 策略阻止；三者不得混写。

**现行状态（按独立复核结论，用户报告，本次未重跑）：**
Windows 真实 Chrome 已验证核心审核、无效修改保留旧值、JSON/CSV 下载、
XSS 按文本显示；本机 Excel 已验证公式样例打开、另存、关闭、重开后仍为文本。
**仍未执行：** 浏览器文件选择/上传、非法文件 UI 提示、WPS、
Windows 锁定依赖完整 pip freeze、全依赖漏洞扫描、模糊测试、并发测试。
以下步骤作为整体仍未全部完成，**不得把 API 测试结果或核心项结果写成整份 UI 验收通过**。
以下步骤请在 Windows 本机按顺序逐项打勾，顺序本身就是逻辑的一部分：

1. [ ] 打开 http://127.0.0.1:8000/ ，页面有上传、文档列表、导出按钮，
   初始列表为空；刷新页面正常。新数据库首次启动应为空，已有数据说明
   没有使用本次独立库。
2. [ ] 上传 `samples\invoice_001.pdf`，再点它的 Review，原值确认：
   列表出现 INV-2026-001，1240.5，无警告，状态 confirmed。
3. [ ] 上传 `samples\invoice_003.pdf`：列表出现 INV-2026-003，0.0，
   并显示金额错误警告，状态 pending。
4. [ ] 此时点 Export CSV / JSON：用记事本打开，确认**只含已确认的 001，
   不含未确认的 003**。这一步验证“未审核不导出”。
5. [ ] 点击 invoice_003 的 Review，把总金额改为 320.00，点确认：
   状态变为 confirmed，警告消失。
6. [ ] 再次点 Export CSV：用记事本打开，确认**同时含 001 和 003**，
   003 数值为 320 或 320.0（CSV 不保证保留两位尾随零）。
7. [ ] 无效修改分两种情况，预期不同，必须分开验证：
   - [ ] 7a 对**未确认文档**：上传 `samples\invoice_002.pdf`（不确认），
     在审核页分别尝试金额 0、-5、空供应商、只有空格的供应商、
     日期 2026-1-2、2026-02-30、币种 JPY；每次其他字段恢复有效值后再测下一项；
     均应显示 Review failed，仍为 pending，导出不含 002。
   - [ ] 7b 对**已确认文档**：回到已确认的 invoice_003，在审核页把总金额改成 0
     再点确认：应显示 Review failed，**旧的已确认版本被保留**，
     列表仍 confirmed，重新点 Review 应重新加载旧值 320，导出仍为 320。
     失败后的编辑框可能暂时仍显示输入的 0，不能据此判断数据库被修改。
8. [ ] 再次上传 invoice_001：应看到 duplicate_invoice_number 警告，
   两个条目有不同 ID。当前政策允许重复号确认并同时导出；
   如果选择确认该条，后续导出行数会增加，不能再按“只有两条”判断。
9. [ ] 上传空的 empty.pdf，应有上传失败提示；上传伪造 PDF 或 txt 应拒绝。
   文件选择器若只显示 PDF，切换“所有文件”；若浏览器限制无法选择，
   用后文 API 补充验证并记录 UI 未覆盖。页面不应白屏。
   不要把“点击未选中文件时的浏览器必填提示”当成服务器拒绝测试。
10. [ ] 打开 002 的审核表单，恢复有效日期、币种、金额 875；供应商填
    `<img src=x onerror=alert(1)>` 并确认。列表应把完整字符串作为文本显示；
    不出现图片、弹窗。刷新页面、再次 Review，仍应是普通文本。
    此步成功后 002 已确认，会进入导出。
11. [ ] 对 003 把供应商改为 `=2+2`，保留金额 320，确认并导出 CSV。
    用记事本确认该单元格带前置单引号 `'=2+2`。依次可用 `+2+2`、`-2+2`、
    `@SUM(1,1)` 重复；逗号应由 CSV 正确加引号。
12. [ ] 用实际目标 Excel/WPS 打开 CSV，确认上述供应商是文本，没有被算成数值、
    公式或触发链接提示。查看公式栏或“定位条件→公式”，该供应商格不应被识别为公式。
    保留原导出，再另存为 CSV，关闭并重新打开复验；记录应用版本、打开方式和另存格式。
    出现计算或公式恢复即判失败，不要只凭“没有弹窗”通过。
    **本项在本环境未执行，Windows 本机完成前必须标为“未执行”。**

## 四、PowerShell API 补充验证（RC2 / RC3 修复，服务窗口保持开启）

此部分在**另一个 PowerShell 窗口**运行，不要用 Bash 的反斜杠续行。
先用浏览器上传一张 002，不要确认，记下该条 ID：

```powershell
$documentId = 这里改成该条数字ID
$baseUrl = 'http://127.0.0.1:8000'
$reviewUrl = "$baseUrl/api/documents/$documentId/review"

function Invoke-RcReviewCheck([string]$body) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($body)
    try {
        $result = Invoke-WebRequest -Uri $reviewUrl -Method Post -ContentType 'application/json' -Body $bytes
        Write-Host "HTTP $([int]$result.StatusCode)"
        $result.Content
    } catch {
        if ($_.Exception.Response) {
            Write-Host "HTTP $([int]$_.Exception.Response.StatusCode)"
            $_.ErrorDetails.Message
        } else { throw }
    }
    Invoke-RestMethod "$baseUrl/api/documents/$documentId" | ConvertTo-Json -Depth 6
}

$valid = '{"invoice_number":"INV-2026-002","vendor":"Demo Vendor","invoice_date":"2026-10-20","currency":"EUR","total_amount":875.0}'
Invoke-RcReviewCheck ($valid.Replace('875.0', 'NaN'))
Invoke-RcReviewCheck ($valid.Replace('875.0', 'Infinity'))
Invoke-RcReviewCheck ($valid.Replace('875.0', '-Infinity'))
Invoke-RcReviewCheck ($valid.Replace('Demo Vendor', '   '))
Invoke-RcReviewCheck ($valid.Replace('2026-10-20', '2026-1-2'))
```

以上五次应全部 HTTP 400，记录始终 pending，金额仍为原始 875；导出不能含本条 ID。
对已经 confirmed 的文档重复无效请求时，预期为 400 且保留旧的 confirmed 状态和值，
不能要求它变回 pending。

## 五、RC3 新增问题复验（PowerShell，原始 RC2 预期失败，RC3 应拒绝）

```powershell
# 原始 RC2 会 HTTP 200，金额变成 1.0 且 confirmed；RC3 应为 422，记录不变
Invoke-RcReviewCheck ($valid.Replace('875.0', 'true'))

# 原始 RC2 会 HTTP 200，导出全角年份；RC3 应为 400，记录不变
Invoke-RcReviewCheck ($valid.Replace('2026-10-20', '２０２６-10-20'))

# 原始 RC2 会 HTTP 500，记录不变；RC3 应为 422，记录不变
Invoke-RcReviewCheck ($valid.Replace('"Demo Vendor"', 'NaN'))
```

错误千分位 PDF 的回归已包含在独立测试文件中；运行测试文件可复现
`1,2,3.45 → 123.45` 在 RC2 的行为，在 RC3 中金额应为 None。
空白字段、非零填充日期的完整请求见上文第四节，不要只测 NaN 一项。

## 六、结束与发布门槛

- [ ] 服务窗口按 Ctrl+C 停止，刷新浏览器确认不再提供服务。
- [ ] 对原始 ZIP 再运行 Get-FileHash，校验值应与交付消息中给出的一致。
- [ ] 保存验收记录；保留独立演示目录供复核，不上传生成的数据库、下载记录或虚拟环境。
- [ ] 四项新增回归已修复、LICENSE 与 PyMuPDF 授权路径已明确、README_EN 测试数量已改正，
  再评估正式公开版本。浏览器或 Excel 任一未执行，应明确标“未执行”，不能填通过。

## 七、已知限制（手工验收时也请注意）

- 只支持本项目定义的单一发票格式；其他版式、扫描件会返回缺失字段或明确错误。
- 默认不调用 LLM；`/api/llm` 返回 enabled=false。
- 无用户认证，只能本机运行，不要暴露到公网。
- 不能宣称为生产级 SaaS。
- 重复发票号只标注警告、不拒绝；若两条同号都被确认，导出会同时出现两条，需人工去重。
- 上传 10 MB 限制只作用于路由读取阶段和最终接受/拒绝决定；Starlette 会先解析
  multipart 并落盘临时文件，不能声称网络接收立即中断或全程磁盘/CPU 都有同样上限；
  公开服务需另加入口请求总量限制，本 Demo 没有。
- CSV 公式注入的单引号防护是缓解层，Excel/WPS 实测未执行前不能称为所有表格软件的绝对保证。
- 未提供仓库级 LICENSE；PyMuPDF 为 AGPL v3 / 商业双许可证，未来公开或闭源收费前
  授权路径已按本仓库 `LICENSE` 与 `NOTICE.md` 确定：AGPL-3.0-only，PyMuPDF 按 AGPL 路径。
- 版本标识统一为 0.1-rc3；旧报告中的 1.0.0 均为历史标识。
