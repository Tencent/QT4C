# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QTA available.
# Copyright (C) 2016THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the BSD 3-Clause License (the "License"); you may not use this 
# file except in compliance with the License. You may obtain a copy of the License at
# 
# https://opensource.org/licenses/BSD-3-Clause
# 
# Unless required by applicable law or agreed to in writing, software distributed 
# under the License is distributed on an "AS IS" basis, WITHOUT WARRANTIES OR CONDITIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
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