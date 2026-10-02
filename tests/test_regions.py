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
            'US🔛❻gR.TW台北|AI':'台湾','HK🔛❻gR.US王者':'美国',
            '❶gR.HKT节点':'香港','❻gR.TW节点':'台湾','❷TJ.JP节点':'日本',
            '❸gR.SG节点':'新加坡','KR Seoul':'韩国','❻gR.US节点':'美国',
            '❶TJ.RU节点':'其他','❶TJ.UK节点':'其他','❸gR.TR节点':'其他',
            'US Test':'美国','us test':'美国','Taiwan 01':'台湾',
            '🇯🇵 JP 01':'日本','香港 HKT 01':'香港',
            'JP US 双标记':None,'ZZ🔛TW台北':'台湾','RUS Test':None,
            '无地区标记':None,'US🔛无地区标记':None,
            'US🔛TW台北':'台湾','US🔛HK🔛TW台北':'台湾',
            'US🔛JP节点':'日本','US🔛SG节点':'新加坡',
            'US🔛US王者':'美国','CN1•❸gR.TW台北':'台湾',
        }
        for name,expected in cases.items():
            hits=[region for region,pattern in g.region_patterns().items() if re.search(pattern,name)]
            self.assertEqual(hits,[] if expected is None else [expected],name)

    def test_status_labels_do_not_exclude_nodes(self):
        cases={'US 下载专用':'美国','US 备用':'美国','US 公益':'美国',
               '◈耗尽◈BR 巴西':'其他','香港 维护':'香港','TW 被墙':'台湾',
               'US🔛TW 失效':'台湾','US 过期':'美国'}
        for name,region in cases.items():
            self.assertIsNotNone(re.search(g.eligible_pattern(),name),name)
            hits=[r for r,p in g.region_patterns().items() if re.search(p,name)]
            self.assertEqual(hits,[region],name)
        self.assertIsNotNone(re.search(g.eligible_pattern(),'流量:123GB 等级6剩15天'))

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
