# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''ChromeBrowser的接口实现
'''

import logging, os, re, time
import shutil
import win32api
import win32com.client
import win32event
import win32gui
import six

from qt4w.browser.browser import IBrowser
from qt4c.qpath import QPath
from qt4c.webview.chromewebview import ChromeWebView
from qt4c.webview.chromewebview.chromedriver import ChromeDriver
from qt4c.wincontrols import Window


class ChromeBrowser(IBrowser):
    '''Chrome浏览器
    '''
    temp_path = os.environ['temp']
    
    def __init__(self, port=9200):
        self._port = port
        self._port_list = [port]
        self._main_wnd = None
        self._pid = 0
        self._temp_dir = os.path.join(self.__class__.temp_path, 'Chrome_%d')
    
    def _handle_title(self, title):
        '''处理标题
        '''
        return title.replace('&amp;', '&')
        
    def get_chrome_window_list(self, pid):
        '''通过pid查找对应的chrome窗口列表
        '''
        from qt4c.exceptions import ControlAmbiguousError
        qp_str = r"/ClassName='Chrome_WidgetWin_1' && ProcessId='%d' && Visible='True' %%s /ClassName='Chrome_RenderWidgetHostHWND' && Visible='True'" % pid
        try:
            win = Window(locator=QPath(qp_str % ''))
            if win.exist() and win.Valid:  # 这句话才会真正去查找控件;增加有效性判断
                return [win]
            else:
                return []
        except ControlAmbiguousError as e:
            pattern = re.compile(r'找到(\d+)个控件')
            ret = pattern.search(str(e))
            if not ret: raise
            win_num = int(ret.group(1))
            win_list = []
            for i in range(win_num):
                win = Window(locator=QPath(qp_str % ("&& Instance='%d'" % i)))
                if win.exist(): win_list.append(win)
            return win_list
        
    def open_url(self, url, page_cls=None):
        import win32process, win32con
        while is_port_occupied(self._port):  # 如果端口被占用，则查找下一个可用端口
            self._port += 1
        if not self._port in self._port_list:
            self._port_list.append(self._port)
        temp_dir = self._temp_dir % self._port
        exe_path = ChromeBrowser.get_browser_path()
        params = "--remote-debugging-port=%d --disable-session-crashed-bubble --disable-features=TranslateUI --disable-breakpad --no-first-run --new-window --disable-desktop-notifications --user-data-dir=%s" % (self._port, temp_dir)
        ext_params = os.environ.get('CHROME_EXT_PARAMS', '')
        cmd = ' '.join([i for i in [exe_path, params, ext_params, url] if i])
        logging.debug('chrome: %s' % cmd)
        _, _, pid, _ = win32process.CreateProcess(None, cmd, None, None, 0, 0, None, None, win32process.STARTUPINFO())
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, False, pid)
        win32event.WaitForInputIdle(handle, 10000)
        self._pid = pid
        logging.info('chrome进程为%d' % pid)  # 加上此句话查看chrome是否成功打开了
        timeout = 10
        time0 = time.time()
        while time.time() - time0 < timeout:
            win_list = self.get_chrome_window_list(pid)
            if len(win_list) > 0: break
            time.sleep(1)
        else:
            raise RuntimeError('find chrome browser window failed')
        assert(len(win_list) == 1)
        page_wnd = win_list[0]
        self._webview = ChromeWebView(page_wnd, url, self._pid, self._port)
        return self.get_page_cls(self._webview, page_cls)
   
    def find_by_url(self, url, page_cls=None, timeout=10):
        '''在当前打开的页面中查找指定url,返回WebPage实例，如果未找到，则抛出异常
        '''
        from qt4c.exceptions import TimeoutError
        time0 = time.time()
        while time.time() - time0 < timeout:
            try:
                webview = self.search_chrome_webview(url)
                break
            except RuntimeError as e:
                logging.warn('[ChromeBrowser] search chrome window failed: %s' % e)
                time.sleep(0.5)
        else:
            raise TimeoutError
        return self.get_page_cls(webview, page_cls)
     
    def get_page_cls(self, webview, page_cls=None):
        '''得到具体页面类
        '''
        if page_cls:
            return page_cls(webview)
        return webview
    
    @staticmethod
    def get_browser_path():
        '''获取chorme.exe的路径
        '''
        from six.moves import winreg
        sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome"
        install_dir = ''
        try:
            hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
            install_dir, _ = winreg.QueryValueEx(hkey, "InstallLocation")
            winreg.CloseKey(hkey)
        except WindowsError:
            try:
                hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key)
                install_dir, _ = winreg.QueryValueEx(hkey, "InstallLocation")
            except WindowsError:
                try:
                    sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                    hkey = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, sub_key)
                    install_dir, _ = winreg.QueryValueEx(hkey, "Path")
                except WindowsError:
                    for env_dir in os.getenv('PATH').split(';'):
                        if os.path.exists(os.path.join(env_dir, 'chrome.exe')):
                            install_dir = env_dir
                            break
                    if not install_dir:
                        app_dirs = [os.getenv('LOCALAPPDATA'), os.getenv('ProgramFiles(x86)'), os.getenv('ProgramW6432')]
                        for app_dir in app_dirs:
                            if(os.path.exists(os.path.join(app_dir, r'Google\Chrome\Application', 'chrome.exe'))):
                                install_dir = os.path.join(app_dir, r'Google\Chrome\Application')
                                break
        if not install_dir:
            raise WindowsError('未找到Chrome可执行文件路径')
        return os.path.join(install_dir, "chrome.exe")
    
    def search_chrome_webview(self, url):
        '''根据url查找chrome对应的webview类
        
        returns ChromeWebView: ChromeWebView类
        '''
        chrome_path = self.get_browser_path()
        for port in self._port_list:
            chrome_driver = ChromeDriver(port)
            title = ''
            for it in chrome_driver.get_page_list():
                if it['url'] == url or re.match(url, it['url']):
                    title = self._handle_title(it['title'])
                    url = it['url']
                    if six.PY2 and isinstance(title, six.text_type): title = title.encode('utf8')
                    break
            else: continue
            break
        else:
            raise RuntimeError('获取页面：%s 标题失败' % url)
        
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if not p.CommandLine:
                continue
            
            if p.CommandLine.startswith(chrome_path) or p.CommandLine.startswith('"%s"' % chrome_path):
                items = p.CommandLine[len(chrome_path):].split()
                if not items or items[0].startswith('--type='): continue  # 都不是Browser进程
                
                chrome_window_list = self.get_chrome_window_list(p.ProcessId)
                for chrome_window in chrome_window_list:
                    win_title = chrome_window.Parent.Text
                    if win_title.endswith(' - Google Chrome'): win_title = win_title[:-16]

                    if win_title == title:
                        try:
                            win32gui.SetForegroundWindow(chrome_window.TopLevelWindow.HWnd)
                        except Exception as e:
                            print(e)
                            logging.warn('win32gui.SetForegroundWindow error')
                        self._webview = ChromeWebView(chrome_window, url, p.ProcessId)
                        return self._webview
                raise RuntimeError('当前标签页不在窗口最前端！')
        else:
            raise RuntimeError('%s对应的chrome进程不存在' % url)


    def clear_cache(self):
        for p in self._port_list:
            temp_dir = self._temp_dir % p
            if os.path.isdir(temp_dir):
                logging.info('clear dir %s' % temp_dir)
                try:
                    shutil.rmtree(temp_dir)
                except:
                    logging.error('clear dir %s failed' % temp_dir)

    def close(self):
        chrome_path = self.get_browser_path()
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if not p.CommandLine:
                continue
            
            if p.CommandLine.startswith(chrome_path) or p.CommandLine.startswith('"%s"' % chrome_path):
                items = p.CommandLine[len(chrome_path):].split()
                if not items or items[0].startswith('--type='): continue  # 都不是Browser进程
                for item in items:
                    if item.find('=') != -1:
                        [commandType, commandValue] = item.split('=', 1)
                        if(commandType == '--remote-debugging-port' and int(commandValue) in self._port_list):
                            try:
                                p.Terminate
                                time.sleep(0.5) # 等待进程完全退出
                                self.clear_cache()
                                break
                            except Exception as e:
                                logging.error('kill process failed, error: %s' % e)
    
    @staticmethod
    def killall():
        '''杀掉所有chrome进程
        '''
        wmi = win32com.client.GetObject('winmgmts:')
        for p in wmi.InstancesOf('win32_process'):
            if p.Name == 'chrome.exe':
                try:
                    p.Terminate
                except:
                    pass

        for it in os.listdir(ChromeBrowser.temp_path):
            p = os.path.join(ChromeBrowser.temp_path, it)
            if os.path.isdir(p) and it.startswith('Chrome_'):
                logging.info('clear dir %s' % p)
                try:
                    shutil.rmtree(p)
                except:
                    logging.error('clear dir %s failed' % p)
        
    @property
    def Url(self):
        return self._webview.eval_script(None, 'location.href')
 
def is_port_occupied(port):
    '''
    端口是否被占用
    '''
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('localhost', port))
        sock.close()
        return False
    except:
        return True
    
def get_next_avail_port(port):
    cur_port = port
    while is_port_occupied(cur_port):
        cur_port += 1
    return cur_port
    
if __name__ == '__main__':
    pass
    