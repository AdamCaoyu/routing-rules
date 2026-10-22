# DNS 配置与更新

本配置位于 `AdamCaoyu/routing-rules`。`AdamCaoyu/SubConverter-Extended` 是转换程序，已有 `clash_rule_base` 支持，本次无需修改程序或重建容器。

订阅模板 `Clash-Full.ini` 引用本仓库 `config/clash-base.yaml`，由转换服务将 DNS 基础设置、订阅节点、分组和分流规则合成最终 YAML。只刷新 rule-providers 不会更新 DNS，需重新转换并更新订阅。

## 面板与路径

- Cloudflare → `DNS-CF-Auto` → `DNS-CF-TW` 台湾候选，全部检测失败时尝试「美国节点」。
- Google → `DNS-Google-Auto` → `DNS-Google-TW` 台湾候选，全部检测失败时尝试「美国节点」。
- 两家解析服务独立使用各自检测路径；后台每 300 秒用真实 DoH 查询地址检查。候选按顺序回退，不保证选中最低延迟节点，也不保证故障瞬间切换。模板传入 4 秒超时参数，但当前转换后端未在 YAML 输出 `timeout`，此时采用内核默认超时；本机兼容覆写会保留原有 4000 毫秒设置。
- DNS 之外的业务仍按原来的服务策略组分流。GitHub 不增设专用回退组，继续使用原有「GitHub」选择卡。
- 普通 Apple/iCloud 与国内域名使用国内阿里 HTTPS DNS 直连；Apple Intelligence 的特殊域名使用国外双 DNS。`gateway.icloud.com` 精确域名走普通 Apple，子域名保留 AI 特殊处理。
- 节点域名的启动解析使用国内 HTTPS DNS，避免必须先通过代理才能解析代理节点的循环依赖。

模板共 48 组，原有 44 组加 4 个 DNS 组。地区自动测速机制保留。两家 DNS 减少解析服务的单点依赖；出口回退减少节点故障影响，两者不能保证所有故障下都可访问。

## 更新和复用

1. 使用 README 的同一个 `Clash-Full.ini` 模板地址，保留自己的机场订阅和可信转换后端。
2. 更新订阅并应用。确认生成 YAML 中出现 `dns.nameserver` 的 `#DNS-CF-Auto` / `#DNS-Google-Auto`，且对应的 4 个策略组存在。
3. OpenClash 如果启用了「自定义 DNS」或自定义覆盖脚本，其本地设置可能覆盖模板。应保留模板 DNS 或同步相关设置，应用后以实际运行配置为准。此前个人 `caoyu_dns_resilience.rb` 脚本可继续作兼容兜底，但必须使用已移除 GitHub 专用组的版本。
4. 新设备可以使用同一个模板。无需复制原设备的订阅令牌、节点密码、控制器密钥、端口、DHCP、防火墙或 NAS 设置。

适用具有这些 DNS 能力的 Mihomo 客户端。依赖客户端可取得所用 geosite 数据；OpenClash 的 DNS 接管、监听端口与局域网域名处理仍由设备管理。没有台湾节点时会尝试美国；两地区都无可用节点时国外 DNS 仍可能失败。台湾名称筛选依据订阅标签，不证明真实公网出口地区。

## 维护与验证

修改 `scripts/generate_dns.py` 和现有 Apple 域名源，再运行 `python3 scripts/build.py`，生成 `config/clash-base.yaml` 与分组模板；运行 `python3 -m unittest discover -s tests -v`。不要只手改生成文件。

加密连接可能增加首次查询耗时。本配置没有带宽限制，但短时测试不能保证任何节点和时段都不变慢。DNS 解析成功也不能证明业务节点能连接所有网站。
