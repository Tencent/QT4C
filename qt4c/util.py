# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''
其他共用类模块
'''

from __future__ import division
import time
import win32con
import ctypes
import types
import win32api
import win32gui
import win32event
import win32process
import win32service
import winerror
import pywintypes
import six
from PIL import ImageGrab
from win32con import DESKTOP_SWITCHDESKTOP
 
from testbase.util import Timeout
from qt4c.exceptions import TimeoutError
from qt4c.keyboard import Keyboard
from qt4c import wintypes

if six.PY3:
    unicode = str


_DEFAULT_BUFFER_SIZE = 255

SIZEOF = lambda datatype: ctypes.sizeof(datatype)

class Point(object):
    """坐标点类
    """
    def __init__(self, x_y):
        self._pt = (x_y[0], x_y[1])
        
    @property
    def X(self):
        return self._pt[0]
    
    @property
    def Y(self):
        return self._pt[1]
    
    def __eq__(self, pt):
        if self._pt == pt._pt:
            return True
        else:
            return False
        
    @property
    def All(self):
        return self._pt
    
    
class Rectangle(object):
    """矩形区域类
    """
    def __init__(self, left_top_right_bottom):
        self._rect = (left_top_right_bottom[0], left_top_right_bottom[1], left_top_right_bottom[2], left_top_right_bottom[3])
#        if isinstance(self._rect, )
    
    def __str__(self):
        return str(self._rect)
    
    @property
    def All(self):
        return self._rect
    
    @property
    def Bottom(self):
        return self._rect[3]
        
    @property
    def Center(self):
        return Point(((self._rect[0] + self._rect[2]) // 2, (self._rect[1] + self._rect[3]) // 2))
    
    @property
    def Left(self):
        return self._rect[0]
    
    @property
    def Right(self):
        return self._rect[2]
    
    @property
    def Top(self):
        return self._rect[1]
    
    @property
    def Width(self):
        return self.Right - self.Left
    
    @property
    def Height(self):
        return self.Bottom - self.Top
    
    def isInRect(self, rc):
        """判断此区域是否在参数rc的范围内
        
        :type rc: Rectangle
        :param rc: 包含的区域   
        """
        if rc is None or not isinstance(rc, Rectangle):
            raise TypeError("rc应为Rectangle类型，实际为%s" % type(rc))#UtilError("参数类型错误!")
            
        if self.Left >= rc.Left and\
           self.Top >= rc.Top and\
           self.Right <= rc.Right and\
           self.Bottom <= rc.Bottom:
            return True
        else:
            return False
    
    def highLight(self):
        """高亮此区域
        """
        hwnd = win32gui.GetDesktopWindow()
        hDesktopDC = win32gui.GetWindowDC(hwnd)
        oldRop2 = ctypes.windll.gdi32.SetROP2(hDesktopDC, win32con.R2_NOTXORPEN)
        newPen = win32gui.CreatePen(win32con.PS_SOLID, 3, 0)
        oldPen = win32gui.SelectObject(hDesktopDC, newPen)
        #在指示窗口周围显示闪烁矩形
        for i in range(2):
            win32gui.Rectangle(hDesktopDC, self._rect[0], self._rect[1], self._rect[2], self._rect[3])
            time.sleep(0.2)
            win32gui.Rectangle(hDesktopDC, self._rect[0], self._rect[1], self._rect[2], self._rect[3])
            time.sleep(0.3)
        ctypes.windll.gdi32.SetROP2(hDesktopDC, oldRop2)
        win32gui.SelectObject(hDesktopDC, oldPen)
        win32gui.DeleteObject(newPen)
        win32gui.ReleaseDC(hwnd,hDesktopDC)
        
    def __eq__(self, rc):
        if isinstance(rc, Rectangle) and self._rect == rc._rect:
            return True
        else:
            return False
    
    def __ne__(self, rc):
        return not self.__eq__(rc)
        
class ProcessMem(object):
    '''跨进程数据读写
    '''
    def __init__(self, processId, buffer_size=None, remote_buffer=None):
        '''构造函数。如果remote_buffer不为None，直接使用此远程进程的内存块，否则在远程进程中创建一个字节数为buffer_size的内存块。 
        '''
        self._hProcess = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, processId).Detach()
        if self._hProcess is None:
            raise RuntimeError("Fail to open process %d" % processId)
        self._release_mem = False
        if remote_buffer is not None:
            self._buffer = remote_buffer
        elif buffer_size is not None:
            self._release_mem = True
            self._buffer = ctypes.windll.kernel32.VirtualAllocEx(self._hProcess, None, buffer_size, win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
            if self._buffer is None:
                raise RuntimeError("Fail to alloc remote memory.")
        else:
            raise ValueError("buffer_size 和 remote_buffer不能同时为空")
    
    def __del__(self):
        if self._release_mem and self._buffer:
            ctypes.windll.kernel32.VirtualFreeEx(self._hProcess, self._buffer, None, win32con.MEM_RELEASE)
            
        if self._hProcess:
            win32api.CloseHandle(self._hProcess)
    
    @property
    def Buffer(self):
        """返回远程进程中内存buffer地址
        """
        return self._buffer
    
    def write(self, local_buffer, buffer_size):
        """将local_buffer中的数据写入远程内存中。
        
        :type local_buffer: buffer
        :param local_buffer: A pointer to the buffer that contains data to be written in the address space of the specified process
        :type buffer_size: unsigned long
        :param buffer_size: The number of bytes to be written to the specified process 
        """
        rst = ctypes.windll.kernel32.WriteProcessMemory(self._hProcess, self._buffer, local_buffer, buffer_size, None)
        if rst == 0:
            raise RuntimeError("Fail to write to remote process memory")

    def read(self, local_buffer, buffer_size):
        """将远程数据读到本地buffer
        
        :type local_buffer: buffer
        :param local_buffer: A pointer to a buffer that receives the contents from the address space of the specified process
        :type buffer_size: unsigned long
        :param buffer_size: The number of bytes to be read from the specified process 
        """
        rst = ctypes.windll.kernel32.ReadProcessMemory(self._hProcess, self._buffer, local_buffer, buffer_size, None)
        if rst == 0:
            raise RuntimeError('Fail to read from remote process memory')
    
#===============================================================================
# 字符串编码相关
#===============================================================================
def getEncoding(s):
    '''获取字符串的编码
    
    :rtype: string
    :return: 'GBK','UNICODE','UTF-8','UNKNOWN'
    '''
    if not isinstance(s, six.string_types):
        return 'UNKNOWN'
    
    if isinstance(s, six.text_type):
        return 'UNICODE'
    
    try:
        unicode(s, 'UTF-8').encode('GBK')
        return 'UTF-8'
    except:
        pass
    
    try:
        unicode(s, 'GBK').encode('UTF-8')
        return 'GBK'
    except:
        pass
        
    try:
        unicode(s, 'UTF-8')
        return 'UTF-8'
    except:
        pass
        
    return 'UNKNOWN'

def myEncode(s, ec='unicode', sc=None):
    '''将字符串转换为指定的编码的字符串
    
    :type s: string
    :param s: 待转换的字符串
    :type ec: string
    :param ec: 待转换的编码. ['GBK','UNICODE','UTF-8']
    :type sc: string
    :param sc: 待转换的字符串的编码
    :attention: sc默认值为None，此时函数会自动判断s的编码（有一定概率会判断错误）
    :return: 转换后的字符串
    '''
    if not isinstance(s, six.string_types):
        return s
    if not sc:
        sc = getEncoding(s)
    else:
        sc = sc.upper()
    ec = ec.upper()
    if sc == 'UTF8':
        sc = 'UTF-8'
    if ec == 'UTF8':
        ec = 'UTF-8'
    validec = ['GBK','UNICODE','UTF-8']
    
    if (ec not in validec) or (sc not in validec) or (sc==ec):
        return s
    
    if ec == 'UNICODE':
        return unicode(s, sc)
    elif ec == 'GBK':
        if sc == 'UTF-8':
            return unicode(s, 'UTF-8').encode('GBK')
        else:
            return s.encode('GBK')
    elif ec == 'UTF-8':
        if sc == 'GBK':
            return unicode(s, 'GBK').encode('UTF-8')
        else:
            return s.encode('UTF-8')
    return s

#===============================================================================
# 获取系统Tips
#===============================================================================
def getToolTips(className='tooltips_class32', retry=10):
    """ 获取系统的浮动tips
    
    :type className: 字符串
    :param className: 类名，默认值为"tooltips_class32"
    :type retry: 整数
    :param retry: 尝试次数，每个0.5秒尝试一次
    """
    from qt4c import qpath
    while retry > 0:
        ctrls = qpath.QPath("/Visible='True'").search()
        for ctrl in ctrls:
            if not ctrl.Valid:
                continue
            if ctrl.ClassName == className:
                tips = ctrl.Caption
                if tips:
                    return tips
        retry = retry - 1
        time.sleep(0.5)
    return ''
            
class MsgSyncer(object):
    '''Thread Post Message 同步
    '''
    pid_event_map = {}
    def __init__(self, hwnd):
        '''Constructor
        
        :param hwnd: 需要同步消息的窗口
        '''
        import qt4c.wincontrols as win
        import qt4c.qpath as qpath
        
        self._syncwnd = 0
        self._eventobj = 0
                
        wndobj = win.Control(root=hwnd)
        try:
            self._pid = wndobj.ProcessId
        except win32gui.error as e:
            if e.winerror == winerror.ERROR_INVALID_WINDOW_HANDLE: #invalid hwnd
                return
            else:
                raise e
        if self._pid == 0: #窗口消失，获取pid为0
            return
        
        if self._pid in MsgSyncer.pid_event_map:
            self._syncwnd, self._eventobj = MsgSyncer.pid_event_map[self._pid]
        else:
            qp = qpath.QPath("/classname='AssistWnd' && processid='%d'" % self._pid)
            wnds = qp.search(None)
            if len(wnds) >1 :
                raise RuntimeError("在一个进程中发现两个SyncWnd")
            elif len(wnds) == 1:
                self._syncwnd = wnds[0].HWnd
                self._eventobj = win32event.CreateEvent(None, True, False, "Event_Sync_%d" % self._pid)
                MsgSyncer.pid_event_map[self._pid] = (self._syncwnd, self._eventobj)
            else:
                import testbase.logger as logger
                logger.debug("Cannot find AssistWnd(%s)" % qp)
    
    def wait(self, timeout=60):
        '''等待消息同步
        '''
        if self._syncwnd == 0:
            return
        win32event.ResetEvent(self._eventobj)
        
        try:
            win32gui.PostMessage(self._syncwnd, win32con.WM_TIMER, 0, 0)
        except pywintypes.error as e:
            if e.winerror == winerror.ERROR_INVALID_WINDOW_HANDLE:
                return
            raise e
        
        start_time = time.time()
        end_time = start_time
        while end_time - start_time <= timeout:
            if win32gui.IsWindow(self._syncwnd):
                ret = win32event.WaitForSingleObject(self._eventobj, 500)
                if ret == win32con.WAIT_OBJECT_0:
                    break
                else:
                    end_time = time.time()
            else:
                win32api.CloseHandle(self._eventobj)
                del MsgSyncer.pid_event_map[self._pid]
                break
        if end_time - start_time > timeout:
            raise RuntimeError('消息同步超时(%d秒)'%timeout)
            
def remote_inject_dll(process_id, dll_path):
    '''在process_id进程中远程注入dll_path的DLL
    '''
    import locale
    os_encoding = locale.getdefaultlocale(None)[1]
    dll_path = dll_path.decode('utf-8').encode(os_encoding)
    
    nbytes = len(dll_path)
    dllpath = str(dll_path)
    hproc = ctypes.windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, process_id)
    dllname = ctypes.windll.kernel32.VirtualAllocEx(hproc, None, nbytes, 
                            win32con.MEM_RESERVE|win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
    ctypes.windll.kernel32.WriteProcessMemory(hproc, dllname, dllpath, len(dllpath), None)
    hknl = ctypes.windll.kernel32.GetModuleHandleA("kernel32.dll")
    ldlib_addr = ctypes.windll.kernel32.GetProcAddress(hknl , "LoadLibraryA")
    ctypes.windll.kernel32.CreateRemoteThread(hproc, None, None, 
                ldlib_addr, dllname, None, None)
    ctypes.windll.kernel32.VirtualFreeEx(hproc, dllname, nbytes, win32con.MEM_RELEASE)
    ctypes.windll.kernel32.CloseHandle(hknl)
    ctypes.windll.kernel32.CloseHandle(hproc)

class Process(object):
    '''
    提供系统进程的操作类
    使用例子：
    for proc in Process.GetProcessesByName('iexplore.exe'):
        print proc.ProcessId
    '''
    
    def __init__(self, pid):
        '''构造函数
        
        :param pid: 进程ID 
        '''
        self._pid = pid
        
    @staticmethod
    def GetProcessesByName(process_name):
        '''返回进程名为process_name的Process类实例列表
        '''
        if six.PY3:
            process_name = process_name.encode('utf8')
        processes = []
        
        TH32CS_SNAPPROCESS = 0x00000002
        pe = wintypes.PROCESSENTRY32() 
        hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe.dwSize = ctypes.sizeof(wintypes.PROCESSENTRY32)
        if not ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            win32api.CloseHandle(hSnapshot)
            return processes
        
        while 1:
            if pe.szExeFile.upper() == process_name.upper():
                processes.append(Process(pe.th32ProcessID))
            
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
            
        win32api.CloseHandle(hSnapshot)
        return processes
    
    @property
    def ProcessName(self):
        # 64位python下有问题
        '''返回进程名字。失败返回None
        '''
        TH32CS_SNAPPROCESS = 0x00000002
        pe = wintypes.PROCESSENTRY32() 
        hSnapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe.dwSize = ctypes.sizeof(wintypes.PROCESSENTRY32)
        if not ctypes.windll.kernel32.Process32First(hSnapshot, ctypes.byref(pe)):
            win32api.CloseHandle(hSnapshot)
            return None
        
        while 1:
            if pe.th32ProcessID == self._pid:
                win32api.CloseHandle(hSnapshot)
                if six.PY3:
                    return pe.szExeFile.decode('utf-8')
                return pe.szExeFile
            
            if not ctypes.windll.kernel32.Process32Next(hSnapshot, ctypes.byref(pe)):
                break
            
        win32api.CloseHandle(hSnapshot)
        return None
    
    @property
    def Live(self):
        return (win32process.GetProcessVersion(self._pid) > 0)
    
    @property
    def ProcessId(self):
        return self._pid
    
    def waitForQuit(self, timeout=10, interval=0.5):
        """在指定的时间内等待退出
        
        :return: 如果在指定的时间内退出，返回True；否则返回False
        """
        if not self.Live:
            return True
        
        try: 
            Timeout(timeout, interval).waitObjectProperty(self, "Live", False)
        except TimeoutError:
            return False
        return True
    
    def _adjustProcessPrivileges(self):
        """提升权限
        """
        import win32security
        hCurPro = win32process.GetCurrentProcess()
        hToken = win32security.OpenProcessToken(hCurPro, win32security.TOKEN_ADJUST_PRIVILEGES | win32security.TOKEN_QUERY)
        luid = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        if luid:
            newState = [(luid, win32security.SE_PRIVILEGE_ENABLED),]
            win32security.AdjustTokenPrivileges(hToken, 0, newState)
        win32api.CloseHandle(hToken)
    
    def terminate(self):
        """终止进程
        """
        from qt4c.wincontrols import TrayNotifyBar

        self._adjustProcessPrivileges()
        try:
            hProcess = win32api.OpenProcess(win32con.PROCESS_TERMINATE, False, self._pid).Detach()
            win32process.TerminateProcess(hProcess, 0)
            win32api.CloseHandle(hProcess)
            tb = TrayNotifyBar()
            item = tb[self._pid]
            if item:
                item.destroy()
        except:
            pass
    
    @property
    def ProcessPath(self):
        """获取进程可执行文件的全路径
        """
        self._adjustProcessPrivileges()
        try:
            hproc=win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS,False,self._pid)
            exe_path=win32process.GetModuleFileNameEx(hproc,0)
            return exe_path
        except WindowsError:
            return "(failed to get)"
        
def is_system_locked():
    '''检测系统是否处于锁屏界面
    
    @return: bool 如果处于锁屏，返回True
    '''

    try:
        UserDll=ctypes.WinDLL("User32.dll")
        hDesk=UserDll.OpenDesktopW(u"Default", 0, False, DESKTOP_SWITCHDESKTOP)
#         PyhDesk=win32service.OpenDesktop("Default",0,FALSE,DESKTOP_SWITCHDESKTOP)
        bUnlocked = UserDll.SwitchDesktop(hDesk)
        UserDll.CloseDesktop(hDesk)
    except win32service.error as e:
        print(str(e))
        bUnlocked=False
    
    return (not bUnlocked)

class MetisView(object):
    '''各端实现的MetisView
    '''
    def __init__(self, control):
        self._control = control

    @property
    def rect(self):
        '''元素相对坐标(x, y, w, h)
        '''
        x = 0
        y = 0
        w = abs(self._control.BoundingRect.Right - self._control.BoundingRect.Left)
        h = abs(self._control.BoundingRect.Top - self._control.BoundingRect.Bottom)
        return x, y, w, h

    @property
    def os_type(self):
        '''系统类型，例如"android"，"ios"，"pc"
        '''
        return 'pc'

    def screenshot(self):
        '''当前容器的区域截图
        '''
        
        bbox =(self._control.BoundingRect.Left,self._control.BoundingRect.Top,
               self._control.BoundingRect.Right,self._control.BoundingRect.Bottom)
        im = ImageGrab.grab(bbox)
        return im

    def click(self, offset_x=None, offset_y=None):
        '''点击
        
        :param offset_x: 相对于该控件的坐标offset_x，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_x: float|None
        :param offset_y: 相对于该控件的坐标offset_y，百分比( 0 -> 1 )，不传入则默认该控件的中央
        :type offset_y: float|None
        '''
        if offset_x != None:
            offset_x = int(offset_x*abs(self._control.BoundingRect.Right - self._control.BoundingRect.Left))
        if offset_y != None:
            offset_y = int(offset_y*abs(self._control.BoundingRect.Top - self._control.BoundingRect.Bottom))
        self._control.click(xOffset=offset_x, yOffset=offset_y)

    def send_keys(self, text):
        Keyboard.inputKeys(text)
        

    def double_click(self, offset_x=None, offset_y=None):
        pass

    def long_click(self, offset_x=None, offset_y=None):
        pass

def getDpi(hwnd=None):
    if not hwnd:
        hwnd = win32gui.GetDesktopWindow()
    ratio = 1.0
    try:
        # win10 1607版本以上
        dpi = ctypes.windll.user32.GetDpiForWindow(hwnd)
        ratio = dpi / 96.0
    except:
        pass
    return ratio

if __name__ == '__main__':
    pass
