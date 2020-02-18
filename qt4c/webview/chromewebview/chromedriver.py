# -*- coding: UTF-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''Chrome浏览器驱动
'''

import time
import json
import logging
import threading
import six
from testbase.util import smart_text
from six.moves import urllib

class ChromeDriverError(RuntimeError):
    '''Chrome驱动错误
    '''
    def __init__(self, code, msg):
        self._code = code
        self._msg = msg
    
    @property
    def code(self):
        return self._code
    
    @property
    def message(self):
        return self._msg
    
    def __str__(self):
        return '[%d] %s' % (self._code, self._msg)
    
class ChromeDriver(object):
    '''Chrome驱动
    '''
    inst_dict = {}  # 每个WebSocket地址只能创建一个实例
    
    def __init__(self, port):
        self._port = port
        
    def get_page_list(self):
        '''获取打开的页面列表
        '''
        result = []
        null_proxy_handler = urllib.request.ProxyHandler({})
        opener = urllib.request.build_opener(null_proxy_handler)
        urllib.request.install_opener(opener)  # 强制不使用代理
        req = urllib.request.Request(url='http://localhost:%d/json' % self._port,
                          headers={'User-Agent': 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'})
        timeout = 10
        time0 = time.time()
        while time.time() - time0 < timeout:
            try:
                ret = urllib.request.urlopen(req).read()
                break
            except urllib.error.URLError as e:
                logging.warn('get_page_list error: %s' % e)
                time.sleep(1)
        else:
            raise RuntimeError('无法访问Chrome远程调试Server')

        page_list = json.loads(ret)
        for item in page_list:
            if item['type'] == 'page':
                page = {'url': item['url'], 'title': item['title']}
                if 'webSocketDebuggerUrl' in item:
                    page['websocketurl'] = item['webSocketDebuggerUrl']
                else:
                    page['websocketurl'] = 'ws://localhost:%s/devtools/page/%s' % (self._port, item['id'])
                result.append(page)
        return result
    
    def get_debugger(self, url=None, title=None):
        '''获取Web调试器
        '''
        if url is None and title is None:
            raise ValueError('url或title参数不能同时为空')
        page_list = self.get_page_list()
        ws_addr = None
        if len(page_list) == 1: 
            ws_addr = page_list[0]['websocketurl']
        else:
            for page in page_list:
                if (url and smart_text(page['url']) == smart_text(url) ) or (title and smart_text(page['title']) == smart_text(title) ):
                    ws_addr = page['websocketurl']
                    break
            else:
                raise RuntimeError('page %s not found' % (url or title))
        if not ws_addr in self.__class__.inst_dict:
            self.__class__.inst_dict[ws_addr] = WebkitDebugger(ws_addr)
        return self.__class__.inst_dict[ws_addr]
    
class WebkitDebugger(object):
    '''Webkit调试器
    '''
    def __init__(self, ws_addr):
        import websocket
        self._ws_addr = ws_addr
#         self._ws = websocket.WebSocket()
#         self._ws.connect(self._ws_addr)
        self._ws = websocket.WebSocketApp(self._ws_addr,
                              on_open=lambda ws: self.on_open(ws),
                              on_message=lambda ws, message: self.on_message(ws, message),
                              on_error=lambda ws, error: self.on_error(ws, error),
                              on_close=lambda ws: self.on_close(ws))
        self._seq = 0
        self._connected = False
        self._context_dict = {}
        self._data_dict = {}
        t = threading.Thread(target=self.work_thread)
        t.setDaemon(True)
        t.start()
        self._wait_for_ready()
        self._init()
    
    def __del__(self):
        self._ws.close()
        
    # ================= WebSocket回调 ===========================
    def on_open(self, ws):
        '''
        '''
        self._connected = True
        
    def on_message(self, ws, message):
        '''收到消息
        '''
        logging.debug('[ChromeDriver] recv %s' % message[:200])
        result = json.loads(message)
        if 'id' in result:
            self._data_dict[result['id']] = result
        else:
            self.on_recv_notify_msg(result['method'], result['params'])
            
    def on_error(self, ws, error):
        print(error)
     
    def on_close(self, ws):
        print("### closed ###")
    
    # ===========================================================
    
    def _wait_for_ready(self, timeout=10, interval=0.1):
        '''等待WebSocket连接
        '''
        time0 = time.time()
        while time.time() - time0 < timeout:
            if self._connected: break
            time.sleep(interval)
        else:
            raise RuntimeError('Connect %s failed' % self._ws_addr)
    
    def _init(self):
        '''初始化
        '''
        self.enable_runtime()
    
    def _get_context_id(self, frame_id):
        '''获取contextId
        '''
        timeout = 5
        time0 = time.time()
        while time.time() - time0 < timeout:
            if frame_id in self._context_dict:
                time_cost = time.time() - time0
                if time_cost >= 0.1: logging.debug('[ChromeDriver] wait context id for %s cost %sS' % (frame_id, time_cost))
                return self._context_dict[frame_id]
            time.sleep(0.1)
        else:
            raise RuntimeError('Can\'t find Context Id of %s' % frame_id)
        
    def on_recv_notify_msg(self, method, params):
        '''接收到通知消息
        '''
        if method == 'Runtime.executionContextCreated':
            context = params['context']
            if 'type' in context and context['type'] == 'Extension': return
            if 'frameId' in context: frame_id = context['frameId']
            else: frame_id = context['auxData']['frameId']
            self._context_dict[frame_id] = context['id']
            logging.debug('[ChromeDriver] add context id: %s(%s %s)' % (context['id'], frame_id, context['origin']))
        elif method == 'Runtime.executionContextDestroyed':
            context_id = params['executionContextId']
            for frame in self._context_dict:
                if self._context_dict[frame] == context_id:
                    del self._context_dict[frame]
                    break
        else:
            pass
            
    def work_thread(self):
        '''工作线程
        '''
        self._ws.run_forever()
    
    def _wait_for_response(self, seq, timeout=600, interval=0.1):
        '''等待返回数据
        '''
        time0 = time.time()
        while time.time() - time0 < timeout:
            if seq in self._data_dict: 
                result = self._data_dict.pop(seq)
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    logging.warn('[ChromeDriver] response error %s' % result)
                    raise ChromeDriverError(result['error']['code'], result['error']['message'])
                
            time.sleep(interval)
        else:
            raise RuntimeError('Wait for [%s] response timeout' % seq)
        
    def send_request(self, method, **kwds):
        '''发送请求
        
        :param method: 命令字
        :type method:  string
        '''
        self._seq += 1
        req = {'id': self._seq, 'method': method}
        if kwds: req['params'] = kwds
        # print req
        data = json.dumps(req)
        self._ws.send(data)
        # logging.debug('[ChromeDriver] send %s' % data[:500])
        return self._wait_for_response(self._seq)
    
    def enable_runtime(self):
        '''
        '''
        self.send_request('Runtime.enable')
        
    def get_frame_tree(self):
        '''获取frame树
        '''
        result = self.send_request('Page.getResourceTree')
        return result['frameTree']
    
    def eval_script(self, frame_id, script):
        '''执行JavaScript
        '''
        if frame_id == None:
            frame_id = self.get_frame_tree()['frame']['id']
        context_id = self._get_context_id(frame_id)
        logging.debug('[ChromeDriver][Eval:%s] %s' % (context_id, script[:200]))
        script = script.replace('\\', r'\\')
        script = script.replace('"', r'\"')
        script = script.replace('\r', r'\r')
        script = script.replace('\n', r'\n')
        script = r'''(function(){
            try{
                var result = eval("%s");
                if(result != undefined){
                    return 'S'+result.toString();
                }else{
                    return 'Sundefined';
                }
            }catch(e){
                var retVal = 'E['+e.name + ']' + e.message;//toString()
                retVal += '\n' + e.stack;
                return retVal;
            }
        })();''' % script
        params = {'objectGroup': 'console', 'includeCommandLineAPI': True, 'doNotPauseOnExceptionsAndMuteConsole': False, 'returnByValue': False, 'generatePreview': True}
        result = self.send_request('Runtime.evaluate', contextId=context_id, expression=script, **params)
        result = result['result']['value']
        logging.debug('[ChromeDriver][Retn] %s' % result)
        return result

    def screenshot(self):
        '''通过Chrome开发者协议获取page页面截图，
        '''
        import base64
        logging.debug('[ChromeDriver][captureScreenshot]')
        params = {'format': 'png'}
        result = self.send_request('Page.bringToFront')
        result = self.send_request('Page.captureScreenshot', **params)
        image = result['data']
        image = base64.b64decode(image)
        from PIL import Image
        picture = Image.open(six.BytesIO(image))
        logging.debug('[ChromeDriver][Retn] %s' % result)
        return picture
        
if __name__ == '__main__':
    pass
