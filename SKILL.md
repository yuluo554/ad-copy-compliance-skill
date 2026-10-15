---
name: ad-copy-compliance-skill
description: 广告文案合规自查（《广告法》第九条绝对化用语 + 平台违禁词）。粘贴推广文案（商品标题/详情页/直播话术/朋友圈/短视频脚本），逐句标红命中词并给出可替换的合规改写；扫描用确定性词表（命中位置可复现），语境判定分层进行（confirmed/exempt/uncertain），不做法律意见。触发词：广告法、极限词、绝对化用语、违禁词、文案合规自查、违规词检测。
---

# 广告文案极限词合规体检（Skill 正式版 v0.0.1）

> 规则包版本：`references/MANIFEST.json` 的 `rulepack_version`（从冻结件派生，禁手写）。
> 工具版本：`scripts/check.py --version`（当前 `0.0.1`）。里程碑与状态见 `plan/06-里程碑.md`。

## 何时使用

用户要检查一段（或一批）推广文案里有没有《广告法》第九条绝对化用语、医疗/保健食品/行业违禁
表述，或需要"发出前自查"、给文案挑违规词、要替换建议时使用本 skill。
适用输入：商品标题、详情页、直播话术、朋友圈文案、短视频脚本等 UTF-8 纯文本。

## 工作流

1. **扫描（确定性，零 LLM、零网络）**：
   `python scripts/check.py <文案文件>`（或 stdin）→ 命中集合 JSON（见下方契约）。
2. **语境判定（可选）**：按 `references/judgment-protocol.md`（M3 交付，行为规范以协议文档为准）对每条命中给
   `confirmed` / `exempt` / `uncertain` + 理由 + 依据锚点；**只注释、不改位置**（不新增/删除/移动命中）；
   判定关闭或失败时**降级**：所有命中标 `uncertain`，并在输出 meta 中显式声明"仅扫描结果，未经语境判定"。
   三态下限（协议 §1）：`exempt` 必须给理由＋锚点（不承认默认豁免）；`uncertain` 必须说明
   "为何无法判定"（非垃圾桶）。
3. **呈现**：逐句标红 + 替换建议（`suggestion`）+ 依据条款 + **免责声明**（措辞见下方"隐私与免责"）。

## 输出契约（与 `scripts/check.py` 逐字段一致）

<!-- contract-fields: word category risk line col context suggestion -->

命中集合为 JSON 数组（`ensure_ascii=False`，缩进 2），每条形如：

```json
[{"word": "……", "category": "……", "risk": "……", "line": 1, "col": 1,
  "context": "……", "suggestion": "……"}]
```

| 字段 | 类型 | 语义 |
|---|---|---|
| `word` | str | 命中的词表项（原样） |
| `category` | str | 绝对化用语 / 医疗违禁 / 保健食品违禁 / 行业违禁 |
| `risk` | str | high / medium / low（展示为 高/中/低） |
| `line` / `col` | int | 命中位置（行/列均 1 起、列按 Unicode 码点；CRLF/CR 归一为 LF、BOM 剥离后计数；可在原文逐字定位） |
| `context` | str | 命中处上下文窗口（默认左右各 10 字符，纯子串、不添加省略号——可逐字回查） |
| `suggestion` | str | 词表内置的确定性替换建议（不做自由生成） |

契约字段**固定 7 个、仅有这 7 个**；`verdict` 类字段只出现在判定层注释副本（Agent 会话内，
按协议只追加 `verdict` / `verdict_reason` / `verdict_anchor`，不动上表任何字段）。诊断信息
（未启用条目清单、词表缺失提示）走 stderr，不污染 stdout 机器契约。

## 参数与退出码

```
python scripts/check.py [输入文件|-] [--wordlists-dir DIR] [--statutes-dir DIR]
                        [--context N] [--format json|text] [--exit-zero]
                        [--version] [--selftest]
```

- 输入：UTF-8 文本文件，或 stdin（省略参数或 `-`）；空输入合法（零命中）。
- `--format json`（默认，机器契约）；`--format text`（人读展示，非机器契约）。
- `--exit-zero`：有命中时仍以退出码 0 结束（纯报告用途）。
- `--selftest`：内置合成数据自检（CI 冒烟），成功打印 `SELFTEST_OK`。

退出码（K4）：`0` = 扫描完成且零命中；`1` = 扫描完成且有命中；
`2` = 用法或输入错误（文件不存在 / 非 UTF-8 / 参数错误 / 词表目录缺失）。

词表门控：仅 `status=="verified"` 且锚点可解析的词条生效；被拒条目逐条列于 stderr
（未启用清单＋原因），词表目录不存在直接 exit 2（不静默空扫）。

## 基准（一条命令复现评测）

```
python tools/bench.py    # → BENCH PASS 148/148 exact-match (required=1.00)
```

命中集合（词＋类别＋行＋列）对 148 条冻结样例**双向精确比对**，验收门槛
`exact_match_required = 1.0` 随 `data/samples/manifest.json` 下发（数据非代码）。

## 隐私与免责

- **纯本地、零上传**：本 skill 自身不含任何联网/外发通路；扫描层零网络、零第三方依赖。
- 判定层由宿主 Agent 在会话内按协议执行，可随时要求"只扫描、不判定"。
- **本工具为辅助自查提示，不构成法律意见、不构成合规保证、不构成行政认定**；正式结论以主管部门口径与专业律师意见为准。
- **零命中 = "未检出词表命中"，不等于合规**。

## 边界

- 不自动发布、不自动改写上线（只给建议供人决策）；
- 词表为公开整理+法条锚点核对所得，**非官方**（"非官方整理，法条原文为准"）；平台规则为人工摘录快照，非官方实时口径；
- 法条/词表/样例为冻结件（禁手改，变更走生成器＋位级守门），文档引用而不复制其内容；
- 规则与限制以仓库 `README.md` 与 `plan/` 文档为准。
