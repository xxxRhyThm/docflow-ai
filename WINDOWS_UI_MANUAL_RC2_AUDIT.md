# DocFlow AI RC2：Windows UI 手工验收

本文件是**待执行步骤**，不代表浏览器或 Excel 已通过。本次审计实际完成的是源码、自动测试及真实 HTTP 服务验证。RC2 尚有四项已复现问题，见独立审计报告；完成本清单也不会自动消除这些问题。

## A. 新副本启动，不改原 ZIP

需要 Python 3.12、Edge/Chrome。下面用独立目录和新数据库，不删除已有演示数据；依赖下载需要联网。若 `py -3.12` 不存在，先安装相应 Python，再运行。

在 PowerShell 中逐段执行：

```powershell
$sourceZip = Join-Path $env:USERPROFILE 'Downloads\docflow-ai-rc2.zip'
(Get-FileHash -LiteralPath $sourceZip -Algorithm SHA256).Hash
# 应为 FBCA1E99D131F3C44F8FD15040C7F817174999526A8FABF19D48942DB9D5C3CF

$manualRoot = Join-Path $env:USERPROFILE 'Documents\Codex\DocFlow-RC2-Manual'
if (Test-Path -LiteralPath $manualRoot) { throw '请换一个新的验收目录名，保留已有记录。' }
Expand-Archive -LiteralPath $sourceZip -DestinationPath $manualRoot
Set-Location (Join-Path $manualRoot 'docflow-ai-rc2')
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip check
& .\.venv\Scripts\python.exe -m pytest -v
# 原有测试应为 30 passed

$env:DOCFLOW_DB_PATH = Join-Path $manualRoot 'manual-acceptance.db'
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

保持该窗口运行，另开浏览器进入 http://127.0.0.1:8000/ 。无需执行 Activate.ps1；样例 PDF 已包含在 samples 中，无需重新生成。若 8000 被占用，可换端口，并同步修改后文 URL。

记录：验收日期、Windows 版本、Python 版本、浏览器名称/版本、Excel/WPS 名称与版本、各步结果和截图。只使用虚构数据。

## B. 浏览器顺序验收

1. [ ] 页面有上传、文档列表、导出按钮，初始列表为空；刷新页面正常。新数据库首次启动应为空，已有数据说明没有使用本次独立库。
2. [ ] 上传 samples\invoice_001.pdf。应显示发票号 INV-2026-001、金额 1240.5、pending，审核表单自动展开，无校验警告。点 Confirm & save，状态变为 confirmed。
3. [ ] 上传 samples\invoice_003.pdf。金额 0、pending，并有金额错误。保留未确认状态。
4. [ ] 点 Export confirmed (JSON) 和 CSV。下载后用记事本查看：只有 001，不能含 003。CSV 另有一行表头。
5. [ ] 点 003 的 Review，把金额改为 320.00 后确认。应 confirmed，返回成功。再导出：现在 001、003 两条都存在，003 数值为 320 或 320.0；CSV 不保证保留两位尾随零。
6. [ ] 上传 samples\invoice_002.pdf，保持 pending。分别尝试金额 0、-5、空供应商、只有空格的供应商、日期 2026-1-2、2026-02-30、币种 JPY。每次其他字段恢复有效值后再测下一项；均应显示 Review failed，仍为 pending，导出不含 002。
7. [ ] 对已 confirmed 的 003，把金额改为 0 后确认。应失败；列表仍 confirmed；重新点 Review，应重新加载旧值 320；导出仍为 320。失败后的编辑框可能暂时仍显示输入的 0，不能据此判断数据库被修改。
8. [ ] 再上传一次 001，应显示 duplicate_invoice_number 警告。两个条目有不同 ID。当前政策允许重复号确认并同时导出；如果选择确认该条，后续导出行数会增加，不能再按“只有两条”判断。
9. [ ] 上传空的 empty.pdf，应有上传失败提示；上传伪造 PDF 或 txt 应拒绝。文件选择器若只显示 PDF，切换“所有文件”；若浏览器限制无法选择，用后文 API 补充验证并记录 UI 未覆盖。页面不应白屏。不要把“点击未选中文件时的浏览器必填提示”当成服务器拒绝测试。
10. [ ] 打开 002 的审核表单，恢复有效日期、币种、金额 875；供应商填 `<img src=x onerror=alert(1)>` 并确认。列表应把完整字符串作为文本显示；不出现图片、弹窗。刷新页面、再次 Review，仍应是普通文本。此步成功后 002 已确认，会进入导出。
11. [ ] 对 003 把供应商改为 `=2+2`，保留金额 320，确认并导出 CSV。用记事本确认该单元格带前置单引号 `'=2+2`。依次可用 `+2+2`、`-2+2`、`@SUM(1,1)` 重复；逗号应由 CSV 正确加引号。
12. [ ] 用实际目标 Excel/WPS 打开 CSV，确认上述供应商是文本，没有被算成数值、公式或触发链接提示。查看公式栏或“定位条件→公式”，该供应商格不应被识别为公式。保留原导出，再另存为 CSV，关闭并重新打开复验；记录应用版本、打开方式和另存格式。出现计算或公式恢复即判失败，不要只凭“没有弹窗”通过。也核对日期、中文及金额；Excel 自动日期显示变化与原始 CSV 内容要分开记录。

## C. PowerShell API 补充：RC2 修复

此部分在**另一个 PowerShell 窗口**运行，服务窗口保持开启。使用新的 pending 文档，避免把已确认记录误当 pending。先用浏览器上传一张 002，不要确认，记下该条 ID：

```powershell
$documentId = 这里改成该条数字ID
$baseUrl = 'http://127.0.0.1:8000'
$reviewUrl = "$baseUrl/api/documents/$documentId/review"

function Invoke-Rc2ReviewCheck([string]$body) {
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
Invoke-Rc2ReviewCheck ($valid.Replace('875.0', 'NaN'))
Invoke-Rc2ReviewCheck ($valid.Replace('875.0', 'Infinity'))
Invoke-Rc2ReviewCheck ($valid.Replace('875.0', '-Infinity'))
Invoke-Rc2ReviewCheck ($valid.Replace('Demo Vendor', '   '))
Invoke-Rc2ReviewCheck ($valid.Replace('2026-10-20', '2026-1-2'))
```

以上五次应全部 HTTP 400，record 始终 pending，金额仍为原始 875；导出不能含本条 ID。不要把可能已有的同号 confirmed 条目当成该条导出记录。按 ID 核对。

对已经 confirmed 的文档重复无效请求时，预期为 400 且保留旧的 confirmed 状态和值，不能要求它变回 pending。

## D. 新增问题复验（原始 RC2 预期失败）

以下步骤用于验证报告，**不是成功验收条件**。使用上述专门创建的文档：

```powershell
# 原始 RC2 会 HTTP 200，金额变成 1.0 且 confirmed，应在修复后拒绝
Invoke-Rc2ReviewCheck ($valid.Replace('875.0', 'true'))

# 原始 RC2 会 HTTP 200，导出全角年份，应在修复后拒绝或按明确政策规范化
Invoke-Rc2ReviewCheck ($valid.Replace('2026-10-20', '２０２６-10-20'))

# 原始 RC2 会 HTTP 500；记录不变。修复后应为可解释的 400/422
Invoke-Rc2ReviewCheck ($valid.Replace('"Demo Vendor"', 'NaN'))
```

错误千分位 PDF 的回归已包含在另附 Python 测试中；运行独立测试文件可复现 `1,2,3.45 → 123.45`。原始包当前应为 **57 passed, 4 failed**，修复后的新副本应 61 项通过，同时原有 30 项保持通过。

## E. 结束与发布门槛

- [ ] 服务窗口按 Ctrl+C 停止，刷新浏览器确认不再提供服务。
- [ ] 对原始 ZIP 再运行 Get-FileHash，校验值应与开头相同。
- [ ] 保存验收记录；保留独立演示目录供复核，不上传生成的数据库、下载记录或虚拟环境。
- [ ] 四项新增回归已修复、LICENSE 与 PyMuPDF 授权路径已明确、README_EN 测试数量已改正，再评估正式公开版本。浏览器或 Excel 任一未执行，应明确标“未执行”，不能填通过。
