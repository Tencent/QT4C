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
TUIA测试用例基类
'''

import time
import threading
import pythoncom
from testbase.testcase import TestCase

def _screenshot(path):
    '''save screenshot
    '''
    
    import win32gui, win32con
    import qt4c.wintypes as wintypes
    import ctypes

    hdcScreen = ctypes.windll.gdi32.CreateDCA('DISPLAY', None, None, None)
    hdcCapture = ctypes.windll.gdi32.CreateCompatibleDC(hdcScreen)
    
    hwnd_dsk = win32gui.GetDesktopWindow()
    l, t, r, b = win32gui.GetWindowRect(hwnd_dsk)
    w = r - l
    h = b - t
    
    lpBits = ctypes.c_void_p(0)
    bmiCapture = wintypes.BITMAPINFO()
    bmiCapture.bmiHeader.biSize = ctypes.sizeof(wintypes.BITMAPINFO)
    bmiCapture.bmiHeader.biWidth = w
    bmiCapture.bmiHeader.biHeight = h
    bmiCapture.bmiHeader.biPlanes = 1
    bmiCapture.bmiHeader.biBitCount = 24
    bmiCapture.bmiHeader.biCompression = win32con.BI_RGB
    bmiCapture.bmiHeader.biSizeImage = 0
    bmiCapture.bmiHeader.biXPelsPerMeter = 0
    bmiCapture.bmiHeader.biYPelsPerMeter = 0 
    bmiCapture.bmiHeader.biClrUsed = 0
    bmiCapture.bmiHeader.biClrImportant = 0
    
    hbmCapture = ctypes.windll.gdi32.CreateDIBSection(None,
                                                         ctypes.byref(bmiCapture),
                                                         win32con.DIB_RGB_COLORS,
                                                         ctypes.byref(lpBits),
                                                         None,
                                                         0)

    if hbmCapture:
        CAPTUREBLT = 0x40000000
        hbmOld = ctypes.windll.gdi32.SelectObject(hdcCapture, hbmCapture)
        ctypes.windll.gdi32.BitBlt(hdcCapture,
                                   0,
                                   0,
                                   w,
                                   h,
                                   hdcScreen,
                                   0,
                                   0,
                                   win32con.SRCCOPY | CAPTUREBLT)
        flag, hcursor, (xcur, ycur) = win32gui.GetCursorInfo()
        if flag == win32con.CURSOR_SHOWING:
            iconinfo = win32gui.GetIconInfo(hcursor)
            ctypes.windll.user32.DrawIcon(hdcCapture,
                                          xcur - iconinfo[1],
                                          ycur - iconinfo[2],
                                          hcursor)
        ctypes.windll.gdi32.SelectObject(hdcCapture, hbmOld)
    
    ctypes.windll.gdi32.DeleteDC(hdcCapture)
    ctypes.windll.gdi32.DeleteDC(hdcScreen)
    
    #位图像素在位元以行为单位对齐存储，每一行的总像素大小都向上取证为4字节
    #参考http://en.wikipedia.org/wiki/BMP_file_format
    alloced_bytes = (((w * 3) % 4) and ((w * 3) + (w * 3) % 4) or w * 3) * h
    pBuf = ctypes.create_string_buffer(alloced_bytes)
    cpy_bytes = ctypes.windll.gdi32.GetBitmapBits(hbmCapture,
                                                  alloced_bytes,
                                                  ctypes.byref(pBuf))
    ctypes.windll.gdi32.DeleteObject(hbmCapture)
    
    if cpy_bytes == 0:
        raise RuntimeError("failed to call GetBitmapBits!")
    
    #保留Image模块，方便使用其保存成文件的功能
    try:
        from PIL import Image
    except ImportError: #PIL模块Import失败时尝试Import Pillow
        import Image
    
    im = Image.frombuffer('RGB', (w, h), pBuf, 'raw', 'BGR', 0, 1)
    im.save(path)
    

class ClientTestCase(TestCase):
    '''QT4C测试用例基类
    '''
    
    def initTest(self, testresult ):
        '''测试用例初始化。慎用此函数，尽量将初始化放到preTest里。
        '''
        super(ClientTestCase, self).initTest(testresult)
        self.__com_threadid = threading.current_thread().ident
        pythoncom.CoInitialize()  # @UndefinedVariable

    def cleanTest(self):
        '''测试用例反初始化
        '''
        if self.__com_threadid == threading.current_thread().ident:
            pythoncom.CoUninitialize()  # @UndefinedVariable
        #清空测试桩对象缓存（这里有个隐含bug,早前的线程创建的对象有可能会被后来线程的使用，因为有可能生成了相同的线程id）
        from qt4c._tif import TestObjectMgr
        TestObjectMgr.clearCache()
        super(ClientTestCase, self).cleanTest()
        
    def get_extra_fail_record(self):
        timestr = time.strftime('%y%m%d%H%M%S', time.localtime())
        file_path = "%s_%s.jpg" % (self.TestClassName, timestr)
        _screenshot(file_path)
        return {}, {'截图': file_path}

    init_test = initTest
    clean_test = cleanTest
