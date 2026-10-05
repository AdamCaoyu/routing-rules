"""Generate Shadowrocket native providers and selectors from OpenClash sources.
Use --refresh to download current upstream sources. Local rules are always fresh.
"""
from pathlib import Path
import concurrent.futures
import hashlib
import json
import re
import sys
import urllib.request
import yaml
from generate_groups import services, region_patterns, eligible_pattern

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'shadowrocket'
CACHE = ROOT / '.local/shadowrocket-sources'
PUBLIC = 'https://raw.githubusercontent.com/AdamCaoyu/routing-rules/main/shadowrocket/'
REFRESH = '--refresh' in sys.argv
SUPPORTED = {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD', 'IP-CIDR', 'IP-CIDR6', 'IP-ASN', 'USER-AGENT', 'URL-REGEX', 'GEOIP'}


def active(text):
    return [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith(('#', ';'))]


def normalized(entry, kind):
    if kind in {'clash-domain', 'native-domain'}:
        if entry.startswith(('+.','.')):
            return 'DOMAIN-SUFFIX,' + entry.lstrip('+.')
        if '*' in entry:
            raise ValueError('Unsupported domain wildcard: ' + entry)
        return 'DOMAIN,' + entry
    if kind == 'clash-ipcidr':
        return ('IP-CIDR6,' if ':' in entry else 'IP-CIDR,') + entry + ',no-resolve'
    parts = entry.split(',')
    parts[0] = parts[0].replace('IP6-CIDR', 'IP-CIDR6')
    if parts[0] == 'PROCESS-NAME':
        return None
    if parts[0] not in SUPPORTED:
        raise ValueError('Unsupported rule: ' + entry)
    if kind == 'native':
        # Native lists may carry a default policy; provider binding determines policy.
        parts = parts[:2] + [p for p in parts[2:] if p == 'no-resolve']
    if len(parts) < 2 or any(p != 'no-resolve' for p in parts[2:]):
        raise ValueError('Unexpected rule fields: ' + entry)
    if parts[0] in {'IP-CIDR', 'IP-CIDR6', 'IP-ASN'} and 'no-resolve' not in parts:
        parts.append('no-resolve')
    return ','.join(parts)


def download(url):
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest() + '.txt')
    if REFRESH or not path.exists():
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=30) as response:
                    data = response.read().decode('utf-8-sig')
                path.write_text(data)
                break
            except Exception:
                if attempt == 2:
                    raise
    return path.read_text()


def source_payload(source):
    url, kind = source['url'], source['kind']
    marker = '/routing-rules/'
    if marker in url and '/rules/' in url:
        path = ROOT / ('rules/' + url.split('/rules/', 1)[1])
        data = path.read_text()
    else:
        data = download(url)
    values = yaml.safe_load(data)['payload'] if kind.startswith('clash-') else active(data)
    if not isinstance(values, list) or not values:
        raise ValueError('Empty source: ' + url)
    kept, removed = [], 0
    for entry in values:
        rule = normalized(entry, kind)
        if rule is None:
            removed += 1
        elif rule not in kept:
            kept.append(rule)
    if not kept:
        raise ValueError('No usable rules: ' + url)
    return kept, {'source': url, 'format': kind, 'count': len(kept), 'removed_process_rules': removed,
                  'source_sha256': hashlib.sha256(data.encode()).hexdigest()}


def group_lines():
    regions = {name: pattern.replace("[A-Za-z]{2,3}", "[A-Za-z]{2}[A-Za-z]?")
               for name, pattern in region_patterns().items()}
    choices = ['DIRECT', '所有-手动', '所有-自动'] + [r + '节点' for r in regions] + ['REJECT']
    lines = []
    for service in services() + [{'name': '📺 哔哩哔哩', 'default': 'DIRECT', 'extra': []}]:
        members = list(dict.fromkeys([service['default'], *service['extra'], *choices]))
        lines.append(service['name'] + ' = select,' + ','.join(members) + ',policy-select-name=' + service['default'])
    lines += [
        '所有-手动 = select,REJECT,policy-regex-filter=' + eligible_pattern(),
        '所有-自动 = url-test,REJECT,policy-regex-filter=' + eligible_pattern() + ',url=http://www.gstatic.com/generate_204,interval=600,tolerance=100,timeout=5',
    ]
    for region, pattern in regions.items():
        lines.append(region + '节点 = select,' + region + '-自动,REJECT,policy-regex-filter=' + pattern + ',policy-select-name=' + region + '-自动')
    for region, pattern in regions.items():
        lines.append(region + '-自动 = url-test,REJECT,policy-regex-filter=' + pattern + ',url=http://www.gstatic.com/generate_204,interval=600,tolerance=100,timeout=5')
    return lines


def build():
    OUT.mkdir(exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    settings = json.loads((ROOT / 'config/shadowrocket.json').read_text())
    sources = []
    bindings = []
    for line in active((ROOT / 'config/rules.ini').read_text()):
        policy, spec = line.split('=', 1)[1].split(',', 1)
        if spec.startswith('[]'):
            rule = spec[2:]
            bindings.append(('inline', 'FINAL,DIRECT' if rule == 'FINAL' else rule + ',' + policy))
            continue
        kind, rest = spec.split(':', 1)
        url = rest.rsplit(',', 1)[0]
        source = {'url': url, 'kind': kind, 'policy': policy}
        sources.append(source)
        bindings.append(('source', source))
    # Preserve useful domestic categories absent from OpenClash, before general globals.
    insertion = next(i for i, (kind, item) in enumerate(bindings)
                     if kind == 'source' and '/Global/' in item['url'])
    extras = []
    for item in settings['domestic_extras']:
        source = {'url': item['url'], 'kind': 'native', 'policy': item['policy']}
        sources.append(source)
        extras.append(('source', source))
        # Shadowrocket Apple/China/Global classical lists omit a companion domain set.
        if '/China/' in item['url']:
            domain_source = {'url': item['url'].replace('China.list', 'China_Domain.list'), 'kind': 'clash-domain', 'policy': item['policy']}
            # Native domain sets have one domain per line, not YAML.
            domain_source['kind'] = 'native-domain'
            sources.append(domain_source)
            extras.append(('source', domain_source))
    bindings[insertion:insertion] = extras
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        payloads = list(executor.map(source_payload, sources))
    lookup = {id(source): payload for source, payload in zip(sources, payloads)}
    rules_dir = OUT / 'rules'
    rules_dir.mkdir(exist_ok=True)
    rule_lines = list(settings['first_rules'])
    ai_domains = ['gateway.icloud.com', 'apple-relay.apple.com', 'apple-relay.fastly-edge.com',
                  'apple-relay.cloudflare.com', 'guzzoni.apple.com', 'cp4.cloudflare.com', 'gspe1-ssl.ls.apple.com']
    rule_lines += ['DOMAIN-SUFFIX,' + domain + ',🍏 Apple Intelligence' for domain in ai_domains]
    records = []
    files = set()
    for kind, item in bindings:
        if kind == 'inline':
            rule_lines.append(item)
            continue
        payload, metadata = lookup[id(item)]
        filename = f'{len(records):02d}-' + item['url'].rsplit('/', 1)[-1].rsplit('.', 1)[0] + '.list'
        files.add(filename)
        body = '# Converted for Shadowrocket; Source: ' + item['url'] + '\n'
        if 'blackmatrix7/' in item['url'] or '/rules/filtered/' in item['url']:
            body += '# Attribution: blackmatrix7/ios_rule_script; see sources.json and repository licenses.\n'
        if 'MetaCubeX/' in item['url']:
            body += '# Attribution: MetaCubeX/meta-rules-dat; GPL-3.0, see repository licenses.\n'
        body += '\n'.join(payload) + '\n'
        (rules_dir / filename).write_text(body)
        metadata.update(file=filename, policy=item['policy'], sha256=hashlib.sha256(body.encode()).hexdigest())
        records.append(metadata)
        rule_lines.append('RULE-SET,' + PUBLIC + 'rules/' + filename + ',' + item['policy'])
    # Snapshot the two retained external blockers for offline routing checks.
    for line in settings['first_rules']:
        if not line.startswith('RULE-SET,'):
            continue
        _, url, policy = line.split(',')
        data = download(url)
        payload = [normalized(entry, 'native') for entry in active(data)]
        payload = [entry for entry in payload if entry is not None]
        filename = 'retained-' + url.rsplit('/', 1)[-1]
        body = '# Retained original external source: ' + url + '\n' + '\n'.join(payload) + '\n'
        (rules_dir / filename).write_text(body)
        files.add(filename)
        records.append({'file': filename, 'policy': policy, 'source': url, 'format': 'native',
                        'count': len(payload), 'original_binding': True,
                        'source_sha256': hashlib.sha256(data.encode()).hexdigest(),
                        'sha256': hashlib.sha256(body.encode()).hexdigest()})
    for path in rules_dir.glob('*.list'):
        if path.name not in files:
            path.unlink()
    general = dict(settings['general'])
    general['update-url'] = PUBLIC + 'caoyu-shadowrocket.conf'
    # System connectivity bypass and HOME-specific route are preserved from the iPad config.
    # Retain IPv6 for IPv6-only mobile networks; prefer IPv4 as in the original.
    # Avoid sending failed domestic DNS lookups through a proxy implicitly.
    general['dns-direct-fallback-proxy'] = 'false'
    # Apple's AI endpoints use the same configurable DNS as other service rules.
    host = {k: v for k, v in settings['host'].items() if k not in {'*.apple.com', '*.icloud.com'}}
    text = '# 草鱼 Shadowrocket：服务分组对齐 OpenClash，前四条个人规则原样保留。\n'
    text += '# 节点沿用首页订阅；HOME 必须是已有节点/订阅策略。MITM 关闭。\n'
    sections = [('General', [k + ' = ' + v for k, v in general.items()]), ('Proxy', []),
                ('Proxy Group', group_lines()), ('Rule', rule_lines),
                ('Host', [k + ' = ' + v for k, v in host.items()]), ('MITM', ['enable = false'])]
    for section, lines in sections:
        text += '\n[' + section + ']\n' + '\n'.join(lines) + '\n'
    (OUT / 'caoyu-shadowrocket.conf').write_text(text)
    (OUT / 'sources.json').write_text(json.dumps({'sources': records, 'node_credentials': False,
        'source_policy': 'OpenClash maintained sources converted to Shadowrocket; original useful domestic lists retained',
        'first_rules': settings['first_rules']}, ensure_ascii=False, indent=2) + '\n')
    print(f'Built {len(group_lines())} groups and {len(records)} native providers')


if __name__ == '__main__':
    build()
