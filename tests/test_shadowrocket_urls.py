"""Released iCloud configs must keep working after new sources are inserted."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_shadowrocket as build


class PublishedUrlTests(unittest.TestCase):
    def test_source_insertion_does_not_rename_existing_provider(self):
        url = 'https://raw.githubusercontent.com/AdamCaoyu/routing-rules/refs/heads/main/rules/filtered/AmazonServices.yaml'
        self.assertEqual(build.provider_filename(url), '46-AmazonServices.list')

    def test_icloud_legacy_urls_keep_same_payload(self):
        names = ['AmazonServices', 'Amazon_No_Resolve', 'BiliBili', 'NetEaseMusic',
                 'Baidu', 'DouBan', 'WeChat', 'DouYin', 'Sina', 'Zhihu',
                 'XiaoHongShu', 'China', 'China_Domain', 'Global_Classical_No_Resolve']
        for index, name in enumerate(names, 45):
            with self.subTest(name=name):
                old = ROOT / 'shadowrocket/rules' / f'{index:02d}-{name}.list'
                current = old.with_name(f'{index+1:02d}-{name}.list')
                self.assertTrue(old.is_file(), f'Released URL removed: {old.name}')
                self.assertEqual(old.read_bytes(), current.read_bytes())


if __name__ == '__main__':
    unittest.main()
