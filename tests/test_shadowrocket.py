"""Regressions for the published iOS config and source conversion."""
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_shadowrocket as build
import validate_shadowrocket as check


class ShadowrocketTests(unittest.TestCase):
    def test_published_configuration_routes_and_boundaries(self):
        report = check.validate()
        self.assertEqual(report['groups'], 51)
        self.assertEqual(report['status'], 'static checks passed')

    def test_region_auto_and_fixed_manual_choices(self):
        groups = {line.split(' = ', 1)[0]: line.split(' = ', 1)[1]
                  for line in build.group_lines()}
        self.assertNotIn('所有-自动', groups)
        self.assertTrue(groups['所有-手动'].startswith('select,PROXY,'))
        for region in build.region_patterns():
            picker = groups[region + '节点'].split(',')
            self.assertEqual(picker[:3], ['select', region + '-自动', region + '-手动'])
            self.assertIn('policy-select-name=' + region + '-自动', picker)
            self.assertTrue(groups[region + '-自动'].startswith('url-test,'))
            self.assertTrue(groups[region + '-手动'].startswith('select,'))
            self.assertNotIn('interval=', groups[region + '-手动'])

    def test_native_source_policy_is_not_embedded(self):
        self.assertEqual(build.normalized('DOMAIN-SUFFIX,example.com,PROXY', 'native'),
                         'DOMAIN-SUFFIX,example.com')
        self.assertEqual(build.normalized('IP-CIDR,192.168.0.0/16,DIRECT,no-resolve', 'native'),
                         'IP-CIDR,192.168.0.0/16,no-resolve')
        self.assertIsNone(build.normalized('PROCESS-NAME,com.apple.geod', 'clash-classic'))
        with self.assertRaises(ValueError):
            build.normalized('DOMAIN-WILDCARD,*.example.com', 'clash-classic')

    def test_region_regex_keeps_forwarding_prefix_behavior_without_option_commas(self):
        import re
        lines = build.group_lines()
        patterns = {}
        for line in lines:
            name, body = line.split(' = ', 1)
            if name.endswith('-手动') and name != '所有-手动':
                field = next(p for p in body.split(',') if p.startswith('policy-regex-filter='))
                patterns[name[:-3] + '节点'] = field.split('=', 1)[1]
        for node, region in [('US🔛TW台北', '台湾节点'), ('HK🔛US王者', '美国节点'),
                             ('US🔛HK🔛TW台北', '台湾节点'), ('香港 维护', '香港节点'),
                             ('US 下载专用', '美国节点'), ('RUS Test', None)]:
            hits = [name for name, pattern in patterns.items() if re.search(pattern, node)]
            self.assertEqual(hits, [] if region is None else [region], node)


if __name__ == '__main__':
    unittest.main()
