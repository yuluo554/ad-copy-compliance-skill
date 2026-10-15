# references/statutes/ — 第一层：法条原文冻结

**状态**：✅ M1 已落盘（2026-10-15 冻结）。

来源 URL（均为 samr.gov.cn 直连静态 HTML，基准日 2026-10-15，HTTP 200）：

| 文件 | 文本 | 来源 URL（raw 同源） | 字节数（txt） | raw sha256 | txt sha256 |
|---|---|---|---|---|---|
| `advertising-law.txt` | 《中华人民共和国广告法》 | https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_5474cf75173c45d6a0379730fb4e8d97.html | 32708 | `e214072bfce625eb7ecf65d36114a069b7c43b14264a3d8ae3d50f5ffd61429a` | `9d16f896842e6577bb0d17265dde5610281223c176782a5e6c133a7a07327927` |
| `internet-ad-measures.txt` | 《互联网广告管理办法》（32 条） | https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/fgs/art/2023/art_d93a579afd45413e8576e4623fab348f.html | 15880 | `4adfe80ca884d5ebe424d3e87da610eb514bfe8fb73827b4433a9919d5b86d31` | `237e7701e69d0fdc0d2cc53915072ac16b389994b1bc77332d3b7e88baaee423` |
| `medical-ad-measures.txt` | 《医疗广告管理办法》（23 条） | https://www.samr.gov.cn/zw/zfxxgk/fdzdgknr/ggjgs/art/2023/art_6584dc1c94c2408db7c73f0b5e3d225a.html | 7139 | `e5ea2310a875411f979d76d59ee0f4e076f11b9787007b2421637d3c7c3be364` | `79a73f2ee20896f0b8b695acaa8854578124c8b75b1674ae2866bf675e3ccfc3` |

冻结方式（工具：`tools/build_statutes.py` v0.0.1，抽取器版本随 `--check` 位级守门锁定）：

- `raw/<doc>.html` 为抓取时原始字节快照；`<doc>.txt` 为确定性抽取的正文快照（仅取 `<p>` 段、剥标签、还原实体、统一"第X条"后空白为单个全角空格、LF 行尾、UTF-8）；
- 抽取器字符集处理：源页声明 `charset="utf-8"`，按 UTF-8 解码（实测无乱码，目标词面逐字命中）；
- `tools/build_statutes.py --check` 从本地 raw 重生成 txt，与库内 txt **位级一致**才算通过（sha256 相同；不联网）；
- 逐字断言已过：广告法含"第九条/国家级/最高级/最佳/医疗/保健食品/虚假广告"，互联网办法 32 条、医疗办法 23 条（条款行首定义位计数）。

锚点目标：

| 文件 | 锚点目标 |
|---|---|
| `advertising-law.txt` | 第九条 绝对化用语 / 第十六条 医疗 / 第十八条 保健食品 / 第二十八条 虚假广告 |
| `internet-ad-measures.txt` | 与广告发布/用语相关的禁止性条款 |
| `medical-ad-measures.txt` | 第六条 / 第七条 禁止性规定 |

纪律（详见 `plan/05-数据计划.md` §2 与 `plan/04-模块详设.md` §2.1）：

- **冻结字节件**：`.gitattributes` 配 `-text`（txt 与 raw 均覆盖），禁 EOL 归一化（否则克隆后 sha256 失配）；
- 禁手改；变更 = 重取 + 重生成 + 更新上表 sha256 + 记录勘误（`plan/00` 决策记录）；
- 条款抽取**只认行首定义位**（交叉引用不参与切分）；`literal` 词面必须逐字见于条款正文（引擎门控 K5）；
- ⚠️ 广告绝对化用语执法指南（一）（二）**存在但不涉及绝对化用语认定口径，勿误标为认定依据**；
- 法条文本为官方文件（不适用著作权保护），随仓冻结可复核。
