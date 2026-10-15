# 广告文案极限词合规体检 Skill

> 粘贴任何推广文案（商品标题 / 详情页 / 直播话术 / 朋友圈 / 短视频脚本），逐句标红《广告法》第九条绝对化用语与平台违禁词，给出可替换的合规改写——**扫描用确定性词表/规则，判定用 LLM 分层，不靠模型拍脑袋**。

**形态**：Agent Skill（Claude Code / Codex 可调用）＋ CLI（`scripts/check.py`）· 纯本地 · 零上传 · 零第三方依赖
**状态**：✅ 已发布 v0.0.1（[Release](https://github.com/yuluo554/ad-copy-compliance-skill/releases/tag/v0.0.1)）——规则包（133 词逐条挂锚点）、DFA 扫描器、判定协议、真值基准（148 cases exact-match 1.0）、交付包装与发布三件套（tag＋Release 附产物＋[发布留档](plan/RELEASE-M6.md)）均已落库；CI 三 job 全绿（run 38736015173）

---

## 这是什么

一个可以被 AI Agent 调用的**广告文案合规自查 Skill**。它把《广告法》第九条绝对化用语与各平台违禁词做成**三层规则包**，用确定性扫描器给出**可复现的命中位置**，再由 LLM 做**语境豁免/品类识别**的分层判定，最后给出**可替换的合规改写建议**。

这是纯 prompt 做不到的三件事：

1. **可复现的命中位置**——同一句文案，命中的词、类别、行号列号永远一致；
2. **可批量 CI 调用**——机器可读 JSON 输出，可进流水线做文案门禁；
3. **可版本化规则包**——法条冻结文本、平台规则、分类词表与代码分离，规则可审计可更新。

---

## 快速开始

环境：Python 3.8+；运行时零第三方依赖，无需安装。以下命令逐条实测可跑
（Windows 中文控制台建议把 `python` 换成 `py -X utf8`）：

```bash
python scripts/check.py --selftest        # 内置合成数据自检 → SELFTEST_OK
python scripts/check.py --version         # 版本
echo "示例文案。" | python scripts/check.py -   # 扫描（stdin）→ 命中集合 JSON（stdout）
echo "本款产品是全效之王，销量第一。" > 文案.txt
python scripts/check.py 文案.txt          # 扫描文件 → 命中集合 JSON；有命中退出码 1
python tools/bench.py                     # 真值基准 → BENCH PASS 148/148 exact-match
```

> 扫描命中示例（字段序即机器契约，与 SKILL.md 契约块逐字段一致）：
> `[{"word": "……", "category": "……", "risk": "……", "line": 1, "col": 5, "context": "……", "suggestion": "……"}]`

开发与测试：

```bash
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

---

## 三层规则包

```
references/
├── statutes/    # 第一层：法条原文冻结（《广告法》§9/§16/§18/§28、互联网广告办法、医疗广告办法）
├── platforms/   # 第二层：分平台规则（淘宝 / 抖音 / 小红书 / 视频号，人工摘录冻结）
├── wordlists/   # 第三层：分类词表（绝对化用语 / 医疗 / 保健食品 / 行业，逐条带条款锚点）
└── MANIFEST.json  # 规则包清单（sha256 + 计数 + 版本派生）——M1 落盘
```

> ⚠️ `wordlists/` 中的公开整理词表**非官方**，标注"**非官方整理，法条原文为准**"；`platforms/` 为**人工摘录**，注摘录日期与出处，不声称官方实时口径。

---

## 输出契约（`scripts/check.py`）

命中集合 JSON，每条形如：

```json
[{ "word": "...", "category": "...", "risk": "...", "line": 1, "col": 12,
   "context": "...", "suggestion": "..." }]
```

`line` / `col` 为命中位置（可在原文逐字定位）；`suggestion` 为词表内置的确定性替换建议。
退出码：`0` 零命中 / `1` 有命中 / `2` 用法或输入错误。LLM 分层判定只在此之上追加 `verdict`（confirmed / exempt / uncertain），**不改位置**。

---

## 项目结构

```
├── SKILL.md                 # Skill 主入口（M5 定稿；契约块与 check.py HIT_FIELDS 一致性测试锁定）
├── scripts/check.py         # 确定性扫描器（M2 DFA 化；零依赖零网络）
├── references/              # 三层规则包：法条冻结 / 平台摘录 / 词表 133 词（M1 落盘，冻结件）
├── references/judgment-protocol.md  # 判定协议（M3：三态 confirmed/exempt/uncertain + 降级路径）
├── data/                    # 数据台账 + 真值基准（M4：148 cases 冻结 + manifest 门槛）
├── tools/                   # 生成器/校验器/基准运行器（--check 位级守门；不进运行通路）
├── docs/技术报告.md          # 技术报告（M5：六主题）
├── tests/                   # pytest 测试（含门禁/探活/契约一致性）
├── plan/                    # 计划体系 00–07 + 跨会话交接快照 HANDOFF-M*.md
└── .github/workflows/ci.yml # CI（win×{3.8,3.12} + ubuntu×{3.12}；未接远端，待首推验证）
```

---

## 路线图

| 里程碑 | 内容 | 状态 |
|---|---|---|
| M0 | 计划先行 + 可运行骨架 | ✅ |
| M1 | 数据先行：法条冻结 / 词表整理（挂锚点）/ 平台摘录 | ✅ |
| M2 | 确定性扫描器（DFA + 全量测试 + 门控/失败路径） | ✅ |
| M3 | LLM 分层判定协议（语境豁免 / 降级路径） | ✅ |
| M4 | 真值基准（合成样例 + 植入真值 + 一条命令复现） | ✅ |
| M5 | 交付：SKILL.md 定稿 + README + 技术报告 + 测试/CI | ✅ |
| M6 | 发布：tag + Release + 发布留档（GitHub 公开仓库） | ✅ v0.0.1（[发布留档](plan/RELEASE-M6.md)；仓库可见性切换待用户确认） |

---

## 项目文档

| 文档 | 内容 |
|---|---|
| [plan/01-题目文档.md](plan/01-题目文档.md) | 十段式题面（介绍 / 任务 / 材料 / 评分 / 锚点 / 边界） |
| [plan/00-README总览.md](plan/00-README总览.md) | 总览、决策记录、承诺-证据台账、里程碑 |
| [plan/02-需求解读.md](plan/02-需求解读.md) | 痛点→能力转译、FR 清单、边界与非目标 |
| [plan/03-架构与技术选型.md](plan/03-架构与技术选型.md) | 分层架构、目录结构、技术选型、确定性边界 |
| [plan/04-模块详设.md](plan/04-模块详设.md) | ①–⑤ 模块详设 + 全局口径 K 清单 |
| [plan/05-数据计划.md](plan/05-数据计划.md) | 三层规则包 + 合成真值的执行卡 |
| [plan/06-里程碑.md](plan/06-里程碑.md) | 里程碑、DoD、演示命令、收尾纪律 |
| [plan/07-交付对标.md](plan/07-交付对标.md) | 提交材料/评分对标、验收门 checklist、待定决策表 |
| [data/README.md](data/README.md) | 数据台账（查证三态+URL+基准日）与数据纪律 |

---

## 边界与非目标

- **不做法律意见**：本工具是辅助自查，**不构成法律意见、不构成合规保证、不构成行政认定**；正式结论以主管部门口径与专业律师意见为准。**零命中 ≠ 合规**。
- **不自动发布/改文案上线**：只输出体检结论与替换建议，供人决策。
- **隐私红线**：纯本地处理、零上传；判定层可关闭（关闭后降级为纯扫描）。
- **不引用真实品牌违规案例**：基准与演示一律使用假品牌名/假商品白名单。

---

## 免责声明

本项目的输出为基于规则与词表的**合规自查提示**，不构成法律意见，不构成对任何文案合法性的保证或认定。使用者的发布决策与其后果由使用者自负；正式合规结论请咨询专业律师或以主管部门口径为准。

## 许可

[MIT](LICENSE)
