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
