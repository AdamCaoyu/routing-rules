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


## 2026-11-07：DNS 出口核查与明文 DNS 兜底防护

IPLeak 显示的是其探针域名最终到达权威端时的递归解析器出口，不等于客户端直接连接了列表中的每个地址。独立探针已复现：通过 `https://223.5.5.5/dns-query`、`https://223.6.6.6/dns-query` 和 `https://dns.alidns.com/dns-query` 请求一个新域名，IPLeak 均可能记录运营商地址。因此该地址可以来自阿里 DoH 后续解析链路；这不能单独证明本机绕过了 DoH，更不能据此推断 Siri/GPT 的 DNS 泄漏。多次测试结果属于当时网络，不保证其他地区、时段相同。

当前采用按需分流，未命中业务规则的流量仍直连。IPLeak 自身实测命中 `DST-PORT,443,DIRECT`，因此会看到本地公网 IPv4/IPv6；本次不为让测试页面变绿而改变全局兜底策略。直连业务的阿里 DoH、默认海外 Cloudflare/Google 独立回退、流媒体同组选区均保留；DNS 出口不会自动等于每个 Apple 业务节点。

OpenWrt 部署另外增加了以下两条防火墙防护（**设备部署设置，不会因下载订阅自动安装**）：保留 LAN 的 IPv4/IPv6、TCP/UDP 53 接管至 dnsmasq/Mihomo；阻断仍试图从 LAN 或路由器本机直接到 WAN 的 TCP/UDP 53。这样，应用显式指定 WAN 明文 DNS 或将来接管意外失效时，不会静默回退到 WAN 明文 DNS。正常路由器查询继续使用 HTTPS DNS。

对应 UCI 段如下；使用前核对设备的 LAN/WAN 区域名称，并检查是否有依赖外部明文 DNS 的特殊程序：

```uci
config rule 'caoyu_dns_guard_lan'
    option name 'Caoyu-Block-Plain-DNS-LAN-WAN'
    option src 'lan'
    option dest 'wan'
    option proto 'tcp udp'
    option dest_port '53'
    option family 'any'
    option target 'REJECT'
    option enabled '1'

config rule 'caoyu_dns_guard_router'
    option name 'Caoyu-Block-Plain-DNS-Router-WAN'
    option dest 'wan'
    option proto 'tcp udp'
    option dest_port '53'
    option family 'any'
    option target 'REJECT'
    option enabled '1'
```

防护有意拒绝明文回退：若加密上游全部失效，DNS 可能失败，而不是恢复 ISP 明文解析。它不阻止应用自行使用 HTTPS/DoT，也不控制代理服务器内部的 DNS；不能据此承诺全局匿名。DoH 加密、业务代理选路、WebRTC、公网 IPv6 暴露是不同问题，需要分别验证。回退此防护时仅删除上述两个命名段并重新应用防火墙；保留原有接管规则。

本机原有 Passwall 防火墙附加脚本在整套防火墙 reload 时返回失败，初次事务已回退。最终安装通过 `fw4 check`、按 UCI 编译结果校验后原子加载这两组规则，并提交 UCI，未改动其他插件。后续全量 reload 的该插件报错仍需独立维护；这两组规则本身的编译、持久配置和当前运行规则已验证。

参考：[Mihomo DNS](https://wiki.metacubex.one/config/dns/)、[IPLeak 解释](https://ipleak.net/#dnsleak)、[OpenWrt DNS 接管](https://openwrt.org/docs/guide-user/firewall/fw3_configurations/intercept_dns)。

## Apple 日常媒体与 AI 路径分离

`rules/local/AppleDailyDirect.list` 保留已验证的媒体、封面、商店和更新端点，经生成器输出为 `rules/clash/AppleDailyDirect.yaml` 与 Shadowrocket 原生 provider。顺序为 Apple Intelligence 优先、日常媒体 DIRECT、普通 Apple；不会把整个 `aaplimg.com`、`akadns.net`、`icloud.com`、`icloud-content.com` 改成直连。

其中 `streamingaudio.g.aaplimg.com` 与 `aod.itunes.g.aaplimg.com` 是从实际音频连接确认的精确补充；后者曾有超过 10 MB 数据走普通 Apple 台湾，补直连后用户反馈等待改善，日志确认两者 DIRECT。Apple TV 视频流 `vod-ap-aoc.tv.apple.com`、接口 `uts-api.itunes.apple.com` 和授权 `cma2.itunes.apple.com` 也已实测 DIRECT。

这是已验证范围的优化，尚未定位本机 Siri 内 GPT 所需代理的最小域名集合，iCloud 照片/文件精细分流仍待继续。该设备当前保留普通 Apple 选台湾、Intelligence 通过 ChatGPT 选台湾；仓库的通用分组默认值不强行替换其他用户的选择。更新订阅需保留这台设备已验证的策略组选择。后台网络检查不等于设备上的 Siri/GPT、照片同步或实际播放复测。
