# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''
Web自动化公共接口
'''
import win32api
import win32con

try:
    from qt4w import XPath
    from qt4w.webcontrols import WebElement,FrameElement
    from browser import EnumBrowserType as BrowserEnum
    from qt4w.webcontrols import WebPage as BaseWebPage
    
    class WebPage(BaseWebPage):
        '''封装PC端自动化所需的页面相关的逻辑
        '''
        def __init__(self, webview):
            '''构造函数
            
            :type webview: webview
            :param webview: 包含webdriver的webview对象
            '''
            self.page = webview
            super(WebPage, self).__init__(webview)
            
        def close(self):
            win32api.PostMessage(self.page._window.HWnd,win32con.WM_CLOSE,0,0)
            
        def activate(self):
            self.page.activate()
except:
    raise RuntimeError('QT4W Not Found')
