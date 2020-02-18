# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''qpath模块单元测试
'''

import unittest

from qt4c.qpath import QPath

class TestQPath(unittest.TestCase):
    '''QPath类测试用例
    '''
    
    def test_id(self):
        self.assertEqual(QPath('/Id="webview"')._parsed_qpath, [{'Id': ['=', 'webview']}])
    
    def test_type(self):
        self.assertEqual(QPath('/Type="WebView"')._parsed_qpath, [{'Type': ['=', 'WebView']}])
    
    def test_text(self):
        self.assertEqual(QPath('/Text="标题"')._parsed_qpath, [{'Text': ['=', '标题']}])
    
    def test_desc(self):
        self.assertEqual(QPath('/ControlId="0x64"')._parsed_qpath, [{'ControlId': ['=', '0x64']}])
        
    def test_instance(self):
        self.assertEqual(QPath('/Text="标题" /Instance="1"')._parsed_qpath, [{'Text': ['=', '标题']}, {'Instance': ['=', "1"]}])
    
    def test_maxdepth(self):
        self.assertEqual(QPath('/UIType="UIA" /Text="消息" && MaxDepth="3"')._parsed_qpath, [{'UIType': ['=', 'UIA']}, {'MaxDepth': ['=', '3'], 'Text': ['=', '消息']}])
        
if __name__ == '__main__':
    unittest.main()
