# DNS 配置与更新

本配置位于 `AdamCaoyu/routing-rules`。`AdamCaoyu/SubConverter-Extended` 是转换程序，已有 `clash_rule_base` 支持，本次无需修改程序或重建容器。

订阅模板 `Clash-Full.ini` 引用本仓库 `config/clash-base.yaml`，由转换服务将 DNS 基础设置、订阅节点、分组和分流规则合成最终 YAML。只刷新 rule-providers 不会更新 DNS，需重新转换并更新订阅。

## 面板与路径

- Cloudflare → `DNS-CF-Auto` → `DNS-CF-TW` 台湾候选，全部检测失败时尝试「美国节点」。
- Google → `DNS-Google-Auto` → `DNS-Google-TW` 台湾候选，全部检测失败时尝试「美国节点」。
- 两家解析服务独立使用各自检测路径；后台每 300 秒用真实 DoH 查询地址检查。候选按顺序回退，不保证选中最低延迟节点，也不保证故障瞬间切换。模板传入 4 秒超时参数，但当前转换后端未在 YAML 输出 `timeout`，此时采用内核默认超时。
- DNS 之外的业务仍按原来的服务策略组分流。GitHub 不增设专用回退组，继续使用原有「GitHub」选择卡。
- 直连出口使用 `direct-nameserver` 的两条阿里 HTTPS DNS，`direct-nameserver-follow-policy: false`，不再依赖逐条维护 Apple 域名 DNS 例外。Apple 为 DIRECT 时，建连解析走阿里；Apple / Apple Intelligence 走代理时，若内核需要解析，使用默认海外双 DNS（没有强制 Apple 走阿里的 policy）。2026-11-06 按用户提供的社区规则试验移除了 `gateway.icloud.com` 的 Apple 精确覆盖，现在裸域名与子域名都按 Apple Intelligence 处理。
- `nameserver-policy` 保留 4 条：`geosite:cn` 用阿里直连，`geosite:netflix` / `geosite:hbo` / `geosite:tiktok` 分别经现有「🎥 Netflix」「🎬 HBO」「👯‍♂️ TikTok」服务组查询 Cloudflare / Google。服务组选新加坡 / 美国时，DNS 使用对应选择；以后切地区无需改 DNS。服务组默认值未修改，新设备应自行选择地区。绑定同组不保证两个不同服务器的探测结果、出口公网 IP 或 CDN 所在国家完全相同。
- 保留 `geosite:cn` 是为了 OpenClash 将国内域名加入 `fake-ip-filter` 等场景：返回真实 IP 的 DNS 查询发生在业务选路之前，不能只靠 `direct-nameserver`。流媒体 geosite 依赖设备的数据文件，不能把 `geodata-loader: standard` 当作数据包含这几类的证明；本地 Extra 规则中未被 geosite 收录的 CDN 仍使用默认 DNS。
- 节点域名的启动解析使用国内 HTTPS DNS，避免必须先通过代理才能解析代理节点的循环依赖。

模板共 48 组，原有 44 组加 4 个 DNS 组。地区自动测速机制保留。两家 DNS 减少解析服务的单点依赖；出口回退减少节点故障影响，两者不能保证所有故障下都可访问。

`respect-rules` 保持 `false`。它控制的是 **DNS 上游连接**是否按路由规则选路，不会按被查询网站的策略组自动选择阿里或海外 DNS；本配置通过 `#DIRECT` / `#策略组` 显式指定出口。`default-nameserver` 只负责解析 DNS 服务器域名，不是所有直连网站的 DNS。参见 [Mihomo DNS 文档](https://wiki.metacubex.one/config/dns/)。DNS 查询也可能由代理服务器完成，不能假定每个代理连接必先在本机查询这两条 DoH。

## 更新和复用

1. 使用 README 的同一个 `Clash-Full.ini` 模板地址，保留自己的机场订阅和可信转换后端。
2. 更新订阅并应用。确认生成 YAML 中出现 `dns.nameserver` 的 `#DNS-CF-Auto` / `#DNS-Google-Auto`、`direct-nameserver` 的两条阿里 DoH，以及上述 4 条 policy；对应的 DNS 组与服务组必须存在。
3. OpenClash 如果启用了「自定义 DNS」或自定义覆盖脚本，其本地设置可能覆盖模板。应保留模板 DNS 或同步相关设置，应用后以实际运行配置为准。本机已关闭重复的「自定义 DNS」，并移除 `caoyu_dns_resilience.rb`、`caoyu_apple_dns_policy.rb` 的活动调用，DNS 与 Apple 精确例外统一由订阅维护。局域网 DNS 接管和规则下载地址修正仍独立保留。
4. 新设备可以使用同一个模板。无需复制原设备的订阅令牌、节点密码、控制器密钥、端口、DHCP、防火墙或 NAS 设置。

适用具有这些 DNS 能力的 Mihomo 客户端。依赖客户端可取得所用 geosite 数据；OpenClash 的 DNS 接管、监听端口与局域网域名处理仍由设备管理。没有台湾节点时会尝试美国；两地区都无可用节点时国外 DNS 仍可能失败。台湾名称筛选依据订阅标签，不证明真实公网出口地区。

## 维护与验证

DNS 修改 `scripts/generate_dns.py`；业务域名归属另改 `rules/local/`。再运行 `python3 scripts/build.py`，生成 `config/clash-base.yaml` 与分组模板；运行 `python3 -m unittest discover -s tests -v`。不要只手改生成文件。

2026-11-06 的 DNS 简化需要重新转换整份订阅，单独刷新规则集不生效。更新前保存可用配置，更新后检查国内网站、Apple TV、App Store、ChatGPT / Claude、Telegram / Facebook，并确认 Netflix 新加坡、HBO / TikTok 美国的实际体验。Siri 内 GPT 是否恢复需要设备实测，本次没有移动 Apple 域名。失败时先恢复更新前的完整配置；仓库用 `git revert <本次DNS提交>` 撤销这一笔修改，再重新转换订阅，不要重置整个仓库而丢弃后续更新。

加密连接可能增加首次查询耗时。本配置没有带宽限制，但短时测试不能保证任何节点和时段都不变慢。DNS 解析成功也不能证明业务节点能连接所有网站。

转换后端必须能访问模板、基础 YAML 和规则来源。本机已让配置与规则抓取通过现有路由器代理，节点订阅抓取方式保持原值；这是部署设置，不需要修改转换程序源码，也不要把本机地址盲目复制到其他设备。

## GitHub 纯 IP 连接

2026-10-22 日志核查发现：部分 GitHub 请求仅携带真实 IP，未命中原来的域名规则而落入直连。原基础模板未配置嗅探协议，OpenClash 虽加入 enable / parse-pure-ip 开关，当前 Mihomo 版本仍没有可运行的嗅探器。

基础模板现明确配置 HTTP 与 TLS 域名识别，保留原目标地址，不做 HTTPS 解密。另在具体业务规则之后、通用云平台及最终兜底之前加入 GitHub 官方 Meta API 的 web / api / git 地址范围，使用 no-resolve 并交给原「GitHub」策略组。没有新增 GitHub 专用节点组，也没有将全部 HTTPS 流量改走代理。

`rules/filtered/GitHubIPs.yaml` 由现有每日来源更新流程维护；不导入 Actions/runner 的大范围共享云地址。官方数据缺失、包含异常宽网段或数量骤减时停止发布并保留已有文件。域名识别受请求协议、加密客户端问候等因素限制，因此仍需要纯 IP 兜底。该修复针对已确认的分流缺口，不保证节点或所有目标永不超时。
