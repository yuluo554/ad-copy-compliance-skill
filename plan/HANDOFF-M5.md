# HANDOFF-M5：交付包装（M5）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M5.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M4 已完成，2026-10-15）

**M4 = 真值基准，已完成**：

- **冻结件**：`data/samples/cases.json`（**148 cases**）＋`manifest.json`——均已配
  `.gitattributes` `-text`（K15 冻结纪律：禁手改，变更走 `tools/gen_cases.py` 重生成＋`--check`）。
  样例构成：逐词全量 133（`pos-*`，每生效词条 1 条单词命中）＋多词 2＋负例 3＋位置边界
  （手工 3：BOM/CRLF/CR＋补组 3：行首/行尾/跨行）＋判定类 8（`expect_verdict`：
  confirmed 2 / exempt 2 / uncertain 2＋2 非命中判定参考）；同词异类如实登记 0
  （本规则包无跨文件同词，不虚构样例）。
- **真值纪律（D-12）**：`expect_hits` 不手写——`tools/gen_cases.py` 内置**独立朴素
  oracle**（逐词 find，与 DFA 引擎不共用代码）运行时实算；生成期守卫：oracle 与引擎
  对拍（全部入库样例＋全词面拼接语料逐位一致）、模板不混入旁词面（全词表对拍）、
  负例零命中、单词样例位置精确断言。真值无 `observed` 类字段（bench 加载与测试双侧拒绝）。
  **注意**：`scan_text` 本身不做规范化——BOM/CR 归一在入口 `_normalize_text`；
  bench 与 oracle 对拍均须先 `_normalize_text` 再喂引擎（M4 实测踩过：守卫逮住
  BOM/CR 样例列位错一行）。
- **词面纪律**：`gen_cases.py` 源码不内嵌词表词面——手工样例用占位模板
  （`{law0}/{abs_price}/{hf_safe}` 等），运行时按**类别码点序下标**从冻结词表解析
  （`_pick_words`）；测试扩展 K6 门禁查 `tools/gen_cases.py`（`tests/test_cases_bench.py`）。
  词表重排/增删须同步核对 `_pick_words` 下标语义注释（守卫会逮错位）。
- **bench**：`tools/bench.py`——运行时实算（真喂 `check.py` 生效词条＋`scan_text`），
  命中集合（word+category+line+col）**双向精确比对**；退出码 0 全对 / 1 有不匹配或
  门控拦截 / 2 配置错误（**门槛缺失即 2，不回落代码默认值**）；`--report PATH` 机读
  JSON；摘要两次运行逐字节一致（测试锁）。判定类样例不进 bench 断言（K9/D-2）。
- **覆盖口径**：`manifest.sampling`——总数/采样数双数（133/133 词、148 cases）、
  逐词采样清单、"抽样覆盖非穷举"显式声明、`coverage_claims` ①–⑤ 五条、
  `acceptance.exact_match_required = 1.0`（数据非代码）。
- **探活三形态**（`tests/test_cases_bench.py`，全部 subprocess 打到 bench 进程入口，
  注入必红）：①篡改真值（col+1 / 文本插前缀）→ exit 1；②注入空词表 → exit 1；
  ③坏锚点注入（真值词面锚点改指向不存在法条）→ 门控拒绝 → exit 1。
- **变异验证**：3 处注入全红已还原——①真值 col+1 → bench/确定性测试红；
  ②bench 失败也退 0 → 探活红（5 failed）；③oracle 列号 +1 → 生成守卫＋位级测试红；
  `git diff --stat` 核对还原干净。（注：曾试"oracle 去掉最长优先排序"作变异——当前
  语料无可重叠词面、语义等价不红，属弱变异已弃用；换列号偏移。）

**证据（当轮实测）**：

- `py -3.8 / py -3.12 -m pytest tests -q` → **73 passed**（双解释器；M3 基线 50 + M4 新增 23）；
- `--check` 四件套全过：build_statutes（3 部位级一致）/ gen_wordlists / validate_rulepack
  （words=133 files=4）/ **gen_cases（148 cases 位级一致，M4 新增）**；
- `py -3.8 -X utf8 tools/bench.py` → `BENCH PASS 148/148 exact-match (required=1.00)`；
- 真实词表端到端 CLI 行为与 M2/M3 快照一致（check.py 一行未改）。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。

---

## 2. 下一棒待办（M5：交付包装）

按 `plan/06` M5 行与 `plan/04` §1/§7 执行：

1. **SKILL.md 定稿**：
   - 契约块 `<!-- contract-fields: word category risk line col context suggestion -->`
     与 `check.py` `HIT_FIELDS` **完全相等**（双向一致性测试，plan/04 §1）；
   - 工作流块与判定协议对齐（M3 已对齐并测试锁——改动须保测试绿）；
   - 输出契约表、参数与退出码摘要（K4）、隐私与免责（K12：零命中 ≠ 合规统一措辞）。
2. **README.md**：快速开始逐条可跑（每条命令实测过再写"可跑"）；安装说明；
   bench 结果（148/148 exact-match）与免责声明；仓库结构导览。
3. **技术报告 `docs/技术报告.md`**：六主题——规则化方法 / 扫描-判定分工 /
   三层规则包设计 / 基准设计 / 评测结果（末态实测回填）/ 局限与免责。
4. **契约一致性与编码守卫**：SKILL.md 契约块==HIT_FIELDS 测试；
   编码守卫覆盖所有会打印的可执行入口（`scripts/`＋`tools/`，含 bench/gen_cases——
   `_ensure_utf8_stdio` 探针模式参照 `check.py`）。
5. **收尾**：M5 DoD 验证（plan/06 M5 行逐项）→ plan/00·06·07 回写 →
   写 `plan/HANDOFF-M6.md` → commit（noreply 核对）。

**M5 DoD**（详见 `plan/06` M5 行）：契约一致性绿；README 命令可跑；技术报告六主题齐；
编码守卫覆盖全部可执行入口；CI 本地等价校验清单逐项过（双解释器 pytest／`--check`
四件套／bench／门禁测试）。

**注意**：

- 判定层是 Agent 会话内行为——SKILL.md 工作流引导"扫描→判定→呈现"，不得给
  check.py 加 LLM、不得让 bench 断言 verdict。
- README/报告中的指标值以末态实测回填（**不预设硬数字**——当前实测：148/148）。
- M5 新增文档若需举例文案，用假品牌白名单＋"自检占位词"式合成词（D-10/K6：
  `scripts/` 门禁只查 scripts，但 tools 门禁已扩到 gen_cases.py，别往枪口上撞）。
- SKILL.md 现为骨架草案（M0 版），M5 定稿时重写但保住 M3 对齐的工作流块语义
  （`tests/test_judgment_protocol.py` 有对齐测试）。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。M5 最易踩的几条：

- **K1 契约字段**：`HIT_FIELDS = (word, category, risk, line, col, context, suggestion)`
  ——SKILL.md 契约块必须与此**集合相等**（不许多、不许少、不许改序语义）。
- **K12 免责措辞**：输出与文档强制携带免责；**零命中 = "未检出词表命中" ≠ 合规**。
- **D-11 三态命名**：`confirmed/exempt/uncertain`（文档措辞出现 "violated" 会被测试打红）。
- **K15 冻结纪律**：cases/manifest/词表/法条均为冻结件——文档里展示它们时引用
  而不复制内容（复制会让 `-text`/位级守门失配或词面门禁红）。
- **K6/D-10 词面门禁**：`scripts/` ≥3 字词面门禁（M2）；`tools/gen_cases.py` 同门禁
  （M4 扩展）。文档/测试构造词面输入一律运行时实算（conftest 纪律）。
- **K7 零依赖**：`scripts/` 仅 stdlib（import 白名单测试）；`tools/` 同样零第三方；
  pytest/PyYAML 只进 tests。
- **D-5 支持面**：Python 3.8 底线——新写脚本/测试 3.8 语法可跑
  （`Path.write_text` 无 `newline`；re.sub 替换串不能用 `\u3000` 转义）。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；
  `PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **pytest 根目录**：`tests/conftest.py` 已就位；测试间共享用 `from conftest import ...`
  （rootdir=仓库根）；conftest 已有 `load_check_module`/`rulepack_word_tokens` 可复用。
- **git**：local `user.email` 已是 noreply；**global 是个人 QQ 邮箱**——commit 后核对
  `git log --format='%ae %ce' -1` 两字段均 noreply。
- **gh**：已登录 yuluo554（HTTPS），token 无 workflow scope → 首推带 workflow 文件走
  **SSH push**。
- 工作树跟踪文本保持 LF（`.gitattributes` `* text=auto eol=lf`）；冻结件已配 `-text`
  （法条 txt/raw＋cases.json/manifest.json）。
- **网络**：raw.githubusercontent.com 直连被重置；可用通道 = api.github.com（base64）。
  M5 零外联，用不到网络。
- **变异验证操作法**：先 `cp <目标> $TEMP/<名>.bak`（**备份须在改动后做**，否则还原会
  连带丢掉本轮合法改动）→ 改 → 跑红 → `cp` 还原 → 全绿复验＋`git diff --stat` 核对。
  M3/M4 实测：文件被还原后 Edit 工具会报 "file has been modified"——需 Read 再改或用
  `py -X utf8 -c` 脚本化替换（M4 的 plan/07 回写即用 heredoc 脚本化替换）。
- 仓库树内无本机绝对路径/用户名/QQ 号词面（保持住；HANDOFF 库内一律相对路径）。

---

## 5. M5 DoD checklist

- [ ] SKILL.md 定稿：契约块==HIT_FIELDS（双向）；工作流/退出码/免责齐（K12/D-11 措辞）
- [ ] README.md：快速开始逐条实测可跑；bench 结果与免责；结构导览
- [ ] `docs/技术报告.md`：六主题齐；指标末态实测回填
- [ ] 契约一致性测试落盘（SKILL.md 契约块==HIT_FIELDS）
- [ ] 编码守卫覆盖全部可执行入口（scripts/＋tools/）
- [ ] 双解释器 pytest 全绿（数量以当轮实测为准）
- [ ] `--check` 四件套＋bench 全过（回归）
- [ ] plan/00·06·07 状态回写
- [ ] `plan/HANDOFF-M6.md` 落盘并 commit
- [ ] commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q

# 扫描器（M2 起 DFA 引擎；M3/M4 未改其一行）
py -3.8 -X utf8 scripts/check.py --selftest
echo "文案" | py -3.8 -X utf8 scripts/check.py -

# 冻结件守门（四件套）
py -3.8 -X utf8 tools/build_statutes.py --check
py -3.8 -X utf8 tools/gen_wordlists.py --check
py -3.8 -X utf8 tools/validate_rulepack.py --check
py -3.8 -X utf8 tools/gen_cases.py --check

# 基准（一条命令复现评测）
py -3.8 -X utf8 tools/bench.py            # BENCH PASS 148/148
py -3.8 -X utf8 tools/bench.py --report report.json

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
