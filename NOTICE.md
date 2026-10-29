# NOTICE — DocFlow AI 0.1-rc3

Copyright (C) 2026 Haoming Xu

本项目代码**仅按 GNU Affero General Public License v3.0（AGPL-3.0-only）许可，
不适用 AGPL 的 “or-later” 选项**。完整许可证文本见仓库根目录 `LICENSE`
（GNU 官方原文，未改写）。
PyMuPDF 按 AGPL 路径使用；**本项目没有获得 Artifex 商业许可，
不得宣称已获得 Artifex 商业许可。**

**版权声明的位置说明（重要修正）：**
`LICENSE` 文件是 GNU 官方许可证文本的逐字副本，其开头的
`Copyright (C) 2007 Free Software Foundation, Inc.` 是该许可证文档本身的
版权声明，**不是 DocFlow AI 代码的版权声明**。
DocFlow AI 代码的版权声明是本文件顶部与 README 中的
`Copyright (C) 2026 Haoming Xu`，故意没有把作者版权声明写进 `LICENSE`
文件内，以免改动官方许可证原文。`LICENSE` 文本中的模板措辞
（如“如何将本条款应用于新程序”中的示例）不改变本项目
AGPL-3.0-only 的选择；项目选择以本 NOTICE 与 README 的声明为准。

## 一、本项目自有内容

- 作者：Haoming Xu（版权署名以用户 2026-10-29 确认为准）
- 代码、文档、演示数据：除第三方依赖外，均为本项目自有内容。
- 演示发票：全部为虚构数据，不涉及任何真实客户、真实发票或第三方图片/字体。
  如未来加入真实客户样例或第三方材料，需另行确认授权后方可加入。

## 二、第三方依赖许可证清单（完整版，基于 RC3 虚拟环境实测）

生成方法：以 RC3 虚拟环境（Python 3.12.3）已安装的发行包元数据为准，
用 `importlib.metadata` 读取各发行包的 License 字段/分类；
`pip` 本身为工具链，不计入运行时依赖清单。
直接依赖以 `requirements.txt` 为准；其余为该环境的间接依赖。

> 注意：许可证字段以发行包元数据为准，不是对各依赖法律文本的逐字复核。
> 各依赖的完整许可证文本以其各自上游为准；本 NOTICE 只做清单与指向，
> 不替代各依赖自身的许可证文本。正式法律签约如依赖某项许可结论，
> 请以该依赖上游文本为准，必要时咨询律师。

### 直接依赖（requirements.txt，锁定版本）

| 依赖 | 版本 | 许可证（元数据） | 说明 |
|---|---|---|---|
| FastAPI | 0.162.0 | MIT | Web 框架 |
| Uvicorn | 0.54.0 | BSD-3-Clause | ASGI 服务器 |
| Pydantic | 2.14.1 | MIT | 数据校验 |
| PyMuPDF | 2.0 | Dual Licensed — GNU AFFERO GPL 3.0 或 Artifex 商业许可 | 本发布选择 AGPL 路径；未取得 Artifex 商业许可 |
| python-multipart | 0.0.32 | Apache-2.0 | multipart 解析 |
| pytest | 9.2.0 | MIT | 测试（开发/测试依赖） |
| httpx | 0.28.1 | BSD-3-Clause | 测试客户端依赖 |

### 间接依赖（RC3 虚拟环境实测版本）

| 依赖 | 版本 | 许可证（元数据） |
|---|---|---|
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| certifi | 2026.10.23 | MPL-2.0 |
| click | 8.5.0 | BSD-3-Clause |
| flatbuffers | 25.12.19 | Apache 2.0 |
| h11 | 0.16.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.1 | MIT |
| networkx | 3.7 | BSD-3-Clause |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| onnxruntime | 1.31.1 | MIT License |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| protobuf | 7.36.2 | 3-Clause BSD License |
| psutil | 7.2.2 | BSD-3-Clause |
| pydantic_core | 2.50.1 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| PyYAML | 6.0.3 | MIT |
| starlette | 1.10.0 | BSD-3-Clause |
| tabulate | 0.10.0 | MIT |
| typing-inspection | 0.4.4 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |

### PyMuPDF 及其子包：上游许可说明与已安装包元数据的区分

本节把“上游公开说明”与“本机已安装包的元数据”分开写，
两者不一致时以何者为准，必须说清楚，不能只写一个笼统结论。

**PyMuPDF 2.0（主包）：**
- 上游公开说明：PyMuPDF 与 MuPDF 由 Artifex 提供，双许可——
  GNU AGPL 或 Artifex 商业许可；PyMuPDF 官方 FAQ 亦说明
  PyMuPDF4LLM 与 PyMuPDF、MuPDF 采用相同许可（AGPL 或 Artifex 商业许可）。
  上游来源：PyMuPDF 官方文档 FAQ（pymupdf.readthedocs.io）。
- 已安装包元数据（RC3 虚拟环境）：`License: Dual Licensed — GNU AFFERO GPL 3.0
  or Artifex Commercial License`，与上游说明一致。
- 本项目选择：AGPL 路径；未取得 Artifex 商业许可。

**pymupdf4llm 2.0：**
- 上游公开说明：与 PyMuPDF、MuPDF 相同，双许可——AGPL 或 Artifex 商业许可
  （PyMuPDF 官方 FAQ；其上游发行说明亦指向 AGPL v3.0 与 Artifex 商业许可
  两种选择）。本项目选择 AGPL 路径。
- 已安装包元数据（RC3 虚拟环境）：**未标注许可证字段**。
  这是元数据缺失，不是与上游不同的许可；本 NOTICE 以更具体的上游说明为准，
  同时如实记录元数据缺失这一事实，不隐瞒。
- 本项目代码本身不直接 import 该子包（核心提取只用 `pymupdf`），
  但它会随 PyMuPDF 安装一同出现，因此列出。

**pymupdf_layout 2.0：**
- 上游公开说明：**本次核查未找到针对该发行包名称的单独上游许可页面**；
  公开资料仅将其描述为 PyMuPDF 发行中的 Layout 模块，
  未给出与主包不同的单独许可声明。
- 已安装包元数据（RC3 虚拟环境）：**未标注许可证字段**。
- 本 NOTICE 的处理：**不为该子包单独断言一个许可证**；
  它在 PyMuPDF 2.0 的 `Requires-Dist` 中列为必需组件，随 PyMuPDF 安装一同出现，
  本项目代码本身不直接 import 它。
  如需法律层面的单独结论，请以 PyMuPDF 上游的 COPYING / 发行许可文件为准
  进一步核对，不得仅凭“随主包安装”就断言它与主包许可完全相同。

## 三、各依赖的许可义务要点（摘要，非法律意见）

- MIT / BSD / Apache-2.0 / PSF-2.0 / MPL-2.0 / CC0 等宽松许可：
  一般要求保留版权声明与许可证声明；Apache-2.0 还包含专利授权条款；
  MPL-2.0 对 MPL 许可文件本身的修改有文件级 copyleft 要求，
  本项目未修改这些依赖的源码。
- AGPL-3.0（本项目自有代码 + PyMuPDF 路径）：
  分发本项目源码或改编版本时，必须按 AGPL-3.0 提供对应源码与许可证；
  作为网络服务向用户提供修改版本时，AGPL 的网络条款会被触发。
  本 Demo 当前只设计为本地 127.0.0.1 运行，不提供在线服务。
- 本项目未修改任何第三方依赖的源码；未把任何依赖的许可证文本
  改写后冒充为该依赖的原文。

## 四、版权声明保留（修正后的准确位置）

- 本项目自有代码的版权声明：Copyright (C) 2026 Haoming Xu，
  **见本 NOTICE 顶部与 README，不在 `LICENSE` 文件内**。
  `LICENSE` 内开头的 2007 年 FSF 声明属于许可证文档本身，不得误读为
  DocFlow AI 代码的版权归属，也不得把作者声明写进 `LICENSE` 以免改动官方原文。
- 本项目代码仅按 AGPL-3.0-only 许可；`LICENSE` 官方原文未改写，
  其模板措辞不改变这一 only 选择。
- 第三方依赖的版权声明归各自作者所有，本 NOTICE 不改变其归属。
- 如发现本清单与某依赖上游实际许可不符，以上游为准，并应立即修正本文件。
