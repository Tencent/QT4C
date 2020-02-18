# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.
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
IE模块
'''

import logging
import os
import re
import subprocess
import time

import win32api
import win32com.client
import win32con
import win32event
import win32gui
import win32process

import qt4c.wincontrols as win32
from qt4c.app import App
from qt4c.qpath import QPath
from qt4c.util import Timeout
from qt4c.webview.iewebview import IEWebView
from qt4w.browser import IBrowser


class IEWindow(win32.Window):
    '''IE窗口 qt4w使用
    '''
    _timeout = Timeout(120, 1)

    def __init__(self, process_id):
        '''初始化，进程id

        :params process_id: 窗口进程id
        :type process_id: int
        '''
        self._pid = process_id
        qpstr = "|classname='IEFrame' && visible='True'|classname='WorkerW' && visible='True'\
        |classname='ReBarWindow32' |classname='Address Band Root' && Instance='0' |maxdepth='3' && classname='Edit' && ProcessId='%d'" % process_id
        old_timeout = win32.Control._timeout
        win32.Control._timeout = self._timeout
        addr_edit = win32.Control(locator=QPath(qpstr))
        win32gui.BringWindowToTop(addr_edit.TopLevelWindow.HWnd)  # 激活ie窗口，并显示在最前端
        win32.Control._timeout = old_timeout
        win32.Window.__init__(self, root=addr_edit.TopLevelWindow)
        # 实现窗口最大化的逻辑
        time.sleep(0.005)  # 优化最大化的视觉效果
#             win32gui.ShowWindow(addr_edit.TopLevelWindow.HWnd, win32con.SW_MAXIMIZE)

    @property
    def pid(self):
        return self._pid

    @property
    def ie_window(self):
        '''获取Internet Explorer_Server对应的ie窗口
        '''
        iever = IEBrowser.get_version()
        iever = int(iever.split('.')[0])
        if iever < 6:
            raise RuntimeError("不支持IE%s" % iever)
        elif iever == 6:  # ie6
            qp = QPath("/classname='Shell DocObject View' && visible='True'/classname='Internet Explorer_Server'")
        elif iever == 7:
            qp = QPath("/classname='TabWindowClass' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")
        else:
            qp = QPath("/classname='Frame Tab' && visible='True'/maxdepth='3' && classname='Internet Explorer_Server'")

        ie_window = win32.Control(root=self, locator=qp)
        ie_window._timeout = self._timeout
        ie_window.HWnd
        return ie_window

    @property
    def webview(self):
        '''返回WebView

        :rtype: IEWebView
        :return: IEWebView，用于实例化对应的WebPage
        '''
        return IEWebView(self.ie_window)

    @property
    def Url(self):
        '''返回当前的URL地址
        '''
        qpstr = "/classname='WorkerW' && visible='True' /classname='ReBarWindow32' \
        /classname~='(Address|ComboBox)' && Instance='0' /maxdepth='3' && classname='Edit'"

        addr_edit = win32.Control(root=self, locator=QPath(qpstr))
        return addr_edit.Caption

class IEBrowser(IBrowser):
    '''IE浏览器
    '''

    def __init__(self):
        self._pid_list = []

    @staticmethod
    def get_version():
        """获取注册表中的IE版本
        """
        hkey = win32con.HKEY_LOCAL_MACHINE
        subkey = r'SOFTWARE\Microsoft\Internet Explorer'
        hkey = win32api.RegOpenKey(hkey, subkey)
        ver = win32api.RegQueryValueEx(hkey, 'Version')[0]
        win32api.RegCloseKey(hkey)
        return ver

    @staticmethod
    def get_path():
        '''获取注册表中IE安装位置
        '''
        hkey = win32con.HKEY_LOCAL_MACHINE
        subkey = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\IEXPLORE.EXE'
        hkey = win32api.RegOpenKey(hkey, subkey)
        return win32api.RegEnumValue(hkey, 0)[1]

    @staticmethod
    def searh_ie_window(url):
        '''查找ie进程查找到就退出，现在无法解决url对应的标签不在IE最前面的问题
        '''
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            # 找到第一个就退出
            if p.CommandLine and p.CommandLine.find('SCODEF') == -1 and not p.CommandLine.lower().find('iexplore.exe') == -1:
                ie_winow = IEWindow(p.ProcessId)
                # IE url中可能存在“/#/”这样的无用字段，固用“/”代替
                ie_url = ie_winow.Url.replace('%3A', ':').replace('%2F', '/').replace('%23', '#').replace('/#/', '/')
                if url == ie_url or re.match(url, ie_url):
                    return ie_winow
        else:
            raise RuntimeError('%s对应的ie窗口不存在' % url)

    @staticmethod
    def killall():
        '''kill掉所有IE进程
        '''
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if p.Name == 'iexplore.exe':
                try:
                    p.Terminate
                except:
                    pass

    def close(self):
        '''kill掉所有IE进程
        '''
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if p.ProcessId in self._pid_list:
                try:
                    p.Terminate
                except Exception as e:
                    logging.error('kill process failed, error: %s' % e)

    def open_url(self, url, page_cls=None):
        '''打开一个url，返回对应的webpage实例类

        :params url: url
        :type url: str
        :params page_cls: page实例类
        :type page_cls: class
        '''
        ie_path = IEBrowser.get_path()
        # -e可以实现以新进程的方式打开ie
        pid = win32process.CreateProcess(None, '%s -e %s ' % (ie_path, url), None, None, 0, win32con.CREATE_NEW_CONSOLE, None, None, win32process.STARTUPINFO())[2]
        if not pid in self._pid_list:
            self._pid_list.append(pid)
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        win32event.WaitForInputIdle(handle, 10000)
        return self._get_page_cls(pid, page_cls)

    def find_by_url(self, url, page_cls=None, timeout=10):
        '''通过url查找页面，支持正则匹配
        '''
        from qt4c.exceptions import TimeoutError
        time0 = time.time()
        while time.time() - time0 < timeout:
            try:
                ie_window = IEBrowser.searh_ie_window(url)
                if not ie_window.pid in self._pid_list:
                    self._pid_list.append(ie_window.pid)
                break
            except RuntimeError as e:
                logging.debug('[IEBrowser] search ie window failed: %s' % e)
                time.sleep(0.5)
        else:
            raise TimeoutError
        return self._get_page_cls(ie_window, page_cls)

    def _get_page_cls(self, process_id_or_window, page_cls=None):
        '''获取具体的webpage实例类
        '''
        if isinstance(process_id_or_window, int):
            webview = IEWindow(process_id_or_window).webview
        else:
            webview = process_id_or_window.webview
        if page_cls:
            return page_cls(webview)
        return webview


class IEApp(object):
    '''to be deleted
    '''

    @staticmethod
    def killAll():
        IEBrowser.killall()


if __name__ == "__main__":
    pass
