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

    def test_direct_resolution_is_independent_of_proxy_dns(self):
        dns = yaml.safe_load((ROOT / 'config/clash-base.yaml').read_text())['dns']
        domestic = ['https://223.5.5.5/dns-query#DIRECT',
                    'https://223.6.6.6/dns-query#DIRECT']
        self.assertEqual(dns.get('direct-nameserver'), domestic)
        self.assertIs(dns.get('direct-nameserver-follow-policy'), False)
        self.assertEqual(dns['proxy-server-nameserver'], domestic)
        # OpenClash may put geosite:cn in fake-ip-filter: those queries need
        # domestic answers before a connection has selected DIRECT.
        self.assertEqual(dns['nameserver-policy']['geosite:cn'], domestic)
        self.assertTrue(all(x.startswith('https://') for x in dns['default-nameserver']))

    def test_service_dns_follows_existing_selectors(self):
        dns = yaml.safe_load((ROOT / 'config/clash-base.yaml').read_text())['dns']
        policy = dns['nameserver-policy']
        services = {'geosite:netflix': '🎥 Netflix',
                    'geosite:hbo': '🎬 HBO', 'geosite:tiktok': '👯‍♂️ TikTok'}
        self.assertEqual(set(policy), {'geosite:cn', *services})
        text = (ROOT / 'Clash-Full.ini').read_text()
        for key, group in services.items():
            self.assertEqual(policy[key], [
                'https://cloudflare-dns.com/dns-query#' + group,
                'https://dns.google/dns-query#' + group])
            self.assertIn('custom_proxy_group=' + group + '`select`', text)

    def test_apple_exact_route_still_precedes_intelligence(self):
        text = (ROOT / 'Clash-Full.ini').read_text()
        self.assertLess(text.index('ruleset=🍎 Apple,[]DOMAIN,gateway.icloud.com'),
                        text.index('ruleset=🍏 Apple Intelligence,'))

