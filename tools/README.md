# tools/ — 构建、校验与基准辅助脚本（不进运行通路）

用户通路的唯一入口是 `scripts/check.py`；本目录脚本面向仓库维护与验收（用户无需调用）。

规划（按里程碑落盘）：

| 脚本 | 职责 | 里程碑 |
|---|---|---|
| `build_statutes.py` | 法条抓取→冻结→抽取→逐字断言→sha256 登记；`--check` 位级一致 | M1 |
| `validate_rulepack.py` | 词表 schema/锚点/排序校验；`--write-manifest` 更新 `references/MANIFEST.json` | M1 |
| `gen_cases.py` | 合成样例+真值生成（确定性）；`--check` 位级一致 | M4 |
| `bench.py` | 真值基准运行器（一条命令复现评测；退出码 0/1/2） | M4 |
| `audit_repo.py` | 发布期脱敏扫描（tracked/history/messages 三模式 + selftest 阳性对照） | M6 |

纪律：本目录脚本的"会打印的中文输出"同样受编码守卫要求（入口 `_ensure_utf8_stdio` 同款）；扫描/校验类脚本的输入路径**不存在时必须大声失败（exit 2）**，不静默空扫。
