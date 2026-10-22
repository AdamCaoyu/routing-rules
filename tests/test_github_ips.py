"""GitHub pure-IP traffic must not fall through to DIRECT."""
from pathlib import Path
import ipaddress
import sys
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import sync_sources


class GitHubIpTests(unittest.TestCase):
    def test_official_provider_covers_observed_addresses(self):
        rules = yaml.safe_load((ROOT / 'rules/filtered/GitHubIPs.yaml').read_text())['payload']
        networks = [ipaddress.ip_network(r.split(',')[1]) for r in rules]
        for address in ['140.82.113.3', '140.82.113.6', '185.199.109.154', '20.27.177.113']:
            self.assertTrue(any(ipaddress.ip_address(address) in n for n in networks), address)
        for address in ['192.168.100.1', '223.5.5.5', '17.1.1.1', '8.8.8.8']:
            self.assertFalse(any(ipaddress.ip_address(address) in n for n in networks), address)
        self.assertTrue(all(r.endswith(',no-resolve') for r in rules))

    def test_shared_actions_networks_are_not_imported(self):
        rules = sync_sources.github_ip_rules({'web': ['140.82.112.0/20'],
                    'api': ['185.199.108.0/22'], 'git': ['140.82.112.0/20'],
                    'actions': ['0.0.0.0/0']})
        self.assertEqual(len(rules), 2)
        self.assertFalse(any('0.0.0.0/0' in r for r in rules))
        with self.assertRaises(ValueError):
            sync_sources.github_ip_rules({'web': ['0.0.0.0/0'], 'api': [], 'git': []})

    def test_protocol_sniffers_and_ip_binding_are_present(self):
        c = yaml.safe_load((ROOT / 'config/clash-base.yaml').read_text())
        self.assertTrue(c['sniffer']['enable'])
        self.assertTrue(c['sniffer']['parse-pure-ip'])
        self.assertIn(443, c['sniffer']['sniff']['TLS']['ports'])
        self.assertFalse(c['sniffer']['override-destination'])
        rows = (ROOT / 'config/rules.ini').read_text().splitlines()
        index = next(i for i,r in enumerate(rows) if '/GitHubIPs.yaml' in r)
        self.assertTrue(rows[index].startswith('ruleset=📘 GitHub,'))
        self.assertLess(index, next(i for i,r in enumerate(rows) if '/Amazon/' in r))

