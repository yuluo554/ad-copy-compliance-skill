# HANDOFF-M2：交棒确定性扫描器（M2）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M2.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M1 已完成，2026-10-15）

**M1 = 数据先行，已完成**：

- **法条冻结（3 部）**：curl 200×3 抓 samr.gov.cn（带 UA/超时/重试）→ `references/statutes/raw/<doc>.html`（原始字节快照）→ `tools/build_statutes.py` 确定性抽取 → `<doc>.txt`（UTF-8/LF/仅 `<p>` 段/实体还原/"第X条"后统一全角空格）；逐字断言过（广告法含"第九条/国家级/最高级/最佳/医疗/保健食品/虚假广告"；互联网办法 32 条、医疗办法 23 条行首定义位计数）；`--check` 从 raw 重生成位级一致 ✅；双 sha256 登记进 `references/statutes/README.md` 来源表；`.gitattributes` 补 `references/statutes/raw/* -text`。
- **词表（4 类 133 条，全 verified 挂锚点）**：主来源 `Dete.txt`（191 词去重）经 **api.github.com base64 通道**获取（raw.githubusercontent.com 直连实测被重置 ❌，D-7 勘误）；参照 `banned-words.md`（MIT）。冻结生成器 `tools/gen_wordlists.py`（literal 词面逐字断言内置，`--check` 位级一致）产出 `absolute-terms`(50)/`medical`(14)/`health-food`(22)/`industry`(47)；采拒全记录 `data/wordlist-candidates.md`（191→采 67+参照增补 66＝133 入包，拒 124 分七类理由）。
- **校验器与清单**：`tools/validate_rulepack.py`（schema/枚举/文件↔类别/同文件同词唯一/锚点解析（条款抽取+literal 词面包含）/suggestion 非空/码点排序/`--check` 0/1/2/`--write-manifest`）全过 ✅；`references/MANIFEST.json` 由工具写入（版本派生 `df8832223387`，禁手写）。
- **平台摘录（1/4 冻结，3/4 如实 ⬜）**：视频号 ✅ `references/platforms/shipinhao.md`（官方 readtemplate 静态模板页可达，34720 字节实测，要点化摘录+条号保持原文+性质声明）；淘宝/抖音/小红书逐通道实测均 JS 渲染壳/接口签名墙，逐通道记录见 `references/platforms/README.md`（D-8）。
- **台账回填**：`data/README.md` §1（#5/#6 通道与计数实测、平台清单行）、`plan/05` §7 网络通道实测、`plan/00`（承诺-证据台账 3 行、里程碑 M1 ✅、决策记录新增 D-7/D-8/D-9）、`plan/06` M1 ✅、`plan/07` 验收门 checkbox。

**证据（当轮实测）**：

- `py -3.8 -m pytest tests -q` → **20 passed**；`py -3.12` 同 → **20 passed**；
- `build_statutes.py --check` / `gen_wordlists.py --check` / `validate_rulepack.py --check` 双解释器全过；
- 真实词表端到端：`echo "超级无敌最好的产品，全国第一，保证治愈，包治百病，稳赚不赔躺赚" | py -3.12 -X utf8 scripts/check.py - --format text` → 6 条命中（跨 3 类别，位置正确），退出码 1；良性输入 → `[]` + exit 0；
- stderr 未启用清单为空（133 条全部通过门控）。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。

---

## 2. 下一棒待办（M2：确定性扫描器）

按 `plan/06` M1 行的 M2 DoD 执行：

1. **DFA 化**：`scripts/check.py` `scan_text()` 由"逐位置 startswith"升级 DFA（双数组/嵌套 dict 均可），语义严格保持 K2（左→右、长词优先、非重叠、同词多类别各记一条、排序 (line,col,category,word)）——升级前后对全部词表词做**等价性对拍**（旧实现 vs 新实现对同一输入输出逐字节一致）。
2. **全量测试**：`tests/test_check.py` 从合成占位扩到真实词表子集（挑 literal 词：国家级/最高级/最佳/治疗/治愈/保证治愈/保本/保收益/无风险/治疗功能/疾病预防），覆盖位置语义（BOM/CRLF/CR/行首行尾/跨行）、长词优先、非重叠、同词异类（跨文件同词）、退出码三态、`--exit-zero`、`--context` 边界。
3. **门控/失败路径**：坏 JSON 文件继续跳过并列入未启用清单（已有）；补充"部分文件坏→其余文件正常加载"的真实词表场景测试。
4. **确定性验收**：同一输入两次运行 stdout/stderr/退出码逐字节一致（测试锁）。
5. **词面不内嵌门禁（初版）**：`tests/test_repo_gates.py` 增"scripts/ 源码不得出现规则包词面"（token 从 `references/wordlists/*.json` 运行时实算）；自检占位词"自检占位词甲/乙"不受影响。
6. **收尾**：M2 DoD 验证 → plan/00·06·07 回写 → 写 `plan/HANDOFF-M3.md` → commit（noreply 核对）。

**M2 DoD**（详见 `plan/06` M2 行）：全部测试绿（双解释器）；同一输入两次运行逐字节一致；命中位置逐字可定位；退出码三语义锁测试；变异验证过。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。最易踩的几条：

- **K1 契约字段**：`word, category, risk, line, col, context, suggestion`——顺序即 JSON 字段序；`SKILL.md` 契约块与其一致（M5 一致性测试锁定）。
- **K2 匹配语义**：左→右、**长词优先**、**非重叠**（命中段消费后从段尾继续）；同词多类别各记一条；排序=(line,col,category,word)。DFA 化不得改变该语义。
- **K3 位置**：行/列均 1 起、列按码点；BOM 剥离、CRLF/CR→LF 后计数。
- **K4 退出码**：0 无命中 / 1 有命中 / 2 用法或输入错误（`--exit-zero`）；锁定在 `tests/test_check.py`。
- **K5 门控**：仅 `verified` + 锚点可解析（literal 词面逐字见于条款）才加载；被拒条目 stderr 显式列出；**词表目录缺失 = exit 2**。
- **K7 零依赖零外联**：`scripts/` import 白名单（argparse/json/re/sys/pathlib）；新增 import 显式登记 `tests/test_repo_gates.py::ALLOWED_TOP_LEVEL_IMPORTS`（tools/ 不受限，但 build_statutes/gen_wordlists/validate_rulepack 均仅用标准库，保持）。
- **冻结纪律（K15）**：法条 raw/txt、词表 JSON、MANIFEST 均冻结件——变更只能走生成器重生成＋`--check` 位级一致＋勘误记录，**禁手改**。
- 自检词面："自检占位词甲/乙"合成串，**不要换成真实词表词**（M2 词面门禁上线后直接撞红）。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；`PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **Python 3.8 语法坑**：`Path.write_text` 无 `newline` 参数（写文件用 `write_bytes`）；re.sub 替换串不能用 `\u3000` 转义（用 lambda）。
- **git**：local `user.email` 已是 noreply；**global 是个人 QQ 邮箱**——commit 后核对 `git log --format='%ae %ce' -1` 两字段均 noreply。
- **gh**：已登录 yuluo554（HTTPS），token 无 workflow scope → 首推带 workflow 文件走 **SSH push**。
- 工作树跟踪文本保持 LF（`.gitattributes` `* text=auto eol=lf`）；冻结件已配 `-text`（txt 与 raw）。
- **网络**：raw.githubusercontent.com 直连被重置；可用通道 = api.github.com（base64）、samr.gov.cn（带 UA）、weixin.qq.com readtemplate。临时文件在 `%TEMP%/wordlist-src/`（不入库）。
- 仓库树内无本机绝对路径/用户名/QQ 号词面（保持住；HANDOFF 库内一律相对路径）。

---

## 5. M2 DoD checklist

- [ ] DFA 升级 + 新旧实现等价对拍（真实词表全量）
- [ ] `tests/test_check.py` 真实词表子集 + 位置/边界/退出码全量
- [ ] 部分坏文件场景：其余文件正常加载 + 未启用清单列出
- [ ] 同一输入两次运行逐字节一致（测试锁）
- [ ] 词面不内嵌门禁（scripts/ 源码 vs 词表 token 实算）
- [ ] 双解释器 pytest 全绿（数量以当轮实测为准）
- [ ] `--check` 三件套仍全过（build_statutes / gen_wordlists / validate_rulepack）
- [ ] plan/00·06·07 状态回写
- [ ] `plan/HANDOFF-M3.md` 落盘并 commit
- [ ] commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q

# 扫描器（M1 起词表已生效）
py -3.8 -X utf8 scripts/check.py --selftest
echo "文案" | py -3.8 -X utf8 scripts/check.py -
py -3.8 -X utf8 scripts/check.py 文案.txt --format text

# 冻结件守门三件套
py -3.8 -X utf8 tools/build_statutes.py --check     # 法条位级一致
py -3.8 -X utf8 tools/gen_wordlists.py --check      # 词表生成器位级一致
py -3.8 -X utf8 tools/validate_rulepack.py --check  # 规则包校验
py -3.8 -X utf8 tools/validate_rulepack.py --write-manifest  # 更新 MANIFEST（计数/版本派生）

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
