"""DNS must remain usable independently of ordinary service selectors."""
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class DnsTests(unittest.TestCase):
    def test_template_loads_dns_base_and_contains_matching_groups(self):
        text = (ROOT / 'Clash-Full.ini').read_text()
        self.assertTrue('clash_rule_base=https://raw.githubusercontent.com/AdamCaoyu/routing-rules/refs/heads/main/config/clash-base.yaml' in text)
        dns = yaml.safe_load((ROOT / 'config/clash-base.yaml').read_text())['dns']
        nameservers = dns['nameserver']
        self.assertEqual(len(nameservers), 2)
        for resolver in nameservers:
            self.assertTrue(resolver.startswith('https://'))
            group = resolver.split('#', 1)[1]
            self.assertIn('custom_proxy_group=' + group + '`fallback`', text)
        self.assertNotIn('GitHub-TW-Fallback', text)
        self.assertFalse(any('国外' in n for n in nameservers))

    def test_apple_exact_and_ai_suffix_dns_boundaries(self):
        dns = yaml.safe_load((ROOT / 'config/clash-base.yaml').read_text())['dns']
        policy = dns['nameserver-policy']
        self.assertTrue(all(x.endswith('#DIRECT') for x in policy['+.icloud.com']))
        self.assertEqual(policy['gateway.icloud.com'], policy['+.icloud.com'])
        self.assertEqual(policy['+.gateway.icloud.com'], dns['nameserver'])
        self.assertEqual(policy['+.gspe1-ssl.ls.apple.com'], dns['nameserver'])
        self.assertTrue(all(x.startswith('https://') for x in dns['default-nameserver']))
        text = (ROOT / 'Clash-Full.ini').read_text()
        self.assertLess(text.index('ruleset=🍎 Apple,[]DOMAIN,gateway.icloud.com'),
                        text.index('ruleset=🍏 Apple Intelligence,'))

