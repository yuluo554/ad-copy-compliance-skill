# HANDOFF-M3：判定协议（M3）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M3.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M2 已完成，2026-10-15）

**M2 = 确定性扫描器，已完成**：

- **DFA 化**：`scripts/check.py` `scan_text()` 升级为前缀树（嵌套 dict，`build_dfa()` 编译）；
  语义严格保持 K2（左→右、长词优先、非重叠、同词多类别各记一条、排序 (line,col,category,word)）。
- **等价对拍**：`tests/test_scan_dfa.py` 内嵌旧实现逐字拷贝作基线，对真实词表全量 133 词
  构造 210 语料（词粘连拼接/模板文案/边界退化）× 3 上下文窗口（0/3/10）逐字节一致；
  另测乱序不变性（30 次乱序唯一输出）——同长同位竞争在词面上不可能（同切片只等于一个词面），
  同词异类多条被全局排序归一，新实现对词条传入顺序不敏感。
- **全量测试**：`tests/test_real_wordlist.py`（CLI 层，真实词面运行时实算）：真实命中/退出码三态/
  `--exit-zero`/`--context 0`/部分坏文件其余正常加载＋未启用清单/两次运行逐字节一致/位置回读定位；
  `tests/test_scan_dfa.py`（模块层）：对拍/长词优先非重叠（运行时选前缀词对）/同词异类/
  BOM·CRLF·CR 位置/上下文窗口边界/空输入。
- **词面不内嵌门禁（K6 初版）**：`tests/test_repo_gates.py::test_scripts_do_not_embed_wordlist_tokens`
  ——token 从 `references/wordlists/*.json` 运行时实算（`tests/conftest.py::rulepack_word_tokens`）；
  **只查 ≥3 字词面（决策 D-10）**：2 字词面实测撞"绝对化用语"的"绝对"、文档串"首个"，碰撞不可收敛。
  另有占位词防撞测试（自检占位词甲/乙/丙/丁 ∉ 词表）。
- **变异验证**：3 处注入全红——①非重叠破坏（`pos += 1`）→ 对拍红；②退出码破坏（命中退 0）→
  CLI 红（9 failed）；③门控破坏（跳过 verified 检查）→ 门控负例红；还原后全绿。
- **台账回写**：`plan/00`（D-10 决策、台账扫描器行 ✅、里程碑 M2 ✅）、`plan/06` M2 行 ✅、
  `plan/07` 验收门（门禁/变异验证两行 ✅、门控/测试行注 M2 快照）。

**证据（当轮实测）**：

- `py -3.8 / py -3.12 -m pytest tests -q` → **36 passed**（双解释器；M0 基线 20 + M2 新增 16）；
- `build_statutes.py --check` / `gen_wordlists.py --check` / `validate_rulepack.py --check`（words=133 files=4）全过；
- 真实词表端到端：`echo "超级无敌最好的产品，全国第一，保证治愈，包治百病，稳赚不赔躺赚" |
  py -3.12 -X utf8 scripts/check.py - --format text` → 6 条命中（跨 3 类别，位置正确）exit 1；
  良性输入 → `[]` + exit 0；`--selftest` 双解释器 OK；
- stderr 未启用清单为空（133 条全部通过门控）。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。

---

## 2. 下一棒待办（M3：判定协议）

按 `plan/06` M3 行执行：

1. **协议文档**：`references/judgment-protocol.md` 六节齐——三态定义（`violated`/`exempt`/`uncertain`）、
   理由字段（`verdict_reason`）、锚点字段（`verdict_anchor`）、适用边界（何语境可豁免/何语境必须 uncertain）、
   降级路径（LLM 关闭→纯扫描；LLM 失败→全 `uncertain`＋声明）、免责与措辞（K12：零命中 ≠ 合规）。
2. **字段口径**：判定层只改 `verdict/verdict_reason/verdict_anchor`（K10），不动 `word/line/col` 等
   K1 扫描字段——结构测试锁定（注释不改位置测试）。
3. **SKILL.md 工作流对齐**：扫描→判定→输出的流程块与协议一致（M5 一致性测试前先人工对齐）。
4. **降级路径测试**：判定关闭→纯扫描输出不变；判定失败→全部命中标 `uncertain`＋降级声明显式。
5. **三态示例**：对一条真实命中给出三态各一例（agent 会话内演示，写进协议文档附录）。
6. **收尾**：M3 DoD 验证 → plan/00·06·07 回写 → 写 `plan/HANDOFF-M4.md` → commit（noreply 核对）。

**M3 DoD**（详见 `plan/06` M3 行）：协议齐六节；降级路径测试（关闭→纯扫描；失败→全 uncertain＋声明）；
注释不改位置测试；对一条命中给出三态示例。

**注意**：M3 是"协议文档＋测试锁定"，不实现 LLM 调用（本项目自身无外发通路，K10/D-2：
判定由宿主 Agent 在会话内执行，协议文档是其行为规范）。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。最易踩的几条：

- **K1 契约字段**：`word, category, risk, line, col, context, suggestion`——顺序即 JSON 字段序；
  `SKILL.md` 契约块与其一致（M5 一致性测试锁定）。M3 判定层新增字段只许 `verdict/verdict_reason/verdict_anchor`。
- **K2 匹配语义**：左→右、**长词优先**、**非重叠**（命中段消费后从段尾继续）；同词多类别各记一条；
  排序=(line,col,category,word)。已由前缀树实现（`build_dfa`），对拍基线冻结在 `tests/test_scan_dfa.py`。
- **K3 位置**：行/列均 1 起、列按码点；BOM 剥离、CRLF/CR→LF 后计数。
- **K4 退出码**：0 无命中 / 1 有命中 / 2 用法或输入错误（`--exit-zero`）；锁定在测试。
- **K5 门控**：仅 `verified` + 锚点可解析（literal 词面逐字见于条款）才加载；被拒条目 stderr 显式列出；
  **词表目录缺失 = exit 2**；**部分文件坏 = 其余正常加载 + 坏文件进未启用清单**（M2 测试锁）。
- **K6 词面不内嵌**：`scripts/` 源码不得逐字出现规则包词面（**≥3 字，D-10**）；测试构造词面输入
  一律运行时实算（`tests/conftest.py`）；自检占位词"自检占位词甲/乙"合成串不要换成真实词表词。
- **K7 零依赖零外联**：`scripts/` import 白名单（argparse/json/re/sys/pathlib）；新增 import 显式登记
  `tests/test_repo_gates.py::ALLOWED_TOP_LEVEL_IMPORTS`（tests/ 引入 conftest/pytest 不受限——门禁只查 scripts/）。
- **K10 判定层**：只改 `verdict/verdict_reason/verdict_anchor`，不动 `word/line/col`；不可用→全
  `uncertain`＋降级声明（M3 核心）。
- **K15 冻结纪律**：法条 raw/txt、词表 JSON、MANIFEST 均冻结件——变更只能走生成器重生成＋
  `--check` 位级一致＋勘误记录，**禁手改**。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；`PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **Python 3.8 语法坑**：`Path.write_text` 无 `newline` 参数（写文件用 `write_bytes`）；re.sub 替换串不能用 `\u3000` 转义（用 lambda）。
- **pytest 根目录**：`tests/conftest.py` 已就位（M2 起）；测试间共享用 `from conftest import ...`（rootdir=仓库根，tests/ 无 `__init__.py`）。
- **git**：local `user.email` 已是 noreply；**global 是个人 QQ 邮箱**——commit 后核对 `git log --format='%ae %ce' -1` 两字段均 noreply。
- **gh**：已登录 yuluo554（HTTPS），token 无 workflow scope → 首推带 workflow 文件走 **SSH push**。
- 工作树跟踪文本保持 LF（`.gitattributes` `* text=auto eol=lf`）；冻结件已配 `-text`（txt 与 raw）。
- **网络**：raw.githubusercontent.com 直连被重置；可用通道 = api.github.com（base64）、samr.gov.cn（带 UA）、weixin.qq.com readtemplate。临时文件在 `%TEMP%/wordlist-src/`（不入库）。
- **变异验证操作法**：先 `cp scripts/check.py /tmp/check.py.bak` → 改 → 跑红 → `cp` 还原 → 全绿复验
  （备份须在改动后做，否则还原会连带丢掉本轮合法改动——M2 实操踩过，靠 `git diff` 核对发现）。
- 仓库树内无本机绝对路径/用户名/QQ 号词面（保持住；HANDOFF 库内一律相对路径）。

---

## 5. M3 DoD checklist

- [ ] `references/judgment-protocol.md` 六节齐（三态/理由/锚点/边界/降级/免责）
- [ ] 判定层字段口径结构测试（只加 verdict 三字段、不改扫描字段、注释不改位置）
- [ ] 降级路径测试（关闭→纯扫描；失败→全 uncertain＋声明）
- [ ] SKILL.md 工作流块与协议对齐（人工核对＋记录）
- [ ] 三态示例各一（真实命中，协议附录）
- [ ] 双解释器 pytest 全绿（数量以当轮实测为准）
- [ ] `--check` 三件套仍全过（build_statutes / gen_wordlists / validate_rulepack）
- [ ] plan/00·06·07 状态回写
- [ ] `plan/HANDOFF-M4.md` 落盘并 commit
- [ ] commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q

# 扫描器（M2 起前缀树 DFA 引擎）
py -3.8 -X utf8 scripts/check.py --selftest
echo "文案" | py -3.8 -X utf8 scripts/check.py -
py -3.8 -X utf8 scripts/check.py 文案.txt --format text

# 冻结件守门三件套
py -3.8 -X utf8 tools/build_statutes.py --check     # 法条位级一致
py -3.8 -X utf8 tools/gen_wordlists.py --check      # 词表生成器位级一致
py -3.8 -X utf8 tools/validate_rulepack.py --check  # 规则包校验

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
