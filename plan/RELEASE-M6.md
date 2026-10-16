# RELEASE-M6：发布留档（2026-10-15）

> 口径：如实记录——首跑红与修复配对留档，不遮掩、不回填美化。

## 1. 仓库与顺序

- 仓库：`yuluo554/ad-copy-compliance-skill`（私有仓先行，URL：https://github.com/yuluo554/ad-copy-compliance-skill）
- 建仓顺序已按 plan/06 执行：**先私有 → CI 绿 → tag/Release →（公开切换单列待用户拍板，见 §6）**
- 首推走 SSH（gh token 无 workflow scope）；tag push 亦 SSH，实测成功。

## 2. 脱敏扫描（发布前全树）

- tracked 59 文件：本机绝对路径 / 用户名（ASUS）/ QQ 号词面 **0 命中**；
- 全历史（`git grep` over rev-list）：仅 `weixin.qq.com` 等公开来源 URL 命中（平台规则引用，非个人标识），**无个人敏感词面**；
- 提交元数据：`git log --format='%ae %ce'` 全部 noreply（local 已配，逐次核对）。

## 3. 干净环境验证（M6 验收形态："干净副本 + README 逐条"）

本地 `git clone --no-local` 全新副本（HEAD=f1e164c）：

- README 快速开始 6 条命令逐条实测：selftest OK / version 0.0.1 / stdin 扫描 `[]` rc=0 /
  文件扫描命中"销量第一" rc=1 / bench `BENCH PASS 148/148 exact-match` —— 全过；
  （注：裸 `python` 在本机解析到 WindowsApps stub（rc=49），按 README 既定提示以 `py -X utf8` 执行）
- 双解释器 pytest：`py -3.8` / `py -3.12` 各 **82 passed**；
- 四件套 `--check`：build_statutes 3 部 ok / gen_wordlists ok / validate_rulepack words=133 files=4 / gen_cases 148 cases ok。

## 4. CI 首推对账（如实配对）

| run | commit | 结果 | 说明 |
|---|---|---|---|
| 38735560145 | f1e164c（首推） | **failure** | `test_readme_quickstart_commands_run` 硬编码 `py` 启动器：ubuntu 无 `py`（FileNotFoundError）、windows CI runner 无 3.8 道退出 103；win×3.8 job 绿 |
| 38736015173 | 2ce3205（修复） | **success（3 job 全绿）** | 修复＝解释器选道跨平台化：py 启动器探测优先 → 宿主版本匹配回退 `sys.executable` → 仍不可得 skip（skip 携带原因，"逐条实测"语义不变；本机双道仍实跑） |

- 修复提交：`2ce3205`（本地双解释器 9 passed 复绿后推送）；
- CI 配置 `.github/workflows/ci.yml`：ubuntu×3.12 ＋ windows×{3.8, 3.12}，与 D-5 一致。

## 5. 发布三件套

1. **git tag**：`v0.0.1`（版本号取 `scripts/check.py __version__`＝0.0.1，K14），tag push 实测成功；
2. **GitHub Release**：https://github.com/yuluo554/ad-copy-compliance-skill/releases/tag/v0.0.1
   - 附件 `ad-copy-compliance-skill-0.0.1.zip`（59 tracked 文件，K15：ZIP_STORED＋固定时间戳 2026-10-15T00:00:00＋条目排序；两次构建 sha256 位级一致＝可复现打包）；
   - **sha256：`4aaea9810c8f1822ab7283f152ba465f654a5b0738a1a9b7eaf4891b6cf8732e`**；
   - 本地副本 `release/ad-copy-compliance-skill-0.0.1.zip`（`release/` 在 .gitignore，不入库）；
   - Release notes 含 K12 免责措辞（零命中 ≠ 合规；不构成法律意见），词面仅用白名单合成示例，无真实词表词面（K6/D-10）。
3. **发布留档**：本文件。

### 发布物本体已验（真下载链路）

- `gh release download v0.0.1` 真下载 → sha256 复算 **与上式一致** → 解压中立目录：
  selftest OK ＋ pytest 82 passed（3.8）；另在本地打包副本解压目录实跑 README 逐条
  （selftest/扫描 rc=1/bench 148/148）＋双解释器 82 passed；
- GitHub 侧全新 `git clone` 复核：HEAD=2ce3205，version 0.0.1，pytest 82 passed；
- Release API 可达：`gh api .../releases/latest` → tag v0.0.1，assets 1 项。

## 6. 遗留与如实结论

- **仓库已切公开（2026-10-15，用户确认后执行）**：`gh repo edit --visibility public` 实测成功，API 复核 visibility=PUBLIC；topics 已设 6 枚（advertising-law / compliance / agent-skill / chinese-nlp / dfa / text-scanner）；Release 链接公开可达（https://github.com/yuluo554/ad-copy-compliance-skill/releases/tag/v0.0.1）；
- CI 首跑红已按"如实配对"记录（§4），未回填美化；
- topics 已随公开切换一并设置（6 枚，见上）。

---

## 7. 发布后修复轮（2026-10-16）：审计缺陷整改 + tag 重打

> 背景：发布后审计发现文档漂移、tag 指向早于发布留档等问题，本轮逐条整改。
> 纪律：一切数字先实测再改（不回抄审计报告），测试/基准复跑全绿，推送后据实记 CI run。

### 7.1 本轮改动（按类型分提交）

| 提交 | 类型 | 改了什么 | 实测依据 |
|---|---|---|---|
| `9093a24` | 数字漂移 | 判定类样例数 8→6（`data/samples/README.md`、`docs/技术报告.md` 两处、`plan/HANDOFF-M5.md`） | 读 `data/samples/cases.json`：`expect_verdict` 非 null = **6**（confirmed 2 / exempt 2 / uncertain 2）；`manifest.json.verdict_case_ids` 列 6 条（生成器本已写 6，doc 侧漂移） |
| `1a384ec` | 数字漂移 | 词表来源量级「约 300 词」→「去重后 191 词」（`plan/01:132`、`plan/00:39`、`plan/04:81`、`plan/05:13/56`、`references/README.md`） | 经 `api.github.com/contents` base64 重取 `Dete.txt`（sha `1954fab`，size 2150）：非空行 195、**去重后 191**（与 M1 快照一致） |
| `a710ea3` | 状态过期 | README 结构导览、技术报告状态行/诚实口径段「未接远端待验证」→ 实跑全绿 + run id | `gh run list` 实测 run 38736015173 三 job 全绿 |
| `5fb5959` | 交付缺口 | README 增「作为 Skill 安装与调用」节；新增 `docs/skill-调用演练.md`（真跑记录）；FR-1/FR-2 验收门、plan/07 §1/§2/§3、plan/06 M6 行、plan/00 台账首行落可核验物 | 本机真跑一轮"安装→frontmatter 解析→扫描→判定"，原始输出与 K10 断言见该文件 |
| `47503db` | 自相矛盾 | plan/07 发布 checklist「切公开待用户确认」「暂 private」→ 已切 PUBLIC | `gh repo edit --visibility public` 实测 + API 复核 visibility=PUBLIC（§6） |

**未改项说明**：审计报告称判定类为 6 条、manifest 已写 6——本轮独立复核一致（见上表）；
另发现审计报告未列的同源漂移 4 处（plan/04、plan/05 两处、references/README），一并修正。

### 7.2 验证（本轮实测）

- `py -3.8 -m pytest tests -q` / `py -3.12 -m pytest tests -q` → **各 82 passed**；
- `py -3.12 -X utf8 tools/bench.py` → `BENCH PASS 148/148 exact-match (required=1.00) gate_blocked=0`；
- 冻结件四件套 `--check` 全过：`build_statutes` 3 部 / `gen_wordlists` / `validate_rulepack`（words=133 files=4）/ `gen_cases`（148 cases）；
- 推送后 CI：**run 38872759121（success，三 job）**，head=`47503db`。

### 7.3 tag 重打（修正 tag 指向）

**缺陷**：原 `v0.0.1` 指向 `2ce3205`（CI 修复提交，早于 M6 发布收尾），其 tag 树内
README 仍写"M5 待发布"、且不含 `plan/RELEASE-M6.md`——tag 与"已发布"状态不符。

**修复**：在文档整改全部提交并验证后，删旧 tag、于**最终提交上重打** `v0.0.1` 并推 tag：

- 旧指向：`2ce3205`；新指向：本轮最终提交（见 §7.4 回填）。
- 重打后核验：`git cat-file -e v0.0.1:plan/RELEASE-M6.md` 成功；`git show v0.0.1:README.md`
  状态行为"已发布 v0.0.1"（非"M5 待发布"）。

### 7.4 Release 附件与 tag（实测记录）

- **tag 新指向**：`v0.0.1` 已重打至**本文件在 tag 树内的版本所在提交**（即 §7.4 定稿提交；
  §7.5 回填因含 tag 自身 sha 只能落在其后提交，故 tag 不含 §7.5）。tag 指针不能写死进
  被 tag 的树内——写死会自指循环，故以 `git rev-parse v0.0.1^{}` 命令复算，实测 sha 见 §7.5。
  重打后核验：`git cat-file -e v0.0.1:plan/RELEASE-M6.md` **成功**（旧指向 `2ce3205` 时该路径不存在）；
  `git show v0.0.1:README.md` 状态行为"已发布 v0.0.1"（旧指向时为"M5 待发布"）。
- **Release 附件**：`ad-copy-compliance-skill-0.0.1.zip` 按 K15 配方
  （`git ls-tree` 全量 tracked 文件 + `ZIP_STORED` + 固定时间戳 2026-10-15T00:00:00 + 条目排序）
  从 tag 树重新构建——**61 tracked 文件**（旧附件 59 文件）。
  **附件 sha256 记于 GitHub Release notes 与下方 §7.5**：附件内含本文件，
  把自身 sha 写进本文件会自指、永不成立，故按惯例置于附件外的 Release notes。
- **CI run**：本轮分支修复推送已实测绿（`47503db` → run 38872759121，三 job）；
  tag 重打推送所触发的 run 与附件 sha 见 **§7.5**（均晚于 tag 本身，无法写进 tag 树——
  如实说明，不伪造、不留空）。

### 7.5 tag 重打后的收尾回填

（本节在 tag 重打并推送后追加；因 run/sha 晚于 tag，只能落在 tag 之后的提交上。）

- **tag 指向 sha**：`16d8a076de33b12c1634d8a8914dd7f712c2771f`（`git rev-parse v0.0.1^{}` 实测）；
  重打后核验通过：`git cat-file -e v0.0.1:plan/RELEASE-M6.md` **成功**、
  `git show v0.0.1:README.md` 状态行 = "已发布 v0.0.1"。
- **Release 附件 sha256**：`7c0a2b488c92d32c31ff43d6f833200bd9d9fe96264cc58ceb56593e7dc0ee8c`
  （61 tracked 文件，821780 字节；旧附件 59 文件 / `4aaea981…8732e` 已由 `--clobber` 覆盖）。
  真下载链路复算：`gh release download v0.0.1` → sha256 **一致** → 解压 `testzip()` 无损坏、
  含 `plan/RELEASE-M6.md`；解压目录实跑 `--selftest` OK ＋ pytest **82 passed** ＋ bench **148/148**。
- **CI run（tag 推送）**：`38873494076` → **success**（push 事件，ref `v0.0.1`，head `16d8a076`）；
  同提交 main 推送 run `38873476747` 亦 success。

