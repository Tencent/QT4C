# -*- coding: UTF-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''IE驱动模块

IE中的坑：
1、为避免用户传入的js存在语法错误，使用eval方式执行；这种方式可以获得最后一句话的返回值
2、eval中使用var xxx=123;不能定义变量，需要使用window['xxx'] = 123; 改成使用window.eval可以解决，ie8还是不行
3、eval中使用function xx(){}不能定义函数，需要加上window['xx'] = xx;
'''

import time
import logging
import win32gui, win32con
import win32com.client.dynamic
import pythoncom
import pywintypes
import six

SID_SWebBrowserApp = pywintypes.IID('{0002DF05-0000-0000-C000-000000000046}')

class IEDriverError(RuntimeError):
    '''
    '''

class IEDriver(object):
    '''window['qt4w_driver_lib']
    '''

    def __init__(self, ie_server_hwnd):
        self._hwnd = ie_server_hwnd
        self._init_com_obj()
        
    def _init_com_obj(self):
        '''初始化com对象
        '''
        if hasattr(self, '_doc'): logging.debug('[IEDriver] re_init com_obj')
        # else: time.sleep(2)  # 部分IE10上发现打开页面时不sleep会导致拒绝访问错误
        msg = win32gui.RegisterWindowMessage('WM_HTML_GETOBJECT')
        for _ in range(3):
            try:
                ret, result = win32gui.SendMessageTimeout(self._hwnd, msg, 0, 0, win32con.SMTO_ABORTIFHUNG, 2000)
                ob = pythoncom.ObjectFromLresult(result, pythoncom.IID_IDispatch, 0)
                self._doc = win32com.client.dynamic.Dispatch(ob)
                self._win = self._doc.parentWindow
                self.handle_error_page(self._doc)
                break
            except pythoncom.com_error as e:
                if (e.args[0] % 0x100000000) == 0x800401F0:
                    # 尚未调用 CoInitialize。
                    pythoncom.CoInitialize()
                    return self._init_com_obj()
            except AttributeError as e:
                # 页面跳转时易发生此问题
                logging.debug(str(e))
                time.sleep(0.5)
        else:
            raise RuntimeError('初始化COM对象失败')
        
    def _retry_for_access_denied(self, func):
        '''IE中经常出现可重试解决的80070005错误
        '''
        timeout = 2
        time0 = time.time()
        err_msg = '拒绝访问'
        while time.time() - time0 < timeout:
            try:
                return func()
            except pywintypes.com_error as e:
                if (e.args[0] % 0x100000000) == 0x80020009:
                    err_msg = e.args[2][2].encode('utf8').strip()
                    logging.info('[IEDriver] retry error: %s' % err_msg)
                    if e.args[2][5] % 0x100000000 == 0x80070005:
                        # 拒绝访问,重试可以解决
                        time.sleep(0.05)
                        continue
                    elif e.args[2][5] % 0x100000000 == 0x80020101:
                        # 由于出现错误 80020101 而导致此项操作无法完成
                        # 一般是页面加载未完成
                        time.sleep(1)
                        timeout = 20
                        continue
                raise e
        else:
            raise IEDriverError(err_msg)
        
    def _check_valid(self):
        '''检查com对象的有效性
        '''
        try:
            self._doc._oleobj_.GetIDsOfNames('readyState')
            return True
        except pywintypes.com_error as e:
            if (e.args[0] % 0x100000000) == 0x80070005:
                self._init_com_obj()  # 重新初始化
                return False
            elif (e.args[0] % 0x100000000) == 0x800401F0:
                # 尚未调用 CoInitialize。
                pythoncom.CoInitialize()
                return self._check_valid()
            raise e
        
    def _get_document(self, frame):
        '''获取frame的IHTMLDocument2指针，此方法可以跨域
        '''
        try:
            return frame.document
        except pywintypes.com_error:
            iServiceProvider = frame._oleobj_.QueryInterface(pythoncom.IID_IServiceProvider)
            iWebBrowser2 = win32com.client.dynamic.Dispatch(iServiceProvider.QueryService(SID_SWebBrowserApp, pythoncom.IID_IDispatch))
            doc = iWebBrowser2.Document
            if not isinstance(doc, win32com.client.dynamic.CDispatch):
                # ie10以上无法跨域
                win = iWebBrowser2._oleobj_.Invoke(1034, 0, pythoncom.DISPATCH_PROPERTYGET, True)  # IHTMLDocument2 HRESULT parentWindow([out, retval] IHTMLWindow2** p);
                win = win32com.client.dynamic.Dispatch(win)
                doc = self._retry_for_access_denied(lambda: win.document)
            return doc

    def get_frames(self, doc):
        '''
        '''
        try:
            return doc.frames
        except pywintypes.com_error as e:
            if (e.args[0] % 0x100000000) == 0x80020009 and (e.args[2][5] % 0x100000000) == 0x80020003:
                return doc.GetElementsByTagName('iframe')
            else: raise

    def get_frame_window(self, win, frame_id, url):
        '''获取doc中id或name为frame_id，或者url匹配的frame的IHTMLWindow对象
        '''
        if not win: doc = self._doc
        else: doc = win.document
        frames = self.get_frames(doc)
        if isinstance(frame_id, six.string_types) and len(frame_id) > 0:
            try:
                frame = frames.item(frame_id)
                doc = self._get_document(frame)
                return doc.parentWindow
            except pywintypes.com_error as e:
                if (e.args[0] % 0x100000000) == 0x80020009 and (e.args[2][5] % 0x100000000) == 0x80020003:
                    # 找不到成员
                    raise RuntimeError('未找到id=%s 的frame' % frame_id)
                else: raise e
        else:
            # 使用url查找
            if url[0] == '/':
                # add domain
                parent_url = doc.url
                pos = parent_url.find('/', 8)
                url = parent_url[:pos] + url
            for i in range(frames.length):
                frame = frames.item(i)
                doc = self._get_document(frame)
                if doc.url == url: return doc.parentWindow
            else:
                raise RuntimeError('未找到url=%s 的frame' % url)

    def handle_error_page(self, doc):
        '''处理错误页面
        '''
        if doc.URL.startswith('res://ieframe.dll/invalidcert.htm'):
            # 证书错误页面
            target_url = None
            pos = doc.URL.find('#')
            if pos > 0:
                target_url = doc.URL[pos + 1:]
                
            for elem in doc.all:
                if elem.id == 'overridelink':
                    logging.info('[IEDriver] Auto click continue button, target url is %s' % target_url)
                    elem.click()
                    break
            else:
                raise RuntimeError('Find continue button failed')

            if target_url:
                time0 = time.time()
                timeout = 30
                while time.time() - time0 < timeout:
                    if not doc.URL.startswith('res://') and doc.readyState == 'complete':
                        break
                    time.sleep(0.5)
                else:
                    logging.warn('Waiting for jump to target url timeout')
                    
                    
    def eval_script(self, frame_win, script, use_eval=True):
        '''
        IE10以上异常对象才有stack属性
        '''
        # script = 'document.script_result = function(){try{%s}catch(){}}();' % script #window.script_result无法获取
        logging.debug('[IEDriver] eval script: %s' % script[:200].strip())
        if not isinstance(script, six.text_type):
            script = script.decode('utf8')  # 必须使用unicode编码

        if use_eval:
            script = script.replace('\\', r'\\')
            script = script.replace('"', r'\"')
            script = script.replace('\r', r'\r')
            script = script.replace('\n', r'\n')
            script = r'''document.script_result = (function(){
                try{
                    var result = eval("%s");
                    if(result != undefined){
                        return 'S'+result.toString();
                    }else{
                        return 'Sundefined';
                    }
                }catch(e){
                    var retVal = 'E['+e.name + ']' + e.message;//toString()
                    if(e.stack) retVal += '\n' + e.stack;
                    else{
                        var f = arguments.callee.caller;
                        while (f) {
                            retVal += f.name;
                            f = f.caller;
                        }
                    }
                    return retVal;
                }
            })();''' % script  #
        # print script[:500]
        self._check_valid()
        
        if frame_win == None:
            frame_win = self._win
            frame_doc = self._doc
        else:
            frame_doc = frame_win.document

        self._retry_for_access_denied(lambda: frame_win.execScript(script)) # 
        if not use_eval: return
        
        if not self._check_valid(): return  # 一般是页面发生跳转，此时无法获取到直接结果
        
        name_id = frame_doc._oleobj_.GetIDsOfNames('script_result')
        result = frame_doc._oleobj_.Invoke(name_id, 0, pythoncom.DISPATCH_PROPERTYGET, True)
        if result == '': raise IEDriverError('JavaScript返回为空')
        if six.PY2 and isinstance(result, unicode):
            result = result.encode('utf8')
        logging.debug('[IEDriver] result: %s' % result[:200].strip())
        return result
    
if __name__ == '__main__':
    pass 
