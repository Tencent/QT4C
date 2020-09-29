# -*- coding: UTF-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''Chrome WebView实现
'''

import time
import logging
from qt4c.webview.base import WebViewBase
from qt4c import qpath
from qt4w.webdriver.webkitwebdriver import WebkitWebDriver
from qt4c.webview.chromewebview.chromedriver import ChromeDriver


class ChromeWebView(WebViewBase):
    '''Chrome WebView实现
    '''
    
    def __init__(self, page_wnd, url, pid, port=9200):
        self._port = port
        self._url = url
        self._pid = pid
        self._window = page_wnd
        super(ChromeWebView, self).__init__(self._window, WebkitWebDriver(self))
        self._driver = ChromeDriver(self._port).get_debugger(self._url)
        self._frame_dict = {}  # 缓存frame xpath和frame id的对应关系
        self._browser_type = 'chrome'
    
    def _get_frame(self, parent, name, url):
        '''根据frame的name和url获取frameTree节点
        
        :param parent 要查找的frameTree节点
        :type parent  dict
        :param name: frame的id或name属性
        :type name:  string
        :param url:  frame的url
        :type url:   string
        '''
        if 'childFrames' in parent:
            for child in parent['childFrames']:
                if (name and child['frame']['name'] == name) or (url and child['frame']['url'] == url):
                    return child
        else:
            logging.info('[ChromeWebView] get_frame %s' % parent)
        # raise RuntimeError('find frame of %s failed' % ((('name=%s' % name) if name else ('url=%s' % url))))
        return None
    
    def _get_frame_id_by_xpath(self, frame_xpaths):
        '''根据XPath对象查找frame id
        
        :param frame_xpaths: frame的xpath数组
        :type frame_xpaths: list
        '''
        frame_xpaths_str = ''.join(frame_xpaths)
        if frame_xpaths_str in self._frame_dict: return self._frame_dict[frame_xpaths_str]
        # 缓存中不存在时
        timeout = 10
        time0 = time.time()
        while time.time() - time0 < timeout:
            frame_tree = self._driver.get_frame_tree()
            frame_id = frame_tree['frame']['id']
            if len(frame_xpaths) == 0: 
                # 顶层frame
                self._frame_dict[frame_xpaths_str] = frame_id
            else:
                frame_exist = True
                for i in range(len(frame_xpaths)):
                    try:
                        name, url = self._webdriver._get_frame_info(frame_xpaths[:i + 1])
                    except Exception as e:
                        logging.error('[ChromeWebView] _get_frame_info_error %s' % e)
                        frame_exist = False
                        break
                    frame_tree = self._get_frame(frame_tree, name, url)
                    if frame_tree == None:
                        # 未找到frame
                        frame_exist = False
                        break
                    self._frame_dict[frame_xpaths_str] = frame_tree['frame']['id']
                if not frame_exist: 
                    time.sleep(0.5)
                    continue
            return self._frame_dict[frame_xpaths_str]
    
    def eval_script(self, frame_xpaths, script):
        '''在指定frame中执行JavaScript，并返回执行结果
        
        :param frame_xpaths: frame元素的XPATH路径，如果是顶层页面，则传入“[]”或者是frame id
        :type frame_xpaths:  list or string
        :param script:       要执行的JavaScript语句
        :type script:        string
        '''
        from qt4c.webview.chromewebview.chromedriver import ChromeDriverError
        timeout = 10
        time0 = time.time()
        while time.time() - time0 < timeout:
            if isinstance(frame_xpaths, list):
                frame_id = self._get_frame_id_by_xpath(frame_xpaths)
            else:
                frame_id = frame_xpaths
            try:
                result = self._driver.eval_script(frame_id, script)
                break
            except (ChromeDriverError, RuntimeError) as e:
                if isinstance(e, RuntimeError):
                    del self._frame_dict[''.join(frame_xpaths)]
                    time.sleep(0.5)
                elif e.code == -32000:
                    # Execution context with given id not found.
                    time.sleep(0.5)
                else:
                    raise e
        else:
            raise RuntimeError('执行JavaScript代码失败')
        return self._handle_result(result, frame_xpaths)
    
    def click(self, x_offset, y_offset): 
        '''Chrome中按住shift键点击，以便在新窗口中打开页面
        '''
        from qt4c.keyboard import Key
        js_tmpl = '''(function(x, y){
    var getNodeByPos = function(tag, x, y){
        var nodes = document.getElementsByTagName(tag);
        for(var i=0;i<nodes.length;i++){
            var rect = nodes[i].getBoundingClientRect();
            if(rect.left <= x && rect.right >= x && rect.top <= y && rect.bottom >= y) return nodes[i];
        }
        return null;
    };
    
    var getTargetFrame = function(x, y){
        var frame = getNodeByPos('iframe', x, y);
        if(frame != null){
            // target node is in iframe
            var result = new Array();
            var rect = frame.getBoundingClientRect();
            var scale = qt4w_driver_lib.getScale();
            result.push(rect.left*scale);
            result.push(rect.top*scale);
            var name = frame.getAttribute('name');
            if(name != null){
                result.push('//iframe[@name="'+name+'"]');
                return result.toString();
            }
            var id = frame.getAttribute('id');
            if(id != null){
                result.push('//iframe[@id="'+id+'"]');
                return result.toString();
            }
            var src = frame.getAttribute('src');
            if(src == '' || src == 'about:blank') return '';
            result.push('//iframe[@src="' + src + '"]');
            return result.toString();
        }
        return '';
    };

    
    var isButton = function(x,y){
        var button = getNodeByPos('button',x,y)
        return (button != null)  
    };
    
    var isNewTabLinkNode = function(x, y){
        var frame_info = getTargetFrame(x, y);
        if(frame_info != '') return frame_info;
        
        var node = getNodeByPos('a', x, y);
        if(node == null) return null;
        //console.log(node.outerHTML);
        return node.getAttribute('target') == '_blank';
    };
    var scale = qt4w_driver_lib.getScale();
    return isNewTabLinkNode(x/scale, y/scale)||isButton(x/scale, y/scale);
})(%f, %f);'''
        x = x_offset
        y = y_offset
        frame_xpaths = []
        new_tab_flag = False
        while True:
            result = self.eval_script(frame_xpaths, js_tmpl % (x, y))
            if ',' in result:
                # in frame
                result = result.split(',')
                frame_xpaths.append(result[2])
                x -= float(result[0])
                y -= float(result[1])
            else:
                new_tab_flag = result == 'true'
                break
        shift_key = Key(16)  # SHIFT
        if new_tab_flag: shift_key._inputKey(False)
        super(ChromeWebView, self).click(x_offset, y_offset)
        if new_tab_flag: shift_key._inputKey(True)
        
def _get_pid_by_port(port):
    '''利用端口，获取对应端口的进程id
    '''
    
    import subprocess
    import time
    import re
    timeout = 10
    start = time.time()
    cur = start
    command = "netstat -aon | findstr %d" % port
    sub_proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while 1:
        ret = sub_proc.poll()
        if ret is None:
            time.sleep(0.2)
            cur = time.time()
            if(cur > start + timeout):
                sub_proc.kill()
                break
        elif ret == 0:
            break
        else:
            break
    content = sub_proc.stdout.read().rstrip()
#     print content
    result = re.search('LISTENING\s+(\d+)$', content)
    if result:
        content = result.group(0)
        result = re.search('\d+$', content)
        return int(result.group(0))
    else:
        raise RuntimeError("The specified port %d does not bind to a process" % port)
    
def get_pid_by_port(port):
    '''增加延时和重试机制，防止网络初始化太慢导致的查找失败
    '''
    import time
    try_count = 3
    for i in range(try_count):
        if i >= 3:
            break
        else:
            try:
                pid = _get_pid_by_port(port)
                return pid
            except RuntimeError:
                time.sleep(2)
            except Exception as err:
                raise err            
                
if __name__ == '__main__':
    pass
