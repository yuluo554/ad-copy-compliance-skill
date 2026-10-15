# HANDOFF-M1：交棒数据先行（M1）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M1.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M0 已完成，2026-10-15）

**M0 = 计划先行 + 可运行骨架，已完成**：

- 计划体系齐：`plan/00–07` 全部落盘（02 需求解读 / 03 架构选型 / 04 模块详设（含 K1–K15 全局口径）/ 05 数据计划 / 06 里程碑 / 07 交付对标+待定决策表）。
- 骨架代码齐：`scripts/check.py`（端到端通路：输入→门控加载→匹配→JSON→退出码 0/1/2；`--selftest`/`--version`）；`tests/test_check.py`（16 项）+ `tests/test_repo_gates.py`（import 白名单 / workflow YAML / fetch-depth:0，共 4 项）；`.github/workflows/ci.yml`；`requirements-dev.txt`。
- Skill 形态齐：`SKILL.md` 草案（含 `<!-- contract-fields: ... -->` 契约块，M5 一致性测试的锚）；README 已更新（状态/快速开始/路线图/文档索引）；`references/{statutes,platforms,wordlists}/README.md`、`data/samples/README.md`、`tools/README.md` 占位就位。

**证据（当轮实测）**：

- `py -3.8 -m pytest tests -q` → **20 passed**；`py -3.12 -m pytest tests -q` → **20 passed**；
- `py -3.8 -X utf8 scripts/check.py --selftest` → `SELFTEST_OK ad-copy-compliance-check 0.0.1`（3.12 同）；
- 空词表扫描（真实入口）→ `[]` + stderr 提示 + exit 0（诚实空态）；`--format text` 正常；
- workflow YAML 可解析、jobs 结构断言过；工作树跟踪文本**零 CR 字节**（.pytest_cache 除外，不入库）。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。可本机实跑的等价物已跑（双解释器全量 pytest + selftest + 门禁测试）；不可本机实跑的通路（矩阵系统/浅克隆/编码环境差异）**待首推验证**（M6 或 D-1 提前建仓时）。

---

## 2. 下一棒待办（M1：数据先行）

按 `plan/05-数据计划.md` 执行卡顺序：

1. **法条冻结**（§2）：curl 抓 samr 三部全文 → `references/statutes/raw/` + `<doc>.txt` → `tools/build_statutes.py` 抽取与逐字断言（含"第九条/国家级/最高级/最佳"）→ sha256 登记 → `--check` 位级守门 → `.gitattributes` 补 `references/statutes/raw/* -text`。
2. **词表整理**（§3）：拉取公开词表（主：`es3344520/advertising-limit-words` Dete.txt；参照：`dx2020z/ad-redline-guardian`）→ 逐条挂锚点（literal/variant）+ 风险 + 建议 → `references/wordlists/*.json`（4 类）→ **只收 verified**，候选留 `data/wordlist-candidates.md` → `tools/validate_rulepack.py` 全过 → `references/MANIFEST.json`（版本派生）。
3. **平台摘录**（§4）：淘宝/抖音/小红书/视频号逐个尝试可达通道（帮助中心/开放平台/静态子页），逐通道记录；可得则摘录冻结（注日期+出处+摘录人），不可得则如实 ⬜。
4. **台账回填**：`data/README.md` §1/§7 实测值（HTTP 状态/字节数/sha256 位置/许可）；`plan/06` M1 状态、`plan/00` 决策记录同步。
5. **勘误义务**：M0 骨架对源数据的任何猜测（文件名/条款正则/字段）被 M1 实测推翻时，同步改 `plan/04`/`plan/05` + 引擎 + 测试，并记入 `plan/00` 决策记录。
6. **收尾**：M1 DoD 验证 → plan/00·06·07 回写 → 写 `plan/HANDOFF-M2.md` → commit。

**M1 DoD**（详见 `plan/06` §1）：冻结件入仓（`-text`）；`--check` 位级一致；校验器全过；门控负例红；台账回填实测；勘误记录。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。最易踩的几条：

- **K1 契约字段**：`word, category, risk, line, col, context, suggestion`——顺序即 JSON 字段序；`SKILL.md` 契约块与其一致（M5 测试锁定）。
- **K2 匹配语义**：左→右、**长词优先**、**非重叠**（命中段消费后从段尾继续）；同词多类别各记一条；排序=(line,col,category,word)。
- **K3 位置**：行/列均 1 起、列按码点；BOM 剥离、CRLF/CR→LF 后计数。
- **K4 退出码**：0 无命中 / 1 有命中 / 2 用法或输入错误（`--exit-zero`）；锁定在 `tests/test_check.py`。
- **K5 门控**：仅 `verified` + 锚点可解析（literal 词面逐字见于条款）才加载；被拒条目 stderr 显式列出；**词表目录缺失 = exit 2**（不静默空扫）。
- **K7 零依赖零外联**：`scripts/` import 白名单（argparse/json/re/sys/pathlib），门禁测试锁定；新增 import 必须显式登记 `tests/test_repo_gates.py::ALLOWED_TOP_LEVEL_IMPORTS` 并复核。
- **D-3 落库纪律**：规则包只收挂锚点 `verified` 条目；候选词只进 `data/wordlist-candidates.md`。
- 自检词面：`scripts/check.py --selftest` 用"自检占位词甲/乙"合成串，**不要换成真实词表词**（会撞"脚本源码不得内嵌词表词面"门禁，M2 起）。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；`PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **git**：本仓 local `user.email` 已是 noreply（`yuluo554@users.noreply.github.com`）；**global 是个人 QQ 邮箱**——任何 amend/新 commit 后核对 `git log --format='%ae %ce' -1` 两字段都是 noreply。
- **gh**：已登录 yuluo554（HTTPS 协议），token scopes = gist/read:org/repo（**无 workflow scope**）→ 首推携带 workflow 文件时走 **SSH push**（或提前核验），别用 HTTPS OAuth push。
- 工作树跟踪文本保持 LF（`.gitattributes` 已配 `* text=auto eol=lf`）；写文件用 `write_bytes` 或 `newline="\n"`（Python 3.8 的 `write_text` 无 `newline` 参数）。
- 本机粗扫确认：仓库树内无本机绝对路径/用户名/QQ 号词面（保持住；HANDOFF 库内一律相对路径）。

---

## 5. M1 DoD checklist

- [ ] `references/statutes/`：3 部冻结件 + raw/ + README 来源表（URL/基准日/状态/双 sha256）；`.gitattributes` 覆盖 raw
- [ ] `tools/build_statutes.py`：抽取 + 逐字断言通过；`--check` 位级一致（从 raw 重生成 txt）
- [ ] `references/wordlists/`：4 类词表（只收 verified 挂锚点条目）；`tools/validate_rulepack.py --check` 全过
- [ ] `references/MANIFEST.json`：sha256/计数/版本派生（工具生成，非手写）
- [ ] `data/wordlist-candidates.md`：采/拒记录
- [ ] `references/platforms/`：4 份摘录件或如实 ⬜（逐通道记录）
- [ ] 门控负例测试红（pending/坏锚点/literal 未见于条款 → 不加载且列原因）——骨架已有，M1 用真实数据回归
- [ ] 双解释器 pytest 全绿（数量以当轮实测为准）
- [ ] `data/README.md` 台账回填实测；`plan/00`/`06`/`07` 状态回写
- [ ] `plan/HANDOFF-M2.md` 落盘并 commit
- [ ] commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q

# 扫描器
py -3.8 -X utf8 scripts/check.py --selftest
py -3.8 -X utf8 scripts/check.py --version
echo "文案" | py -3.8 -X utf8 scripts/check.py -
py -3.8 -X utf8 scripts/check.py 文案.txt --format text

# M1 起启用（落盘后）
py -3.8 -X utf8 tools/build_statutes.py --check     # 法条冻结位级一致
py -3.8 -X utf8 tools/validate_rulepack.py --check  # 词表校验

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
