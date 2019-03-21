# -*- coding: utf-8 -*-
"""test for browsers
"""

import unittest

from browser.chrome import ChromeBrowser


class ChromeTest(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        ChromeBrowser.killall()

    def test_chrome(self):
        chrome = ChromeBrowser()
        chrome.open_url("http://www.qq.com")


if __name__ == "__main__":
    unittest.main()