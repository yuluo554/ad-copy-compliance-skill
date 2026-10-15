# references/platforms/ — 第二层：分平台规则（人工摘录冻结）

**状态**：◐ M1 部分落盘（2026-10-15）——视频号 ✅；淘宝/抖音/小红书 ⬜（逐通道实测不可达，见下表）。

| 摘录件 | 平台 | 状态 | 说明 |
|---|---|---|---|
| `shipinhao.md` | 微信视频号 | ✅ 已冻结 | 官方静态模板页可达，要点化摘录 |
| `taobao.md` | 淘宝 | ⬜ 不可获取 | 逐通道实测记录见下 |
| `douyin.md` | 抖音 | ⬜ 不可获取 | 同上 |
| `xiaohongshu.md` | 小红书 | ⬜ 不可获取 | 同上 |

每份摘录件头部元数据块须含：

- 平台 / 摘录日期 / 原页 URL / 摘录人 / 摘录范围（哪类违禁词）；
- **性质声明**："人工摘录快照，非官方实时口径，以平台现行规范为准"。

## 不可达平台逐通道实测记录（基准日 2026-10-15，curl + UA 模拟，重定向跟随）

| 平台 | 已查通道 | 实测结果 | 阻断原因 |
|---|---|---|---|
| 淘宝 | `rule.taobao.com/`（规则首页）、`detail.htm?id=…`、`detail.json?id=…&cid=…`、`getChannel.json`、`mtop.rule.getdetail/1.0/` | 首页/详情页均为 **JS 渲染壳**（约 1.7–8KB HTML，正文零长 CJK 段）；API 端点报 `missing params:cid` / 返回 HTML 壳，未获可用正文 | 正文经 JS/接口异步加载，静态抓取不可得 |
| 抖音 | `www.douyin.com/rules`、`/rules/home`、`/rule`、`/rulecenter`、`/aweme/v1/law/rule/list/`、`developer.open-douyin.com` 规则文档页 | `/rules/*` 返回 1059 字节壳；API 需签名返回登录页 HTML；开发者文档 936KB 但**正文零长 CJK 段**（纯 JS 渲染） | 正文 JS 渲染 + 接口签名墙 |
| 小红书 | `www.xiaohongshu.com/protocol`、`/protocol/community`、`/agreement/community`、`/web/protocol/community-standard` | 页面 200（97–976KB）但正文**零长 CJK 段**；`__INITIAL_STATE__` 内只有 UI 文案（搜索/攻略推荐语），无社区规范正文 | 正文 JS 渲染 |

纪律（沿 `plan/05-数据计划.md` §4）：两个不同渠道都查不到 → 落"不可获取"+已查渠道，**不停摆、不编造**；降级继续不阻塞其余模块。若后续人工浏览器访问获取正文，走"新增摘录件＋注明新日期"补录。

首期定位：审计素材 + 判定层可引锚点；机器化多平台输出为扩展（FR-E2，见 `plan/04-模块详设.md` §6）。
