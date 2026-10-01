"""Protect concrete cross-service misroutes found in upstream providers."""
import importlib.util
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sync_sources',ROOT/'scripts/sync_sources.py')
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

class BoundaryTests(unittest.TestCase):
    def test_apple_keeps_own_cdn_but_not_entire_dns_platform(self):
        kept, removed = sync.filter_rules('AppleServices',[
            'DOMAIN-SUFFIX,akadns.net','DOMAIN,apple.com.akadns.net',
            'DOMAIN-SUFFIX,apple.com','IP-CIDR,17.0.0.0/8,no-resolve'])
        self.assertEqual(removed,['DOMAIN-SUFFIX,akadns.net'])
        self.assertIn('DOMAIN,apple.com.akadns.net',kept)
        self.assertIn('IP-CIDR,17.0.0.0/8,no-resolve',kept)

    def test_amazon_keeps_service_domain_not_other_tenants(self):
        kept, removed = sync.filter_rules('AmazonServices',[
            'DOMAIN-SUFFIX,amazon.com','DOMAIN-SUFFIX,cloudfront.net',
            'DOMAIN-SUFFIX,amazonaws.com','IP-CIDR,13.32.0.0/15,no-resolve'])
        self.assertEqual(kept,['DOMAIN-SUFFIX,amazon.com'])
        self.assertEqual(len(removed),3)

    def test_ai_does_not_assign_shared_infrastructure_to_a_single_service(self):
        kept, removed = sync.filter_rules('OtherAI',[
            '+.poe.com','+.host.livekit.cloud','browser-intake-datadoghq.com',
            '+.chatgpt.livekit.cloud'])
        self.assertIn('DOMAIN-SUFFIX,poe.com',kept)
        self.assertIn('DOMAIN-SUFFIX,chatgpt.livekit.cloud',kept)
        self.assertEqual(len(removed),2)

    def test_checked_in_providers_respect_boundaries(self):
        for name,(_,excluded,no_ip) in sync.SOURCES.items():
            rules=yaml.safe_load((ROOT/'rules/filtered'/f'{name}.yaml').read_text())['payload']
            self.assertTrue(rules)
            for rule in rules:
                fields=rule.split(',')
                self.assertNotIn(fields[1],excluded)
                if no_ip:self.assertNotIn(fields[0],['IP-CIDR','IP-CIDR6'])

    def test_shared_aws_comes_after_every_specific_service(self):
        rows=(ROOT/'config/rules.ini').read_text().splitlines()
        shared=next(i for i,r in enumerate(rows) if r.startswith('ruleset=🌍 国外,') and '/Amazon/' in r)
        for i,row in enumerate(rows):
            if row.startswith('ruleset=') and not row.startswith(('ruleset=🌍 国外,','ruleset=DIRECT,')):
                self.assertLess(i,shared)

if __name__=='__main__':unittest.main()
