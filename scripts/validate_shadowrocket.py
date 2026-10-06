"""Offline structural and first-match tests; not an on-device import test."""
from pathlib import Path
import hashlib
import ipaddress
import json
import re
from generate_groups import services, region_patterns

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'shadowrocket'
AI = '🍏 Apple Intelligence'
DOMAINS = ['gateway.icloud.com', 'apple-relay.apple.com', 'apple-relay.fastly-edge.com',
           'apple-relay.cloudflare.com', 'guzzoni.apple.com', 'cp4.cloudflare.com', 'gspe1-ssl.ls.apple.com']


def active(text):
    return [l.strip() for l in text.splitlines() if l.strip() and not l.lstrip().startswith(('#', ';'))]


def sections(text):
    marks = list(re.finditer(r'^\[([^\]\n]+)\]\s*$', text, re.M))
    return {m[1]: text[m.end():marks[i+1].start() if i+1 < len(marks) else len(text)] for i, m in enumerate(marks)}


def validate():
    config_path = OUT / 'caoyu-shadowrocket.conf'
    text = config_path.read_text()
    config = sections(text)
    settings = json.loads((ROOT / 'config/shadowrocket.json').read_text())
    rules = active(config['Rule'])
    assert rules[:4] == settings['first_rules'], 'First four rules changed'
    assert rules[4:11] == ['DOMAIN-SUFFIX,' + d + ',' + AI for d in DOMAINS]
    assert rules[-1] == 'FINAL,DIRECT'
    for bad in ['ca-p12', 'ca-passphrase', 'password=', 'private-key', 'BEGIN PRIVATE KEY']:
        assert bad not in text.lower(), bad
    assert not active(config['Proxy'])
    assert active(config['MITM']) == ['enable = false']
    groups = {}
    for line in active(config['Proxy Group']):
        name, body = [s.strip() for s in line.split('=', 1)]
        assert name not in groups, name
        groups[name] = body.split(',')
    required = {service['name'] for service in services()}
    assert required <= set(groups)
    builtins = {'DIRECT', 'PROXY', 'REJECT', 'HOME'}
    refs = {}
    for name, fields in groups.items():
        refs[name] = [f for f in fields[1:] if '=' not in f]
        assert all(r in groups or r in builtins for r in refs[name]), (name, refs[name])
        assert fields[0] == 'select', name
        assert '-自动' not in name, name
    for service in services():
        fields = groups[service['name']]
        assert fields[0] == 'select'
        default = '所有-手动' if service['default'] == '所有-自动' else service['default']
        assert 'policy-select-name=' + default in fields
        assert default in refs[service['name']]
    for region, pattern in region_patterns().items():
        assert 'policy-regex-filter=' + pattern.replace('[A-Za-z]{2,3}', '[A-Za-z]{2}[A-Za-z]?') in groups[region + '节点']
        assert not refs[region + '节点']
    assert '所有-自动' not in groups
    assert 'policy-select-name=PROXY' in groups['所有-手动']
    def walk(name, stack):
        assert name not in stack, (name, stack)
        for ref in refs.get(name, []):
            if ref not in builtins:
                walk(ref, stack + [name])
    for name in groups:
        walk(name, [])
    general = dict(l.split('=', 1) for l in active(config['General']))
    general = {k.strip(): v.strip() for k, v in general.items()}
    assert general['bypass-system'] == 'true'
    assert general['tun-included-routes'] == '192.168.100.0/24'
    assert general['ipv6'] == settings['general']['ipv6']
    assert general['prefer-ipv6'] == 'false'
    assert general['dns-direct-fallback-proxy'] == 'false'
    assert general['update-url'].endswith('/shadowrocket/caoyu-shadowrocket.conf')
    assert '*.apple.com' not in config['Host'] and '*.icloud.com' not in config['Host']
    manifest = json.loads((OUT / 'sources.json').read_text())['sources']
    providers = {item['file']: item for item in manifest}
    external = {item['source']: item for item in manifest if item.get('original_binding')}
    expanded = []
    allowed = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'IP-CIDR', 'IP-CIDR6', 'IP-ASN', 'USER-AGENT', 'URL-REGEX', 'GEOIP', 'FINAL'}
    # Expand retained external blockers from verified local snapshots as well.
    for line in rules:
        fields = line.split(',')
        if fields[0] == 'RULE-SET':
            name = fields[1].rsplit('/', 1)[-1]
            if name not in providers:
                assert line in settings['first_rules'][2:4], line
                item = external[fields[1]]
                name = item['file']
            else:
                item = providers[name]
            path = OUT / 'rules' / name
            body = path.read_text()
            assert hashlib.sha256(body.encode()).hexdigest() == item['sha256']
            payload = active(body)
            assert len(payload) == item['count']
            assert fields[2] == item['policy']
            for rule in payload:
                p = rule.split(',')
                expanded.append(','.join(p[:2] + [fields[2]] + p[2:]))
        else:
            expanded.append(line)
    for line in expanded:
        p = line.split(',')
        assert p[0] in allowed, line
        policy = p[1] if p[0] == 'FINAL' else p[2]
        assert policy in groups or policy in builtins, line
        if p[0] in {'IP-CIDR', 'IP-CIDR6'}:
            ipaddress.ip_network(p[1], strict=False)
            assert p[3:] == ['no-resolve'], line
    def match(domain):
        for line in expanded:
            p = line.split(',')
            if p[0] == 'FINAL':
                return p[1]
            if (p[0] == 'DOMAIN' and domain == p[1] or
                p[0] == 'DOMAIN-SUFFIX' and (domain == p[1] or domain.endswith('.' + p[1])) or
                p[0] == 'DOMAIN-KEYWORD' and p[1] in domain):
                return p[2]
    cases = {
        'api.smoot.apple.com': AI, 'apple-relay.mask.apple-dns.net': AI,
        'www.apple.com': '🍎 Apple', 'apps.mzstatic.com': '🍎 Apple', 'mask.icloud.com': '🍎 Apple',
        'push.apple.com': '🍎 Apple', 'time.apple.com': '🍎 Apple', 'iqos.com': '日本节点',
        'chatgpt.com': '💬 ChatGPT', 'auth.openai.com': '💬 ChatGPT', 'chatgpt.livekit.cloud': '💬 ChatGPT',
        'claude.ai': '🧠 Claude', 'grok.com': '🤖 Grok', 'meta.ai': '🦙 Meta AI', 'perplexity.ai': '🔍 Perplexity',
        'github.com': '📘 GitHub', 'poe.com': '✨ 其他 AI', 'gemini.google.com': '🔎 Google',
        'login.live.com': '🔑 微软登录', 'onedrive.live.com': '☁️ OneDrive', 'outlook.live.com': 'Ⓜ️ Microsoft',
        'paypal.com': '💳 PayPal', 'amazon.com': '🌳 Amazon', 'youtube.com': '🎞️ YouTube',
        'netflix.com': '🎥 Netflix', 'spotify.com': '🎵 Spotify', 'bilibili.com': '📺 哔哩哔哩',
        'baidu.com': 'DIRECT', 'router.lan': 'DIRECT', 'unclassified-example.invalid': 'DIRECT',
    }
    for domain in DOMAINS:
        cases[domain] = AI
        cases['sub.' + domain] = AI
    for domain, expected in cases.items():
        assert match(domain) == expected, (domain, expected, match(domain))
    for domain in ['unrelated.akadns.net', 'unrelated.edgesuite.net', 'unrelated.b.akamaiedge.net']:
        assert match(domain) not in {'🍎 Apple', 'Ⓜ️ Microsoft'}, domain
    for domain in ['unrelated-' + d for d in DOMAINS]:
        assert match(domain) != AI, domain
    for address, expected in [('192.168.100.1', 'HOME'), ('192.168.2.1', 'DIRECT')]:
        ip = ipaddress.ip_address(address)
        actual = next((p[2] for line in expanded if (p := line.split(','))[0] in {'IP-CIDR','IP-CIDR6'} and ip in ipaddress.ip_network(p[1], strict=False)), None)
        assert actual == expected, (address, actual)
    test = sections((OUT / 'lazy_group-AppleAI-test.conf').read_text())
    test_rules = active(test['Rule'])
    assert test_rules[:11] == rules[:11]
    assert active(test['MITM']) == ['enable = false']
    test_groups = {line.split('=', 1)[0].strip() for line in active(test['Proxy Group'])}
    for line in test_rules:
        fields = line.split(',')
        target = fields[1] if fields[0] == 'FINAL' else fields[2]
        assert target in test_groups | builtins, target
    assert all(line.split('=', 1)[1].strip().startswith('select,') for line in active(test['Proxy Group']))
    assert not any(key in test['Proxy Group'] for key in ['interval=', 'url=', 'timeout=', 'tolerance='])
    assert all(line.endswith(' 302') for line in active(test['URL Rewrite']))
    report = {'status': 'static checks passed', 'groups': len(groups), 'providers': len(manifest),
              'expanded_rules': len(expanded), 'domain_checks': len(cases) + 10,
              'preserved_first_rules': rules[:4], 'home_route_checks': 2, 'on_device_import': 'not performed'}
    (OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))
    return report


if __name__ == '__main__':
    validate()
