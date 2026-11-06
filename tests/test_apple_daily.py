"""Preserve verified media DIRECT paths without overriding Apple AI/shared hosts."""
from pathlib import Path
import unittest
from test_rules import entries, matches
ROOT = Path(__file__).resolve().parents[1]

class AppleDailyTests(unittest.TestCase):
    def test_media_routes_direct_and_ai_priority_is_preserved(self):
        path = ROOT / 'rules/local/AppleDailyDirect.list'
        self.assertTrue(path.is_file(), 'verified media DIRECT provider is missing')
        daily = entries(path)
        ai = entries(ROOT / 'rules/local/Apple.list')
        for host in ['vod-ap-aoc.tv.apple.com', 'vod-ap-amt.tv.apple.com',
                     'uts-api.itunes.apple.com', 'amp-api.videos.apple.com',
                     'images-mercury.mzstatic.com', 'play-china.itunes-apple.com.akadns.net',
                     'amp-api-music-lb.itunes-apple.com.akadns.net',
                     'streamingaudio.g.aaplimg.com', 'aod.itunes.g.aaplimg.com']:
            self.assertTrue(any(matches(r, host) for r in daily), host)
        for host in ['gateway.icloud.com', 'twntc1.icloud-content.com',
                     'guzzoni-smoot.v.aaplimg.com', 'unrelated.aaplimg.com',
                     'unrelated.akadns.net', 'gsa.apple.com']:
            self.assertFalse(any(matches(r, host) for r in daily), host)
        template = (ROOT / 'Clash-Full.ini').read_text()
        direct_binding = next(r for r in template.splitlines() if 'AppleDailyDirect.yaml' in r)
        self.assertTrue(direct_binding.startswith('ruleset=DIRECT,'))
        self.assertLess(template.index('ruleset=🍏 Apple Intelligence,'), template.index(direct_binding))
        self.assertLess(template.index(direct_binding), template.index('ruleset=🍎 Apple,'))
        self.assertTrue(any(matches(r, 'apps.mzstatic.com') for r in ai))
        self.assertFalse(any(matches(r, 'aod.itunes.g.aaplimg.com.evil.example') for r in daily))
