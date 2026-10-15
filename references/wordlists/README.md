# references/wordlists/ — 第三层：分类词表

**状态**：⬜ M1 落盘（当前为占位）。

M1 将产出（文件名 → 类别，逐条 `category` 必须与文件声明一致）：

| 文件 | 类别 |
|---|---|
| `absolute-terms.json` | 绝对化用语 |
| `medical.json` | 医疗违禁 |
| `health-food.json` | 保健食品违禁 |
| `industry.json` | 行业违禁 |

条目字段（详见 `plan/04-模块详设.md` §2.3）：

- `word` / `category` / `risk`(`high|medium|low`) / `anchor`(`doc`,`clause`,`basis=literal|variant`) / `source`（**非官方标注**）/ `status`(`verified|pending`) / `suggestion`（非空）；
- `basis=literal`：词面必须逐字见于冻结条款正文；`basis=variant`：必须写 `note` 说明语义类属判定依据。

纪律：

- **落库纪律（K6/D-3）**：规则包**只收挂锚点条目的 `verified` 条目**；候选词留 `data/wordlist-candidates.md` 工作台账（不进规则包、不被引擎加载）；
- **门控（K5）**：引擎只加载 `verified` 且锚点可解析的条目；被拒条目进"未启用清单"（stderr 显式列出原因）；
- 来源为公开整理词表（`es3344520/advertising-limit-words`、`dx2020z/ad-redline-guardian` 等），**非官方整理，法条原文为准**；来源仓库许可在 `data/README.md` 台账登记。
