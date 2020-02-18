# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''app模块单元测试
'''

import unittest

from qt4c.app import App

class demoApp(App):
    '''demoApp类
    '''

    def __init__(self):
        super(demoApp, self).__init__()

    def quit(self):
        App.quit(self)

class TestApp(unittest.TestCase):
    '''App类测试用例
    '''
    def test_init(self):
        app = demoApp()
        self.assertEqual(len(App._totalapps), 1)

    def test_quit(self):
        App._totalapps = []
        app = demoApp()
        app.quit()
        self.assertEqual(len(App._totalapps), 0)

    def test_quitall(self):
        app1 = demoApp()
        app2 = demoApp()
        self.assertEqual(len(App._totalapps), 2)
        App.quitAll()
        self.assertEqual(len(App._totalapps), 0)

if __name__ == '__main__':
    unittest.main()
