"""Regression cases for observed multi-country prefixes and dirty node groups."""
from pathlib import Path
import importlib.util
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('generate_groups',ROOT/'scripts/generate_groups.py')
g=importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)

class RegionTests(unittest.TestCase):
    def test_name_classification_is_exclusive(self):
        cases={
            'US🔛❻gR.TW台北|AI':'美国','HK🔛❻gR.US王者':'香港',
            '❶gR.HKT节点':'香港','❻gR.TW节点':'台湾','❷TJ.JP节点':'日本',
            '❸gR.SG节点':'新加坡','KR Seoul':'韩国','❻gR.US节点':'美国',
            '❶TJ.RU节点':'其他','❶TJ.UK节点':'其他','❸gR.TR节点':'其他',
            'US Test':'美国','us test':'美国','Taiwan 01':'台湾',
            '🇯🇵 JP 01':'日本','香港 HKT 01':'香港',
            'JP US 双标记':None,'ZZ🔛TW台北':None,'RUS Test':None,
            '无地区标记':None,
        }
        for name,expected in cases.items():
            hits=[region for region,pattern in g.region_patterns().items() if re.search(pattern,name)]
            self.assertEqual(hits,[] if expected is None else [expected],name)

    def test_exclusions_apply_to_every_node_group(self):
        for name in ['US 下载专用','US 备用','US 公益','◈耗尽◈BR 巴西','香港 维护','流量:123GB 等级6剩15天']:
            for pattern in [g.eligible_pattern(),*g.region_patterns().values()]:
                self.assertIsNone(re.search(pattern,name),name)

    def test_services_only_reference_groups_and_builtins(self):
        rows=g.build_groups().splitlines()
        for row in rows:
            if row.startswith('custom_proxy_group='):
                name,kind,*members=row.split('=',1)[1].split('`')
                if name in g.service_names():
                    self.assertEqual(kind,'select')
                    self.assertTrue(all(m.startswith('[]') for m in members),name)
                    self.assertIn('[]所有-手动',members)
                    self.assertIn('[]美国节点',members)
        self.assertNotIn('台日新韩',g.build_groups())
        self.assertNotIn('港台日新韩',g.build_groups())

if __name__=='__main__':unittest.main()
