"""Check real subconverter output, without printing node credentials.
Usage: python3 scripts/validate_generated.py CONFIG.yaml [PROVIDER_FIXTURE_DIR]
Requires PyYAML. The optional directory contains downloaded test provider payloads.
"""
import sys
import re
import ipaddress
from pathlib import Path
from urllib.parse import urlparse
import yaml

config = yaml.safe_load(Path(sys.argv[1]).read_text())
groups = {g['name']: g for g in config['proxy-groups']}
ai = '🍏 Apple Intelligence'
for name in ['所有','香港','台湾','日本','新加坡','韩国','美国','其他']:
    g = groups[name+'-自动']
    assert g['type'] == 'url-test'
    assert g['interval'] == 180 and g['tolerance'] == 100
    assert g['proxies'] and 'DIRECT' not in g['proxies']
    assert g['proxies'][-1] == 'REJECT'
assert groups[ai]['proxies'][0] == '💬 ChatGPT'
assert groups['☁️ OneDrive']['proxies'][0] == '美国节点'
assert groups['🔑 微软登录']['proxies'][0] == '☁️ OneDrive'
assert groups['Ⓜ️ Microsoft']['proxies'][0] == 'DIRECT'
assert config['rules'][-1] == 'MATCH,DIRECT'
from generate_groups import region_patterns, eligible_pattern, service_names
node_names = {p['name'] for p in config['proxies']}
for name in service_names():
    assert groups[name]['type'] == 'select'
    assert set(groups[name]['proxies']) <= set(groups) | {'DIRECT','REJECT'}, name
    assert not (set(groups[name]['proxies']) & node_names), name
    assert '所有-手动' in groups[name]['proxies']
    assert '美国节点' in groups[name]['proxies']
for region,pattern in region_patterns().items():
    expected={n for n in node_names if re.search(pattern,n)}
    assert set(groups[region+'-自动']['proxies']) == expected | {'REJECT'}, region
    chooser=groups[region+'节点']
    assert chooser['type']=='select' and chooser['proxies'][0]==region+'-自动'
    assert set(chooser['proxies'])==expected | {region+'-自动','REJECT'}, region
for name in ['所有-自动','所有-手动']:
    expected={n for n in node_names if re.search(eligible_pattern(),n)}
    assert set(groups[name]['proxies'])==expected | {'REJECT'}, name
for n in node_names:
    memberships=[r for r in region_patterns() if n in groups[r+'节点']['proxies']]
    assert len(memberships)<=1,(n,memberships)
assert '台日新韩-自动' not in groups and '港台日新韩-自动' not in groups

rules = []
for rule in config['rules']:
    fields = rule.split(',')
    if fields[0] != 'RULE-SET':
        rules.append(rule)
        continue
    provider = config['rule-providers'][fields[1]]
    assert provider['interval'] == 86400
    assert '/getruleset' not in provider['url'], 'Provider depends on converter at runtime'
    fixture = Path(sys.argv[2]) / Path(urlparse(provider['url']).path).name
    payload = yaml.safe_load(fixture.read_text())['payload']
    for entry in payload:
        if provider['behavior'] == 'domain':
            if entry.startswith('+.'):
                rules.append('DOMAIN-SUFFIX,' + entry[2:] + ',' + fields[2])
            else:
                rules.append('DOMAIN,' + entry + ',' + fields[2])
        elif provider['behavior'] == 'ipcidr':
            kind = 'IP-CIDR6' if ':' in entry else 'IP-CIDR'
            rules.append(','.join([kind,entry,fields[2]] + fields[3:]))
        else:
            parts = entry.split(',')
            rules.append(','.join(parts[:2] + [fields[2]] + parts[2:]))

def first_domain_match(domain):
    for rule in rules:
        parts = rule.split(',')
        kind, value = parts[:2]
        if kind == 'MATCH':
            return value
        if (kind == 'DOMAIN' and domain == value or
            kind == 'DOMAIN-SUFFIX' and (domain == value or domain.endswith('.' + value)) or
            kind == 'DOMAIN-KEYWORD' and value in domain):
            return parts[2]

cases = {}
for domain in ['gateway.icloud.com', 'apple-relay.apple.com',
               'apple-relay.fastly-edge.com', 'apple-relay.cloudflare.com',
               'guzzoni.apple.com', 'cp4.cloudflare.com', 'gspe1-ssl.ls.apple.com']:
    cases['sub.' + domain] = ai
for domain in ['guzzoni.apple.com', 'api.smoot.apple.com', 'apple-relay.apple.com',
               'apple-relay.cloudflare.com', 'apple-relay.fastly-edge.com',
               'cp4.cloudflare.com', 'apple-relay.mask.apple-dns.net',
               'gateway.icloud.com', 'gspe1-ssl.ls.apple.com']:
    cases[domain] = ai
for domain in ['www.apple.com', 'apps.mzstatic.com',
               'push.apple.com', 'time.apple.com']:
    cases[domain] = '🍎 Apple'
cases.update({'chatgpt.com':'💬 ChatGPT','auth.openai.com':'💬 ChatGPT',
              'cdn.oaistatic.com':'💬 ChatGPT','files.oaiusercontent.com':'💬 ChatGPT',
              'chatgpt.livekit.cloud':'💬 ChatGPT','openaiassets.blob.core.windows.net':'💬 ChatGPT',
              'claude.ai':'🧠 Claude','claude.com':'🧠 Claude','gemini.google.com':'🔎 Google',
              'grok.com':'🤖 Grok','grok.x.com':'🤖 Grok','x.com':'🕊️ Twitter(X)',
              'meta.ai':'🦙 Meta AI','perplexity.ai':'🔍 Perplexity','poe.com':'✨ 其他 AI',
              'github.com':'📘 GitHub','githubcopilot.com':'📘 GitHub',
              'accounts.google.com':'🔎 Google','login.microsoftonline.com':'🔑 微软登录',
              'login.live.com':'🔑 微软登录','copilot.microsoft.com':'Ⓜ️ Microsoft',
              'copilot.com':'Ⓜ️ Microsoft','onedrive.live.com':'☁️ OneDrive',
              'paypal.com':'💳 PayPal','amazon.com':'🌳 Amazon',
              'netflix.com':'🎥 Netflix','youtube.com':'🎞️ YouTube',
              'baidu.com':'DIRECT','router.lan':'DIRECT',
              'unclassified-example.invalid':'DIRECT'})

cases.update({'account.live.com':'🔑 微软登录','oauth.live.com':'🔑 微软登录',
              'aadcdn.msauth.net':'🔑 微软登录','aadcdn.msftauth.net':'🔑 微软登录',
              'graph.microsoft.com':'🔑 微软登录',
              'onedrive.cloud.microsoft':'☁️ OneDrive','skyapi.live.net':'☁️ OneDrive',
              'officeapps.live.com':'☁️ OneDrive','outlook.live.com':'Ⓜ️ Microsoft',
              'unrelated.trafficmanager.net':'Ⓜ️ Microsoft',
              'venmo.s3.amazonaws.com':'💳 PayPal','dai3fd1oh325y.cloudfront.net':'🎬 HBO',
              'cloudsync-prod.s3.amazonaws.com':'🕹️ Game',
              'ubisoft-orbit-savegames.s3.amazonaws.com':'🕹️ Game',
              'appldnld.apple.com.edgesuite.net':'🍎 Apple','e16991.b.akamaiedge.net':'🍎 Apple',
              'apple.com.akadns.net':'🍎 Apple','apple-support.akadns.net':'🍎 Apple',
              'redirector.offline-maps.gvt1.com':'🔎 Google','beacons.gvt2.com':'🔎 Google',
              'trae.ai':'✨ 其他 AI','marscode.com':'✨ 其他 AI','coderabbit.gallery.vsassets.io':'✨ 其他 AI',
              'unrelated.us-west-2.amazonaws.com':'🌍 国外',
              'unrelated.execute-api.us-east-1.amazonaws.com':'🌍 国外',
              'unrelated.execute-api.ap-southeast-1.amazonaws.com':'🌍 国外'})
cases.update({'ppl-ai-file-upload.s3.amazonaws.com':'🔍 Perplexity',
              'pplx-res.cloudinary.com':'🔍 Perplexity',
              'servd-anthropic-website.b-cdn.net':'🧠 Claude',
              'unrelated.cloudfront.net':'🌍 国外'})
# Shared Akamai names must not be classified as Apple/Microsoft merely by their CDN.
for domain in ['unrelated.akadns.net','unrelated.edgesuite.net','unrelated.b.akamaiedge.net','unrelated.g.akamaiedge.net']:
    assert first_domain_match(domain) not in ['🍎 Apple','Ⓜ️ Microsoft'], domain
for domain in ['host.livekit.cloud','turn.livekit.cloud','browser-intake-datadoghq.com','gateway.ai.cloudflare.com']:
    assert first_domain_match(domain) != '✨ 其他 AI', domain

# Domains are checked without DNS; IP-only connections independently exercise IP providers.
for address, expected in [('192.168.100.1','DIRECT'),('23.246.1.1','🎥 Netflix'),('2607:fb10::1','🎥 Netflix')]:
    ip = ipaddress.ip_address(address)
    actual = None
    for rule in rules:
        f = rule.split(',')
        if f[0] in ['IP-CIDR','IP-CIDR6'] and ip in ipaddress.ip_network(f[1],strict=False):
            actual = f[2]; break
        if f[0] == 'MATCH': actual=f[1]; break
    assert actual == expected, f'{address}: {actual} != {expected}'
lan = next(r for r in rules if r.startswith('IP-CIDR,192.168.0.0/16,'))
assert lan.endswith(',no-resolve'), 'LAN should not force DNS before service domain rules'

for domain, expected in cases.items():
    actual = first_domain_match(domain)
    assert actual == expected, f'{domain}: {actual} != {expected}'
known = set(groups) | {p['name'] for p in config['proxies']} | {'DIRECT', 'REJECT'}
for group in groups.values():
    assert group['proxies'], group['name']
    assert set(group['proxies']) <= known, group['name']
for rule in rules:
    assert 'ProxyGroupName' not in rule, 'Unconverted policy placeholder'
print(f'PASS: {len(rules)} expanded rules, {len(groups)} groups; {len(cases)} routing cases and empty-group guards')
