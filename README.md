# 草鱼 · 服务分流规则

每个服务一张独立选择卡，自动测速与具体节点都能选择。未匹配流量直连（黑名单模式）。这是独立仓库，不携带旧 Fork 的历史模板。

## OpenClash 订阅转换模板

```text
https://raw.githubusercontent.com/AdamCaoyu/routing-rules/refs/heads/main/Clash-Full.ini
```

填入现有订阅转换的“自定义模板地址”。继续使用你自己的订阅和转换服务。本仓库不包含节点、密码或订阅链接。

## 面板怎么选

ChatGPT、Claude、Grok、Perplexity、Meta AI、其他 AI 与 TikTok、Telegram 一样独立选择。所有业务组都有直连、所有自动、各地区自动、所有手动、拒绝以及具体节点选项，没有 AI1 / AI2。

多数境外服务初始选择“所有-自动”。普通 Apple、Microsoft、Amazon、PayPal、国内默认直连；OneDrive 初始选择“美国-自动”，可以改成任何提供的选项。Apple Intelligence 默认跟随 ChatGPT，微软登录默认跟随 OneDrive，这两项也能独立更改。

需要固定账号出口时，在服务卡片中直接选具体节点；其他服务继续选自动组。固定节点不等于固定公网 IP，也不能保证免于账号风控。

## 文件分工

| 文件 / 目录 | 维护内容 |
| --- | --- |
| `config/groups.ini` | 面板分组、默认选项、地区节点筛选 |
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
