# HANDOFF-M6：发布＋收尾（M6）

> **用法**：新对话启动提示词（用户侧拼绝对路径）——
> `/goal 读取 <项目根>/plan/HANDOFF-M6.md 继续完成任务`
> （本文件库内一律相对路径；项目根 = 仓库根目录）

---

## 1. 当前进度与证据（M5 已完成，2026-10-15）

**M5 = 交付包装，已完成**：

- **SKILL.md 定稿**（正式版 v0.0.1）：契约块
  `<!-- contract-fields: word category risk line col context suggestion -->` 与
  `check.py HIT_FIELDS` **双向一致**（`tests/test_delivery_packaging.py`：
  块唯一性/集合相等/序相等/与实际命中字段序三方对齐）；工作流块保 M3 对齐语义
  （`tests/test_judgment_protocol.py` 同族口径测试仍绿）；K4 退出码摘要、词表门控说明、
  基准命令、K12 免责（零命中 ≠ 合规）、D-11 三态措辞全部落齐。
- **README.md 定稿**：快速开始 6 条命令逐条实测可跑（**测试锁**：
  `test_readme_quickstart_commands_run` 在 pytest 内对 3.8/3.12 双通道 subprocess 实跑，
  stdin 管道/造数行等价处理）；状态行转"功能完成（M5），待发布（M6）"；
  路线图 M0–M5 ✅；结构导览含 docs/与基准；免责与许可齐。
- **技术报告 `docs/技术报告.md`**：六主题齐（规则化方法 / 扫描-判定分工 / 三层规则包
  设计 / 基准设计 / 评测结果 / 局限与免责），指标末态实测回填（bench 148/148=1.00、
  82 测试双解释器绿），不预设硬数字纪律保持。
- **编码守卫（K13）**：`_ensure_utf8_stdio` 探针模式覆盖全部 6 个可执行入口
  （`scripts/check.py` 原有 ＋ `tools/` 5 个：bench/gen_cases/gen_wordlists/
  build_statutes/validate_rulepack 均已在 `main()` 入口挂守卫）；AST 测试锁定
  （`test_all_executable_entrypoints_have_utf8_guard`，新增入口漏挂即红）。
- **M5 新增测试**：`tests/test_delivery_packaging.py` 9 项（契约一致性 6 ＋ 编码守卫 1
  ＋ README 可跑 2×双解释器参数化计 2）。

**证据（当轮实测）**：

- `py -3.8 / py -3.12 -m pytest tests -q` → **82 passed**（双解释器；M4 基线 73 ＋ M5 新增 9）；
- `--check` 四件套全过（build_statutes 3 部位级 / gen_wordlists / validate_rulepack
  words=133 files=4 / gen_cases 148 cases 位级）；
- `py -3.8 -X utf8 tools/bench.py` → `BENCH PASS 148/148 exact-match (required=1.00)`；
- `scripts/check.py --selftest` → SELFTEST_OK；
- **变异验证 2 处全红已还原**：①`HIT_FIELDS` 减一字段 → 契约一致性测试 3 处红；
  ②删 bench `main()` 守卫 → 编码守卫测试红；`git diff --stat` 核对还原干净。
- README 快速开始整链（selftest/version/stdin 扫描/造数+文件扫描/bench）当轮实跑全过。

**CI 状态**：未接远端——**本地等价校验（未接远端，CI 待首推验证）**。

---

## 2. 下一棒待办（M6：发布＋收尾）

按 `plan/06` M6 行与 `plan/00` M6 DoD 三件套硬约束执行：

1. **脱敏扫描**：仓库树内无本机绝对路径/用户名/QQ 号词面（保持住，发布前全树再扫一遍）；
   `plan/` 交接文件库内一律相对路径。
2. **干净环境验证**：全新 clone（或干净副本）→ README 快速开始逐条实测 →
   双解释器 pytest → `--check` 四件套 → bench（M6 验收形态："干净副本 + README 逐条"）。
3. **建仓与首推（顺序固定）**：先私有仓库 → CI 绿 → tag/Release → 公开。
   - `gh` 已登录 yuluo554（HTTPS）但 token 无 workflow scope → **首推带 workflow 文件走
     SSH push**；
   - 首推后核对 CI run：`本地等价校验` 措辞可转正，须记录 run id 与结论；
     首跑若红，失败与修复提交**如实配对留档**（不遮掩、不回填美化）。
4. **发布三件套（缺一即 M6 未达成）**：
   - ① git tag（版本号对齐 `check.py __version__`，当前 0.0.1）；
   - ② GitHub Release 附产物（zip 用 `ZIP_STORED`＋固定时间戳＋条目排序，K15），
     本地留 release zip 副本 ＋ sha256 可复验；**发布物本体已验**：真下载 → sha256 →
     解压验证（selftest＋README 逐条）；
   - ③ 发布留档 `plan/RELEASE-M6.md`（run id、sha256、复核记录、如实结论）。
5. **收尾**：topics/README 状态行转正；缓议项清零（`plan/07` §4 待定决策表 +
   缓议清单逐条给"拍板/跳过"结论）；plan/00·06·07 回写 M6 状态；commit（noreply 核对）。

**M6 DoD**（详见 `plan/06` M6 行）：tag＋Release（附产物＋sha256）＋发布留档三件套；
发布物本体已验；CI 首推全绿＋push/run 对账；topics/README 状态行转正；缓议项清零；
GitHub 全新 clone 复核＋Release 链接可达。

---

## 3. 既定口径清单（K 编号——动了会打挂测试/基准）

全量见 `plan/04-模块详设.md` §0（K1–K15）。M6 最易踩的几条：

- **K12 免责措辞**：README/topics/Release notes 措辞保持"零命中 = 未检出词表命中 ≠ 合规"、
  "不构成法律意见"；三态只用 confirmed/exempt/uncertain（D-11，文档出现 violated 会被
  测试打红）。
- **K15 冻结纪律**：发布 zip 用 `ZIP_STORED`＋固定时间戳＋条目排序；冻结件（法条/词表/
  cases/manifest）引用而不复制。
- **K6/D-10 词面门禁**：Release notes/README 举例文案用假品牌白名单＋"自检占位词"式
  合成词，不粘贴真实词表词面。
- **K7 零依赖**：发布物运行通路零第三方依赖的承诺不变（pytest/PyYAML 只在 tests）。
- **K14 版本**：tag/Release 版本号取 `check.py __version__`（唯一处）；规则包版本取
  `references/MANIFEST.json` 派生值（禁手写）。

---

## 4. 本机环境坑（只记实测过的）

- **Python**：`py -0p` = 3.8.8-64 + 3.12-64 双通道；一律 `py -X utf8` 跑脚本；
  `PYTHONDONTWRITEBYTECODE=1` 全程带（含 pytest）。
- **Python 3.8 语法坑（D-5）**：`Path.write_text` 无 `newline` 参数（M5 实测又踩一次——
  heredoc 写文件用 `open(..., newline="\n")`）；re.sub 替换串不能用 `\u3000` 转义。
- **pytest 根目录**：`tests/conftest.py` 已就位；共享用 `from conftest import ...`
  （rootdir=仓库根）。
- **git**：local `user.email` 已是 noreply；**global 是个人 QQ 邮箱**——commit 后核对
  `git log --format='%ae %ce' -1` 两字段均 noreply。
- **gh**：已登录 yuluo554（HTTPS），token 无 workflow scope → 首推带 workflow 文件走
  **SSH push**。
- **网络**：raw.githubusercontent.com 直连被重置；可用通道 = api.github.com（base64）。
- **变异验证操作法**：先 `cp <目标> $TEMP/<名>.bak`（备份须在改动后做）→ 改 → 跑红 →
  `cp` 还原 → 全绿复验＋`git diff --stat` 核对；文件被还原后 Edit 工具会报
  "file has been modified"——需 Read 再改或用脚本化替换。
- **heredoc 中文**：`py - <<'EOF'` 直喂中文会报 Non-UTF-8（M5 实测）——先落
  `$TEMP/*.py`（带 `# -*- coding: utf-8 -*-`）再执行。

---

## 5. M6 DoD checklist

- [ ] 脱敏扫描：全树无本机绝对路径/用户名/QQ 号词面
- [ ] 干净环境验证：全新 clone + README 逐条 + 双解释器 pytest + 四件套 + bench
- [ ] 建仓顺序：先私有 → CI 绿 → tag/Release → 公开；首推走 SSH（workflow scope 缺）
- [ ] CI 首推全绿＋push/run 对账（run id 留档；首跑红则修复配对留档）
- [ ] tag＋Release（附产物＋sha256，ZIP_STORED/固定时间戳/条目排序）＋本地 zip 副本可复验
- [ ] 发布物本体已验：真下载 → sha256 → 解压验证（selftest＋README 逐条）
- [ ] `plan/RELEASE-M6.md` 发布留档
- [ ] topics/README 状态行转正；缓议项清零（plan/07 §4 逐条拍板/跳过）
- [ ] plan/00·06·07 回写 M6 状态；commit 后 `git log --format='%ae %ce' -1` 两字段均 noreply

---

## 6. 关键命令速查

```bash
cd <项目根>   # 用户侧拼绝对路径；库内一律相对路径

# 测试（双解释器）
PYTHONDONTWRITEBYTECODE=1 py -3.8  -m pytest tests -q   # 82 passed
PYTHONDONTWRITEBYTECODE=1 py -3.12 -m pytest tests -q   # 82 passed

# 扫描器与基准
py -3.8 -X utf8 scripts/check.py --selftest
py -3.8 -X utf8 tools/bench.py            # BENCH PASS 148/148 exact-match

# 冻结件守门（四件套）
py -3.8 -X utf8 tools/build_statutes.py --check
py -3.8 -X utf8 tools/gen_wordlists.py --check
py -3.8 -X utf8 tools/validate_rulepack.py --check
py -3.8 -X utf8 tools/gen_cases.py --check

# 提交自查
git status --short
git log --format='%ae %ce' -1        # 两字段必须均 noreply
```
