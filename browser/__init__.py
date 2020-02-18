# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''浏览器类库
'''

class EnumBrowserType(object):
    IE="iexplorer"
    TT="ttraverler"
    FireFox="firefox"
    Chrome="chrome"
    QQBrowser="qqbrowser"

browser_list=[]
for name in dir(EnumBrowserType):
    if not name.startswith('__'):
        browser_list.append(getattr(EnumBrowserType,name))

def _get_default_browser1():
    '''获取xp下的默认浏览器
    '''
    import win32con, win32api
    hkey = win32con.HKEY_CLASSES_ROOT
    subkey = r'http\shell\open\command'
    hkey = win32api.RegOpenKey(hkey, subkey)
    brwcmd = win32api.RegQueryValue(hkey, None)
    win32api.RegCloseKey(hkey)
    for browser_type in browser_list:
        if brwcmd.lower().find(browser_type)>=0:
            return browser_type
    else:
        raise RuntimeError("未支持浏览器%s" % brwcmd)#Exception("浏览器%s还未支持" % brwchoice)

def _get_default_browser2():
    '''获取vista或以上的默认浏览器
    '''
    import win32con, win32api, pywintypes
    hkey = win32con.HKEY_CURRENT_USER
    subkey = r'Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice'
    win32api.RegOpenCurrentUser()
    brwchoice = 'IE.HTTP'
    try:
        hkey = win32api.RegOpenKey(hkey, subkey)
        brwchoice = win32api.RegQueryValueEx(hkey, 'ProgId')[0]
        win32api.RegCloseKey(hkey)
    except pywintypes.error: # subkey没有设过，因此默认是IE
        return EnumBrowserType.IE
    brwmap = {'FirefoxURL': EnumBrowserType.FireFox, 
              'IE.HTTP': EnumBrowserType.IE, 
              'TTraveler.HTTP':EnumBrowserType.TT}
    if brwchoice in brwmap.keys():
        return brwmap[brwchoice]
    else:
        raise RuntimeError("未支持浏览器%s" % brwchoice)
    
def get_default_browser():
    '''获取默认浏览器类型
    
    :rtype: EnumBrowserType
    '''
    import sys
    winver = sys.getwindowsversion()
    if winver[0]<=5 : #xp or below
        return _get_default_browser1()
    elif winver[0] >=6: # vista or above
        return _get_default_browser2()

if __name__ == '__main__':
    pass
