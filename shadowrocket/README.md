# 草鱼 · Shadowrocket 配置

## 选择文件

- `caoyu-shadowrocket.conf`：推荐优化版。51 个分组，服务选择与 OpenClash 对齐，61 个来源转换为 Shadowrocket 原生规则格式。
- `lazy_group-AppleAI-test.conf`：原配置的最小测试版，保留原服务分组与规则源，新增 Apple Intelligence 分组和七条后缀规则，地区组增加自动与手动切换；公开版删除 MITM 证书、关闭 MITM，并校正规则目标的大小写。原来的混合格式等问题仍保留，适合对照测试，不推荐长期使用。
- `rules/`：优化版引用的规则列表。`sources.json` 记录来源、格式、规则数量和校验值；`validation.json` 记录静态验证结果。
- `对比分析.md`：旧小火箭与 OpenClash 的差异、优化选择及测试边界。

优化版导入地址：

`https://raw.githubusercontent.com/AdamCaoyu/routing-rules/main/shadowrocket/caoyu-shadowrocket.conf`

测试版导入地址：

`https://raw.githubusercontent.com/AdamCaoyu/routing-rules/main/shadowrocket/lazy_group-AppleAI-test.conf`

在 Shadowrocket 的配置页面通过 URL 下载，选中配置，确认使用配置模式并重新连接。节点继续使用首页已有订阅，不需要转换订阅。Apple Intelligence 默认跟随 ChatGPT，可独立改选地区；地区节点提供地区自动与地区手动两个选项，默认自动。选择地区手动后，再进入该组指定固定节点。跨地区所有自动不恢复。所有手动默认选择 PROXY，跟随首页当前节点，也可在该组内手选节点。

## 两份配置共同保留的前四条

```ini
DOMAIN-SUFFIX,iqos.com,日本节点
IP-CIDR,192.168.100.0/24,HOME,no-resolve
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanProgramAD.list,REJECT
RULE-SET,https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/BanAD.list,REJECT
```

第 5–11 条为用户指定的七条 `DOMAIN-SUFFIX`，全部指向 `🍏 Apple Intelligence`，随后才是局域网和普通服务规则。原有 `192.168.100.0/24` TUN 包含路由也保留。**HOME 是已有外部节点/策略名称，配置不虚构回家节点。** 客户端必须已有 HOME 才能访问回家网段。

原 OpenClash 默认所有自动的服务，在小火箭中改为所有手动；OpenClash 本身不改动。

最终兜底为 `FINAL,DIRECT`。普通 Apple、Microsoft、Amazon、PayPal、国内默认直连；OneDrive 默认美国节点；微软登录跟随 OneDrive。Apple Intelligence 跟随 ChatGPT。未识别地区的节点仍可在所有手动中选择。

## 苹果设备设置

保留原配置的系统联网绕过、国内 DoH、系统备用 DNS、IPv6 开启且不优先 IPv6、HOME 包含路由及不支持 UDP 时 REJECT 的行为。地区自动组每 600 秒测速，公差 100 毫秒；选择低延迟可用节点，避免因微小波动反复切换。地区手动组不测速、不自动切换。OpenClash 的自动组和测速参数保持原样。

优化版移除全局 `*.apple.com` / `*.icloud.com → system DNS` 的 Host 覆盖，让 Apple Intelligence 和普通 Apple 使用同一套可配置 DNS。关闭 `dns-direct-fallback-proxy`，避免直连 DNS 失败时隐式经代理重试；网络对 DoH 不可达时可能需要调整 DNS。保留系统备用 DNS，不承诺消除全部 DNS 泄漏。

公开配置不含节点、密码、订阅令牌、CA 私钥；MITM 关闭，去掉旧 Google HTTPS 重写。域名/IP 分流不需要 HTTPS 解密。IPv6、地区正则和分组选择仍需在当前版本 Shadowrocket 上实际验证。

## 更新和验证

```sh
python3 scripts/build_shadowrocket.py --refresh
python3 scripts/validate_shadowrocket.py
python3 -m unittest discover -s tests -v
```

配置、默认组来自 `config/services.json`、`config/regions.json` 与 `config/rules.ini`；小火箭专用参数、前四条和额外国内服务来自 `config/shadowrocket.json`。本地 Apple/ChatGPT 等列表始终从当前仓库读取；上游下载失败会停止，不以空列表继续。

原有 GitHub 每日更新流程同时重建小火箭规则。客户端需要更新规则集；改了分组或配置参数时还要更新配置。配置文件的更新地址已改为本仓库，不再指向旧第三方 lazy_group 模板。

已验证规则格式、源文件哈希、首四条保留、七条及其子域名优先归属、服务分组默认值、循环引用、HOME 先于普通局域网、共享 CDN 边界与地区前缀识别。另外使用 macOS Apple Foundation 正则引擎检查了地区筛选表达式及转发前缀样例。HOME 包含 /24 与排除 /16 的实际 TUN 路由优先级、地区自动/手动组的客户端行为仍需设备确认。未执行 iPad 导入、实际节点连通、iCloud 到达或 Apple Intelligence 功能激活测试；静态验证不是官方 Shadowrocket 解析器验证。

本地的旧草稿已备份到仓库外，然后由这些新文件替换。原用户数据库不公开上传。
