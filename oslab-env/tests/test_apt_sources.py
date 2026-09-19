import unittest

from oslab_setup.core.apt_sources import _active_uris, _contains_official_source, _rewrite


class AptSourceRewriteTests(unittest.TestCase):
    def test_rewrites_only_official_ubuntu_uris_in_legacy_format(self) -> None:
        source = (
            "deb http://archive.ubuntu.com/ubuntu resolute main universe\n"
            "deb http://security.ubuntu.com/ubuntu resolute-security main\n"
            "deb https://download.docker.com/linux/ubuntu resolute stable\n"
        )
        result = _rewrite(source, "https://mirrors.aliyun.com/ubuntu/")
        self.assertEqual(result.count("https://mirrors.aliyun.com/ubuntu/"), 2)
        self.assertIn("https://download.docker.com/linux/ubuntu", result)
        self.assertFalse(_contains_official_source(result))

    def test_rewrites_deb822_uris_without_touching_third_party_uri(self) -> None:
        source = (
            "Types: deb\n"
            "URIs: http://ports.ubuntu.com/ubuntu-ports/ https://example.invalid/repo\n"
            "Suites: resolute resolute-updates\n"
        )
        result = _rewrite(source, "https://mirrors.aliyun.com/ubuntu-ports/")
        self.assertIn("https://mirrors.aliyun.com/ubuntu-ports/", result)
        self.assertIn("https://example.invalid/repo", result)
        self.assertFalse(_contains_official_source(result))

    def test_active_source_detection_ignores_commented_official_urls(self) -> None:
        source = (
            "# deb https://archive.ubuntu.com/ubuntu/ resolute main\n"
            "deb https://mirrors.aliyun.com/ubuntu/ resolute main\n"
        )
        self.assertEqual(_active_uris(source), ("https://mirrors.aliyun.com/ubuntu/",))
        self.assertFalse(_contains_official_source(source))


if __name__ == "__main__":
    unittest.main()
