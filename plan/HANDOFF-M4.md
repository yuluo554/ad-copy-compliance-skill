# HANDOFF-M4：真值基准（M4）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M4.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M3 已完成，2026-10-15）

**M3 = 判定协议，已完成**：

- **协议文档**：`references/judgment-protocol.md` 六节齐——§0 输入/输出（注释副本＋meta 声明）、
  §1 三态定义、§2 适用边界（语境特征→判定对照表）、§3 降级路径（off/failed/on 三状态＋铁律）、
  §4 理由与锚点字段口径、§5 免责与统一措辞（K12）；附录 A = 对"国家级"一条真实命中
  给出三态各一例（七个扫描字段逐字一致，只追加三字段）；附录 B = 降级 meta 示例。
- **三态命名口径（D-11）**：全仓既定口径 = `confirmed`/`exempt`/`uncertain`
  （plan/01/04、SKILL.md、README、data/README 共 5 处）；HANDOFF-M3 中 "violated" 为笔误不采，
  已登记 `plan/00` 决策 D-11，测试锁定协议文档不得出现 "violated"。
- **结构测试**：`tests/test_judgment_protocol.py`（14 项）——协议六节存在性；
  判定字段白名单 = verdict/verdict_reason/verdict_anchor 且与扫描 7 字段契约无交集（K1/K10）；
  注释副本不改位置/条数/顺序、(line,col) 仍可在原文逐字定位（K3 不失效）；
  三态下限（confirmed/exempt 锚点必给、uncertain 必须说明为何无法判定——非垃圾桶）；
  SKILL.md 工作流块与协议对齐（术语/不改位置/降级声明措辞）。
- **降级路径测试**：off → 全 `uncertain` ＋ meta.note 显式"仅扫描结果，未经语境判定"；
  failed → 同＋失败原因；降级产物扫描字段逐字不动；扫描器 stdout 契约保持 7 字段无 verdict 字段。
  判定层执行者 = 宿主 Agent（D-2），测试内含协议的**可执行参考实现**（annotate/apply_judgment/degrade）
  作为行为规范的可证伪编码，非运行时组件——扫描器 `check.py` 一行未改。
- **变异验证**：3 处注入全红——①注释副本改位置（col+1）→ 5 failed；
  ②降级误标 `confirmed` → 降级测试红；③降级声明清空 → 显式声明测试红；
  还原后全绿（`git diff --stat` 核对还原干净）。
- **台账回写**：`plan/00`（D-11 决策、判定协议行 ✅、里程碑 M3 ✅）、`plan/06` M3 行 ✅、
  `plan/07`（提交材料 #4 行、判定语义两行 ✅ M3 快照、测试全绿行 M3 快照 50 项）。

**证据（当轮实测）**：

- `py -3.8 / py -3.12 -m pytest tests -q` → **50 passed**（双解释器；M2 基线 36 + M3 新增 14）；
- `--check` 三件套全过（build_statutes 位级一致 3 部 / gen_wordlists / validate_rulepack words=133 files=4）；
- `--selftest` 双解释器 OK；真实词表端到端 6 条命中 exit 1（扫描器行为与 M2 快照一致）。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。

---

## 2. 下一棒待办（M4：真值基准）

按 `plan/06` M4 行与 `plan/04` §5 执行：

1. **样例与真值**：`data/samples/cases.json`（冻结构）＋`manifest.json`
   （计数/双数覆盖/采样清单/验收门槛）。样例 schema 见 plan/04 §5.1
   （`expect_hits` 精确集合、`expect_verdict`、**禁 `observed` 类字段**）。
2. **生成器 `tools/gen_cases.py`**：确定性枚举构造（禁 random/set 迭代序/时钟，Python 3.8 兼容）；
   每生效词条 ≥1 条单词命中样例＋手工语义样例（多词/负例/位置边界/同词异类/判定类）；
   `--check` 重生成位级一致；`--write-manifest` 派生 manifest。
3. **基准运行器 `tools/bench.py`**：加载 cases → 运行时实算（真喂 `check.py` 扫描函数）→
   与 `expect_hits` 集合精确比对（双向）→ 人读摘要＋机读 JSON；
   exit 0 全对 / exit 1 有不匹配 / exit 2 用法配置错误；
   验收门槛随 `manifest.acceptance`（`exact_match_required=1.0`，缺失即 exit 2 不回落默认值）。
4. **探活三形态**（每套件配可证伪测试，打到端到端入口）：①篡改一条真值→必红；
   ②注入空词表→必红；③坏锚点注入→相关样例必红。
5. **覆盖口径**：按 plan/04 §5.2 ①–⑤ 登记 manifest（总数/采样数双数＋采样清单；
   抽样非穷举显式声明）。
6. **收尾**：M4 DoD 验证 → plan/00·06·07 回写 → 写 `plan/HANDOFF-M5.md` → commit（noreply 核对）。

**M4 DoD**（详见 `plan/06` M4 行）：`bench` exit 0（exact-match）；三形态探活必红；
双数覆盖登记；门槛随 manifest；真值无 `observed`。

**注意**：

- 离线基准只断言**扫描层**（`expect_verdict` 样例仅供有 LLM 时评估，不进 bench 断言）。
- 假品牌白名单（K8，`data/README.md` §3）；不引真实品牌案例。
- **冻结纪律（K15）**：cases.json/manifest.json 为冻结件——禁手改，变更走 `gen_cases.py`
  重生成＋`--check`；`.gitattributes` 冻结件 `-text` 配置参照 `references/` 现状。
- 判定层是 Agent 会话内行为（无运行时组件）——bench 不涉及 verdict 断言，别给 check.py 加 LLM。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。M4 最易踩的几条：

- **K8 合成数据**：假品牌白名单；真值只存"输入与期望"（禁 `observed`）。
- **K9 基准**：命中集合**精确匹配**（词＋位置，双向集合相等）；覆盖度"总数/采样数"双登记；
  门槛随 manifest 下发（数据非代码）；探活必红且打到端到端入口。
- **K15 冻结纪律**：cases/manifest 冻结、生成器重生成＋`--check` 位级守门、禁手改。
- **K1/K2/K3/K4**：扫描契约/匹配语义/位置/退出码均已锁测试——bench 断言的对象就是这些语义，
  别改扫描器（改了 36 项 M0–M2 基线测试会红）。
- **K6 词面不内嵌**：`tools/` 未在门禁范围（只查 `scripts/`），但测试构造词面输入仍应
  运行时实算（conftest 纪律）；gen_cases 从词表 JSON 读词面，不在源码内嵌词面。
- **K7 零依赖**：`tools/` 同样零第三方（除 pytest 测试外）；`tools/` 现有 3 个生成器是样式参照。
- **D-10 词面门禁口径**：≥3 字词面门禁只查 `scripts/`；gen_cases 若需在文档串举例，
  用"自检占位词"式合成词，不用真实词面。
- **D-11 三态命名**：`confirmed/exempt/uncertain`（样例 `expect_verdict` 枚举用这套）。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；`PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **Python 3.8 语法坑**：`Path.write_text` 无 `newline` 参数（写文件用 `write_bytes` 或 `io.open`）；
  re.sub 替换串不能用 `\u3000` 转义（用 lambda）；gen_cases 要 3.8/3.12 双解释器可跑。
- **pytest 根目录**：`tests/conftest.py` 已就位；测试间共享用 `from conftest import ...`（rootdir=仓库根）。
- **git**：local `user.email` 已是 noreply；**global 是个人 QQ 邮箱**——commit 后核对
  `git log --format='%ae %ce' -1` 两字段均 noreply。
- **gh**：已登录 yuluo554（HTTPS），token 无 workflow scope → 首推带 workflow 文件走 **SSH push**。
- 工作树跟踪文本保持 LF（`.gitattributes` `* text=auto eol=lf`）；冻结件已配 `-text`
  （txt 与 raw）——**cases.json/manifest.json 落库时记得补 `-text` 条目**。
- **网络**：raw.githubusercontent.com 直连被重置；可用通道 = api.github.com（base64）。
  M4 零外联，用不到网络。
- **变异验证操作法**：先 `cp <目标> $TEMP/<名>.bak`（**备份须在改动后做**，否则还原会连带丢掉
  本轮合法改动——M2 实操踩过）→ 改 → 跑红 → `cp` 还原 → 全绿复验＋`git diff --stat` 核对。
  M3 实测：测试文件被还原后 Edit 工具会报 "file has been modified"——需 Read 再改或用 `py -X utf8 -c` 脚本化替换。
- 仓库树内无本机绝对路径/用户名/QQ 号词面（保持住；HANDOFF 库内一律相对路径）。

---

## 5. M4 DoD checklist

- [ ] `data/samples/cases.json` ＋ `manifest.json` 落库（冻结件＋`-text`）
- [ ] `tools/gen_cases.py`（确定性枚举＋`--check` 位级一致＋`--write-manifest`）
- [ ] `tools/bench.py`（exact-match 双向比对＋退出码三语义＋门槛随 manifest）
- [ ] `bench` exit 0（全绿）
- [ ] 三形态探活必红（篡改真值/空词表/坏锚点，打到端到端入口）
- [ ] 覆盖"总数/采样数"双登记＋采样清单；真值无 `observed` 字段
- [ ] 双解释器 pytest 全绿（数量以当轮实测为准）
- [ ] `--check` 三件套仍全过（build_statutes / gen_wordlists / validate_rulepack）＋ gen_cases `--check`
- [ ] plan/00·06·07 状态回写
- [ ] `plan/HANDOFF-M5.md` 落盘并 commit
- [ ] commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q

# 扫描器（M2 起 DFA 引擎；M3 未改其一行）
py -3.8 -X utf8 scripts/check.py --selftest
echo "文案" | py -3.8 -X utf8 scripts/check.py -

# 冻结件守门（M4 起新增 gen_cases --check）
py -3.8 -X utf8 tools/build_statutes.py --check
py -3.8 -X utf8 tools/gen_wordlists.py --check
py -3.8 -X utf8 tools/validate_rulepack.py --check

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
