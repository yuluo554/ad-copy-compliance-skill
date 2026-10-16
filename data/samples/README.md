# data/samples/ — 合成样例与植入真值（M4 已落盘，2026-10-15）

**状态**：✅ M4 落盘（148 cases / 133 词逐词全量；bench exit 0 全绿）。

- `cases.json` — 合成文案样例集（假品牌白名单；每条登记 `expect_hits`（词+类别+行+列）与 `expect_verdict`）；
- `manifest.json` — 计数 / 覆盖"总数-采样数"双登记 / 采样清单 / 验收门槛（**数据非代码**，
  `acceptance.exact_match_required = 1.0`）。

纪律（详见 `plan/05-数据计划.md` §5 与 `plan/04-模块详设.md` §5）：

- 生成器 `tools/gen_cases.py` 确定性产出（枚举式、无随机、无时间戳），配 `--check` 位级一致守门；
  两文件均为**冻结件**（`.gitattributes` `-text`）——禁手改，变更走重生成；
- 真值**只存"输入与期望"**——出现 `observed` 类字段即视为缺陷（测试锁定）；
- 覆盖五类：①逐词全量 ②多词/负例 ③位置边界（行首/行尾/跨行/CRLF/CR/BOM）
  ④同词异类（规则包无跨文件同词，如实登记 0）⑤判定类 6 条（`expect_verdict`：
  confirmed 2 / exempt 2 / uncertain 2；离线基准不断言，仅供有 LLM 时评估）；
- 基准 `tools/bench.py` 一条命令复现评测，断言命中集合（词+类别+行+列）**双向精确匹配**；
  退出码：0 全对 / 1 有不匹配或门控拦截 / 2 用法配置错误（门槛缺失即 2，不回落默认值）。

复现命令：

```bash
py -3.8 -X utf8 tools/bench.py        # BENCH PASS 148/148 exact-match (required=1.00)
py -3.8 -X utf8 tools/gen_cases.py --check
```
