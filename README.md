# 草鱼 · 服务分流规则

每个服务一张独立选择卡，只选地区或公共策略；具体节点统一在下方节点组管理。未匹配流量直连（黑名单模式）。这是独立仓库，不携带旧 Fork 的历史模板。

## OpenClash 订阅转换模板

```text
https://raw.githubusercontent.com/AdamCaoyu/routing-rules/refs/heads/main/Clash-Full.ini
```

填入现有订阅转换的“自定义模板地址”。继续使用你自己的订阅和转换服务。本仓库不包含节点、密码或订阅链接。

## 面板怎么选

ChatGPT、Claude、Grok、Perplexity、Meta AI 与 TikTok、Telegram 一样独立选择地区组。服务卡片不再展开所有节点；删除港台日新韩 / 台日新韩两个组合自动组。

- 服务卡片：选择香港节点、台湾节点、日本节点、新加坡节点、韩国节点、美国节点、其他节点，或所有自动、所有手动、DIRECT / REJECT。
- 地区节点卡片：默认选对应的“地区-自动”；也可手动指定该地区的具体节点。选回“地区-自动”即可恢复自动测速。
- 所有手动：保留跨地区手选入口；多个服务选择它时会一起跟随它的选择。
- 地区自动卡片：负责测速，是地区选择卡片的辅助组；日常不用逐个操作。

普通 Apple、Microsoft、Amazon、PayPal、国内默认直连；OneDrive 初始选择“美国节点”，该地区默认自动，可以自行更改。Apple Intelligence 默认跟随 ChatGPT，微软登录默认跟随 OneDrive。

**地区组是共享的**：两个服务都选“台湾节点”，就会使用同一个地区选择。需要另一个固定出口时，可以让其中一个服务改选“所有手动”。固定节点不等于固定公网 IP，也不能保证免于账号风控。

## 文件分工

| 文件 / 目录 | 维护内容 |
| --- | --- |
| `config/services.json` | 服务组默认选项及少量共享登录关联 |
| `config/regions.json` | 地区名称与缩写（不按状态词排除节点） |
| `config/groups.ini` | 自动生成的分组定义，不手动编辑 |
| `config/rules.ini` | 规则源、归属策略、匹配顺序 |
| `config/settings.ini` | 转换开关 |
| `rules/local/*.list` | 个人补充域名，无策略字段，按服务区分 |
| `rules/filtered/*.yaml` | 从上游筛选的规则，附来源与排除清单，每日检查更新 |
| `rules/clash/*.yaml` | 从本地列表生成的 Clash 原生格式 |
| `Clash-Full.ini` | 自动生成的最终模板，供订阅转换读取 |
| `docs/` | 使用说明、规则目录、来源与验证 |
| `shadowrocket/` | 后续 Shadowrocket 配置位置 |

依赖：Python 3 与 `PyYAML==6.0.3`。手动更新筛选规则执行 `python3 scripts/sync_sources.py`。

修改源文件后执行 `python3 scripts/build.py`，再运行 `python3 -m unittest discover -s tests -v`。不要单独编辑生成文件。

[使用说明](docs/使用说明.md) · [规则目录](docs/规则目录.md) · [来源与边界](docs/来源与边界.md) · [验证记录](docs/验证记录.md)
