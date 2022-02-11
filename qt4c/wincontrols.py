# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''
Window的控件模块
'''

from __future__ import division
import locale
import win32api
import win32gui
import win32process
import win32con
import winerror
import commctrl
import copy
import ctypes
import os
import time
import types
import six

from testbase.util import LazyInit, Timeout

from qt4c.util import ProcessMem, Rectangle
from qt4c.mouse import Mouse, MouseFlag, MouseClickType
from qt4c.exceptions import ControlAmbiguousError, ControlNotFoundError, TimeoutError
from qt4c import accessible, control, wintypes, util
from qt4c.keyboard import Keyboard

class _CWindow(object):
    '''
    Win32 Window类（bridge）
    '''
    
    #TODO：将Control类中的Windows窗口接口移到此类
    
    def __init__(self, hwnd):
        '''构造函数
        :param hwnd: 窗口句柄
        :type hwnd: integer
        '''
        self._hwnd = hwnd 
        
    @property
    def HWnd(self):
        '''窗口句柄
        '''
        return self._hwnd
    
    
class Control(control.Control):
    '''
    Win32 Window类，实现Win32窗口常用属性。
    '''

    def __init__(self, root=None, locator=None):
        '''Constructor
        
        :type root: wincontrols.Control
        :param root: 开始查询的窗口。 如果是None，表示用desktop开始查找。
        :type locator: qpath.QPath
        :param locator: 查询类的实例, 如果是None，则将root作为此窗口。
        '''
        
        control.Control.__init__(self)
        if locator is None:
            if (isinstance(root, six.integer_types) or 
                isinstance(root, Control) or 
                isinstance(root, _CWindow) or
                root is None):
                pass
            else:
                raise TypeError("root不支持该类型%s" % type(root))
        self._root = root
        self._locator = locator
        self._wndobj = LazyInit(self, '_wndobj', self._init_wndobj )
        
    def _init_wndobj(self):
        '''初始化Win32窗口对象
        '''
        if self._locator is None and self._root is None:
            wndobj =  _CWindow(int(win32gui.GetDesktopWindow()))
        elif self._locator is None:
            if isinstance(self._root, six.integer_types): #root is a hwnd
                wndobj = _CWindow(self._root)
            elif isinstance(self._root, Control):
                wndobj = _CWindow(self._root.HWnd)
            elif isinstance(self._root, _CWindow):
                wndobj = self._root
        else:
            try:
                kwargs = {'root': self._root}
                foundctrls =  self._timeout.retry(self._locator.search, kwargs, (), lambda x: len(x)>0 )
            except TimeoutError as erro:
                raise ControlNotFoundError("<%s>中的%s查找超时：%s" % (self._locator, self._locator.getErrorPath(), erro))
            nctrl = len(foundctrls)
            if (nctrl > 1):
                raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
            wndobj = _CWindow(foundctrls[0].HWnd)
        return wndobj
    
    @staticmethod
    def __enum_childwin_callback(hwnd, hwnds):
        parent = hwnds[0]
        if parent == None:
            hwnds.append(hwnd)
        else:
            hparent = ctypes.windll.user32.GetAncestor(hwnd, win32con.GA_PARENT)
            if hparent == parent:
                hwnds.append(hwnd)  
             
    def __validCtrlNum(self, ctrls):
        return (len(ctrls) > 0)
       
    def equal(self, other):
        '''判断两个对象是否相同。
        
        :type other: Control
        :param other: 本对象实例
        '''
        if not isinstance(other, Control):
            return False
        return (self.HWnd == other.HWnd)
    
    def exist(self):
        '''判断控件是否存在
        '''
        if self._locator is None and self._root is None:
            return True
        elif self._locator is None:
            if isinstance(self._root, six.integer_types): #root is a hwnd
                return True
            elif isinstance(self._root, Control):
                return self._root.exist()
            elif isinstance(self._root, _CWindow):
                return self._root.Valid
        else:
            if isinstance(self._root, Control):
                if not self._root.exist():
                    return False
            foundctrls = self._locator.search(root=self._root)
            nctrl = len(foundctrls)
            if (nctrl > 1):
                raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
            if (nctrl < 1):
                return False
            else:
                return True    
    
    def wait_for_exist(self, timeout, interval ):
        '''等待控件存在
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==True)
        
    def waitForExist(self, timeout, interval ):
        '''等待控件存在
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==True)
        
    def wait_for_invalid(self, timeout=10.0, interval=0.5 ):
        '''等待控件失效
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==False)
        
    def waitForInvalid(self, timeout=10.0, interval=0.5 ):
        '''等待控件失效
        '''
        Timeout(timeout, interval).retry(self.exist, (), (), lambda x:x==False) 
        
    @property
    def BoundingRect(self):
        """返回窗口大小
        
        :rtype: util.Rectangle
        :return: util.Rectangle实例
        """
        scale = util.getDpi()
        rect = win32gui.GetWindowRect(self.HWnd)
        rect = [it * scale for it in rect]
        return util.Rectangle(rect)
    
    @property
    def Caption(self):
        """返回窗口标题
        
        :rtype: StringType
        :return: 窗口标题
        """
        buf_size = 0
        try:
            textlength = ctypes.c_long(0)
            hr = ctypes.windll.user32.SendMessageTimeoutA(self.HWnd, win32con.WM_GETTEXTLENGTH, 0, 0, 0, 200, ctypes.byref(textlength))
            if hr == 0 or textlength.value < 0:
                return ""
            buf_size = textlength.value + 1
        except win32gui.error:
            return ""

        if buf_size <= 0:
            return ""
        # pybuffer = win32gui.PyMakeBuffer(buf_size)
        # ret = win32gui.SendMessage(self.HWnd, win32con.WM_GETTEXT, buf_size, pybuffer)

        pybuffer = ctypes.create_unicode_buffer(buf_size)
        ret = ctypes.windll.user32.SendMessageW(self.HWnd, win32con.WM_GETTEXT, buf_size, ctypes.byref(pybuffer))
        if ret:
            text = pybuffer.value
            try:
                if six.PY2:
                    text = text.encode('utf8')
                return text
            except Exception:
                return text
        else:
            return ""

    @property
    def Children(self):
        """返回子控件列表
        
        :rtype: ListType
        """
        hwnds = []
        if self.HWnd == win32gui.GetDesktopWindow():
            hwnds.append(None)
            win32gui.EnumWindows(self.__enum_childwin_callback, hwnds)
        else:
            hwnds.append(self.HWnd)
            try:
                win32gui.EnumChildWindows(self.HWnd, self.__enum_childwin_callback, hwnds)
            except win32gui.error as e:
                # if e[0]== 0 or e[0]==1400: #1400是无效窗口错误
                if e.winerror == 0 or e.winerror == winerror.ERROR_INVALID_WINDOW_HANDLE: #1400是无效窗口错误
                    pass
                else:
                    raise e
            
        del hwnds[0]
        return [Window(root=hwnd) for hwnd in hwnds]

    @property
    def ClassName(self):
        '''返回窗口类名
        '''
        text = win32gui.GetClassName(self.HWnd)
        os_encoding = locale.getdefaultlocale(None)[1]
        try:
            if six.PY2:
                text = text.decode(os_encoding)
            return text
        except UnicodeDecodeError:
            return text
    
    @property
    def ControlId(self):
        '''返回控件ID
        '''
        return win32gui.GetDlgCtrlID(self.HWnd)
    
    @property
    def Enabled(self):
        '''此控件是否可用
        '''
        bEnable = win32gui.IsWindowEnabled(self.HWnd)
        if bEnable == 1:
            return True
        else:
            return False
    
    @property
    def ExStyle(self):
        """此控件的扩展样式
        """
        return win32gui.GetWindowLong(self.HWnd, win32con.GWL_EXSTYLE)
        
    @property
    def HWnd(self):
        return self.hwnd

    @property
    def hwnd(self):
        return self._wndobj.HWnd
    
    @property        
    def Parent(self):
        """返回父窗口
        
        :rtype: Window
        :return: 获取父窗口
        :attention: 如果是desktop窗口，则返回None;如果是顶级窗口，则返回desktop窗口;否则返回父窗口 。
        """
        hwind_desktop = win32gui.GetDesktopWindow()
        if self.HWnd == hwind_desktop:
            return None

        isChild = ((self.Style & win32con.WS_CHILDWINDOW) > 0)
        if isChild:
            hwnd = win32gui.GetParent(self.HWnd)
            return Window(root=hwnd)
        else:
            return Window(root=hwind_desktop)
        
    @property
    def ProcessId(self):
        pid = win32process.GetWindowThreadProcessId(self.HWnd)[1]
        return pid
    
    @property
    def Style(self):
        """此控件的样式
        """
        return win32gui.GetWindowLong(self.HWnd, win32con.GWL_STYLE)
        
    @property
    def Text(self):
        return self.Caption
    
    @Text.setter
    def Text(self, text):
        """设置文本
        
        :type text: StringType
        :param text: 设置的文本 
        """
        os_encoding = locale.getdefaultlocale(None)[1]
        if six.PY2:
            win32gui.SendMessage(self.HWnd, win32con.WM_SETTEXT, 0, text.decode('utf8').encode(os_encoding))
        else:
            win32gui.SendMessage(self.HWnd, win32con.WM_SETTEXT, 0, text)
        
    @property
    def ThreadId(self):
        '''窗口线程ID
        '''
        tid = win32process.GetWindowThreadProcessId(self.HWnd)[0]
        return tid
    
    @property
    def TopLevelWindow(self):
        '''返回控件的最上层窗口
        
        :rtype: Window
        '''
        topwnd = self
        while (topwnd.Style & win32con.WS_CHILDWINDOW) > 0:
            topwnd = topwnd.Parent
        return Window(root=topwnd)

    @property    
    def Valid(self):
        '''窗口是否存在
        '''
        if 0 == win32gui.IsWindow(self.HWnd):
            return False
        else:
            return True
    
    @property
    def Visible(self):
        '''此控件是否可见
        '''
        if not self.Valid:
            return False
        bVisible = win32gui.IsWindowVisible(self.HWnd)
        if bVisible == 1:
            return True
        else:
            return False
        
    @property
    def AccessibleObject(self):
        """返回AccessibleObject
        
        :rtype: qt4c.accessible.AccessibleObject
        """
        return accessible.AccessibleObject(self.HWnd)
        
    @property
    def Width(self):
        """宽度
        """
        if self.BoundingRect:
            return self.BoundingRect.Right - self.BoundingRect.Left
        return 0
    
    @property
    def Height(self):
        """高度
        """
        if self.BoundingRect:
            return self.BoundingRect.Bottom - self.BoundingRect.Top
        return 0
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        '''点击控件
        
        :type mouseFlag: qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: qt4c.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移；
        '''
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.sendClick(self.HWnd, x,y, mouseFlag, clickType)
        
    def setFocus(self):
        '''将此控件设为焦点
        '''
#        self.bringForeground() #comment out because of bug 4973401
        current_id = win32api.GetCurrentThreadId()
        target_id = self.ThreadId
        win32process.AttachThreadInput(target_id,current_id,True)
        win32gui.SetFocus(self.HWnd)
        win32process.AttachThreadInput(target_id,current_id,False)

class ListViewItem(control.Control):
    """sysListView32的每一项
    """
    def __init__(self, parent, item_index):
        self._parent = parent
        self.item_index = item_index
        control.Control.__init__(self)
    
    @property
    def SubItems(self):
        pass
    
    @property
    def BoundingRect(self):
        """获取ListView的某项Item的文本
        """
        rect = wintypes.RECT()
        rcsize = ctypes.sizeof(wintypes.RECT)
        pm = util.ProcessMem(self._parent.ProcessId, buffer_size=rcsize)
        rect.left = commctrl.LVIR_SELECTBOUNDS
        pm.write(ctypes.byref(rect), rcsize)
        
        # Fill in the requested item
        retval = win32gui.SendMessage(self._parent.HWnd,
                                      commctrl.LVM_GETITEMRECT,
                                      self.item_index,
                                      pm.Buffer)
    
        # if it succeeded
        if not retval:
            raise RuntimeError("Did not succeed in getting rectangle")
        pm.read(ctypes.byref(rect), rcsize)
        parentRC = self._parent.BoundingRect
        
        return util.Rectangle((parentRC.Left+rect.left,
                               parentRC.Top+rect.top,
                               parentRC.Left+rect.right,
                               parentRC.Top+rect.bottom))
    
    @property
    def Text(self):
        """获取ListView的某项Item的文本
        """
        dwPid = win32process.GetWindowThreadProcessId(self._parent.HWnd)[1]
        hProcess = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, dwPid).Detach()
        
        if 'PROGRAMFILES(X86)' in os.environ:
            lvi = wintypes.LVITEM64()
        else:
            lvi = wintypes.LVITEM()
        pTextBuf = ctypes.c_char_p(six.b('\0') * win32con.MAX_PATH)
    
        plvi = ctypes.windll.kernel32.VirtualAllocEx(hProcess, None, ctypes.sizeof(wintypes.LVITEM), win32con.MEM_COMMIT, win32con.PAGE_READWRITE)  # @UndefinedVariable
        pBuf = ctypes.windll.kernel32.VirtualAllocEx(hProcess, None, win32con.MAX_PATH, win32con.MEM_COMMIT, win32con.PAGE_READWRITE) # @UndefinedVariable
        lvi.iSubItem = 0
        lvi.pszText = pBuf
        lvi.cchTextMax = win32con.MAX_PATH
        lvi.mask = commctrl.LVIF_TEXT
        ctypes.windll.kernel32.WriteProcessMemory(hProcess, plvi, ctypes.byref(lvi), ctypes.sizeof(wintypes.LVITEM), None) # @UndefinedVariable
        ctypes.windll.kernel32.WriteProcessMemory(hProcess, pBuf, 0, win32con.MAX_PATH, None) # @UndefinedVariable
        win32gui.SendMessage(self._parent.HWnd, commctrl.LVM_GETITEMTEXT, self.item_index, plvi)
        ctypes.windll.kernel32.ReadProcessMemory(hProcess, pBuf, pTextBuf, win32con.MAX_PATH, None) # @UndefinedVariable
        ctypes.windll.kernel32.VirtualFreeEx(hProcess, plvi, ctypes.sizeof(wintypes.LVITEM), win32con.MEM_DECOMMIT) # @UndefinedVariable
        ctypes.windll.kernel32.VirtualFreeEx(hProcess, pBuf, win32con.MAX_PATH, win32con.MEM_DECOMMIT) # @UndefinedVariable
        win32api.CloseHandle(hProcess)
        pTextBuf = pTextBuf.value.decode('gbk').encode('utf8')
        return pTextBuf
    
class ListView(Control):
    """sysLisView32 控件类型
    """
    @property
    def ItemCount(self):
        "The number of items in the ListView"
        return win32gui.SendMessage(self.HWnd,commctrl.LVM_GETITEMCOUNT)

    @property
    def Items(self):
        return self
    
    def __iter__(self):
        cnt = self.ItemCount
        for i in range(cnt):
            yield ListViewItem(self, i)  
            
    def __getitem__(self, key):
        if isinstance(key, int):
            cnt = self.ItemCount
            if key >= cnt:
                raise IndexError("key超出下标范围!")
            return ListViewItem(self, key)
        elif isinstance(key, six.string_types):
            if(isinstance(key, six.text_type)):
                key = key.encode('utf8')
            for item in self:
                if item.Text == key:
                    return item
            raise ValueError("cannot find Listview item of text %s" %key)  
        raise TypeError('参数key=%s, 不是int或string' % key)    

class TextBox(Control):
    """编辑控件
    """
    pass

class Window(Control, control.ControlContainer):
    '''
    Win32 Window类，实现Win32窗口常用属性。
    '''
    def __init__(self, root=None, locator=None):
        '''Constructor
        
        :type locator: 类实例 
        :param locator: 查询类的实例, 如果是None，则将root作为此窗口。
        :type root: Window或者window句柄 
        :param root: 开始查询的窗口。 如果是None，表示用desktop开始查找。
        '''
        Control.__init__(self, root=root, locator=locator)
        control.ControlContainer.__init__(self)  
        
    @property
    def Maximized(self):
        """该窗口是否最大化
        """
        if not self.Valid:
            raise RuntimeError("句柄无效，窗口已销毁!")
        if((self.Style & win32con.WS_MAXIMIZE) > 0):
            return True
        else:
            return False
    
    @property
    def Minimized(self):
        """该窗口是否最小化
        """
        if not self.Valid:
            raise RuntimeError("句柄无效，窗口已销毁!")
        return win32gui.IsIconic(self.HWnd)
    
    @property
    def OwnerWindow(self):
        '''此窗口的所有者窗口
        
        :rtype: Window
        :return: 获取Owner Window
        '''
        if not self.Valid:
            return None
        hwnd = win32gui.GetWindow(self.HWnd, win32con.GW_OWNER)
        if hwnd == None:
            return None
        else:
            return Window(root=hwnd)
    
    @property
    def PopupWindow(self):
        '''此窗口的弹出窗口
        
        :rtype: Window
        :return: 获取EnabledPopup
        '''
        hwnd = win32gui.GetWindow(self.HWnd, win32con.GW_ENABLEDPOPUP)
        if hwnd == 0:
            return None
        else:
            return Window(root=hwnd)
        
    @property
    def TopMost(self):
        """是否具有总在最前端
        """
        if((self.ExStyle & win32con.WS_EX_TOPMOST) > 0):
            return True
        else:
            return False
        
    def bringForeground(self):
        '''将窗口设为最前端窗口
        '''
        fwnd = win32gui.GetForegroundWindow()
        if(fwnd == self.HWnd):
            return
        if fwnd == 0:
            try:
                win32gui.SetForegroundWindow(self.HWnd)
                return
            except win32api.error:
                # 防止有菜单弹出导致异常
                Keyboard.inputKeys('{ESC}')
                win32gui.SetForegroundWindow(self.HWnd)
                return
        
        ftid, _ = win32process.GetWindowThreadProcessId(fwnd)
        wtid, _ = win32process.GetWindowThreadProcessId(self.HWnd)
                
        ctypes.windll.user32.AttachThreadInput(wtid, ftid, True)
#        if ret == 0:
#            raise Exception("AttachThreadInput(attach) with exception, error code:%s" % win32api.GetLastError())

        try:
            util.Timeout(5, 0.5).retry(  ctypes.windll.user32.SetForegroundWindow, 
                                         (self.HWnd, ), 
                                         (), 
                                         lambda x: win32gui.GetForegroundWindow() == self.HWnd)
        except TimeoutError:
            pass
        
        ctypes.windll.user32.AttachThreadInput(wtid, ftid, False)
#        if ret == 0:
#            raise Exception("AttachThreadInput(detach) with exception, error code:%s" % win32api.GetLastError())
            
    
    def _wait_for_disabled_or_invisible(self, timeout=60, interval=0.5):
        tt = util.Timeout(timeout, interval)
        tt.retry(lambda x: x, (self, ), (), lambda x: x.Enabled==False or x.Valid==False or x.Visible==False)
        
    def close(self):
        '''关闭窗口
        
        :rtype: bool
        :return: 窗口销毁返回True，否则返回False
        '''
        win32api.PostMessage(self.HWnd,win32con.WM_CLOSE,0,0)
        self._wait_for_disabled_or_invisible() #有弹出窗口时，此窗口会变为disabled
        if self.Valid == True:
            return False
        else:
            return True 
        
    
    def hide(self):
        '''隐藏
        '''
        win32gui.ShowWindow(self.HWnd, win32con.SW_HIDE)
    
    def maximize(self):
        '''最大化窗口
        '''
        win32api.PostMessage(self.HWnd,win32con.WM_SYSCOMMAND,win32con.SC_MAXIMIZE,0) 
    
    def minimize(self):
        '''最小化窗口
        '''
        win32api.SendMessage(self.HWnd,win32con.WM_SYSCOMMAND,win32con.SC_MINIMIZE,0) 
    
    def resize(self, width, height):
        '''设置窗口大小
        '''
        x, y = self.BoundingRect.Left, self.BoundingRect.Top
        win32gui.MoveWindow(self.HWnd, x, y, width, height, True)
        
    def restore(self):
        '''恢复窗口
        '''
        win32gui.ShowWindow(self.HWnd,win32con.SW_RESTORE)

    def show(self):
        '''显示窗口
        '''
        win32gui.ShowWindow(self.HWnd, win32con.SW_SHOW)
        
    def move(self, x, y):
        """移动窗口
        """
        win32gui.MoveWindow(self.HWnd, x, y, self.Width, self.Height, True)
        
    def waitForInvalid(self, timeout=10.0, interval=0.5):
        '''等待窗口失效
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        if False == self.Valid:
            return 
        self.waitForValue('Valid', False, timeout, interval, False)
        
    def waitForInvisible(self, timeout=10.0, interval=0.5):
        '''等待窗口消失
        
        :type timeout: float 
        :param timeout: 超时秒数
        '''
        if False == self.Visible:
            return 
        self.waitForValue('Visible', False, timeout, interval, False)

#class ShellTrayWnd(Control):
#    """Tray Window"""
#    class ABE(object):
#        """Windows Taskbar的停靠位置"""
#        LEFT,TOP,RIGHT,BOTTOM = range(4)
#        
#    def __init__(self):
#        import qpath
#        qp = qpath.QPath("/ClassName='Shell_TrayWnd'")
#        Control.__init__(self, locator=qp)
#        
#    @property
#    def NotifyBar(self):
#        return TrayNotifyBar()
#    
#    @property
#    def TaskBar(self):
#        return TrayTaskBar()
#    
#    @property
#    def Locked(self):
#        """任务栏是否被锁定"""
#        uEdge = self.Edge
#        if uEdge == ShellTrayWnd.ABE.BOTTOM or uEdge == ShellTrayWnd.ABE.TOP:
#            oLeft = self.TaskBar.BoundingRect.Left
#            win32gui.SendMessage(self.HWnd, win32con.WM_COMMAND, 424, 0)
#            nLeft = self.TaskBar.BoundingRect.Left
#            win32gui.SendMessage(self.HWnd, win32con.WM_COMMAND, 424, 0)
#            if nLeft > oLeft:
#                return True
#            else:
#                return False
#        else:
#            oTop = self.TaskBar.BoundingRect.Top
#            win32gui.SendMessage(self.HWnd, win32con.WM_COMMAND, 424, 0)
#            nTop = self.TaskBar.BoundingRect.Top
#            win32gui.SendMessage(self.HWnd, win32con.WM_COMMAND, 424, 0)
#            if nTop > oTop:
#                return True
#            else:
#                return False
#        
#    @Locked.setter
#    def Locked(self, lock):
#        """锁定/解锁任务栏
#        @param lock: bool
#        @param lock: 是否锁定任务栏  
#        """
#        if self.Locked != lock:
#            win32gui.SendMessage(self.HWnd, win32con.WM_COMMAND, 424, 0)
#    
#    @property
#    def Edge(self):
#        """返回Windows Taskbar的停靠位置
#        @rtype: ShellTrayWnd.ABE
#        """
#        abd = wintypes.APPBARDATA()
#        abd.cbSize = ctypes.sizeof(abd)
#        abd.hWnd = self.HWnd
#        ctypes.windll.shell32.SHAppBarMessage(5, ctypes.byref(abd))
#        return abd.uEdge
#    
#    def setPosition(self, edge):
#        """设置Windows Taskbar的停靠位置
#        @param edge: ShellTrayWnd.ABE
#        """
#        from mouse import Mouse
#        import time
#        fromX = self.TaskBar.BoundingRect.Right
#        fromY = self.TaskBar.BoundingRect.Bottom
#        
#        uEdge = self.Edge
#        if uEdge == ShellTrayWnd.ABE.LEFT:
#            fromX = fromX - 1 
#        elif uEdge == ShellTrayWnd.ABE.TOP:
#            fromY = fromY - 1
#        
#        pDevMode = win32api.EnumDisplaySettings(None, win32con.ENUM_CURRENT_SETTINGS)
#        toX = pDevMode.PelsWidth / 2
#        toY = pDevMode.PelsHeight / 2
#        if edge == ShellTrayWnd.ABE.LEFT:
#            toX = 5
#        elif edge == ShellTrayWnd.ABE.TOP:
#            toY = 5
#        elif edge == ShellTrayWnd.ABE.RIGHT:
#            toX = pDevMode.PelsWidth - 5
#        else:
#            toY = pDevMode.PelsHeight - 5
#        
#        Mouse.drag(fromX, fromY, toX, toY)
#        time.sleep(3)
    
class TrayNotifyBar(Control):
    """系统的通知区域
    """
    def __init__(self):
        from qt4c import qpath
        import platform
        if platform.release() == 'XP':
            qp = qpath.QPath("/ClassName='Shell_TrayWnd'/ClassName='TrayNotifyWnd'/ClassName='ToolbarWindow32' && MaxDepth='5' && Instance='0'")
        else:
            qp = qpath.QPath("/ClassName='Shell_TrayWnd'/ClassName='TrayNotifyWnd'/ClassName='SysPager'/ClassName='ToolbarWindow32' && MaxDepth='5'")
        Control.__init__(self, locator=qp)
    
    @property
    def Items(self):
        """返回TrayNotifyBar的全部TrayNotifyIcon
        """
        itemcount = win32gui.SendMessage(self.HWnd, commctrl.TB_BUTTONCOUNT, 0, 0)
        tb = wintypes.TBBUTTON()
        tbsize = ctypes.sizeof(wintypes.TBBUTTON)
        td = wintypes.TRAYDATA()
        tdsize = ctypes.sizeof(wintypes.TRAYDATA)
        pm = util.ProcessMem(self.ProcessId, buffer_size=tbsize)
        items = []
        for i in range(itemcount):
            win32gui.SendMessage(self.HWnd, commctrl.TB_GETBUTTON, i, pm.Buffer)
            pm.read(ctypes.byref(tb), tbsize)
            pmtmp = util.ProcessMem(self.ProcessId, remote_buffer=tb.dwData)
            pmtmp.read(ctypes.byref(td), tdsize)
            
            isSeparator = tb.fsStyle & commctrl.TBSTYLE_SEP
            isEnable = tb.fsState & commctrl.TBSTATE_ENABLED
            if not isSeparator and isEnable:
                items.append(_TrayIcon(tb, td, self))
        
        return items
    
    def refresh(self):
        """刷新通知区域
        """
        width = self.BoundingRect.Width
        height = self.BoundingRect.Height
        hwnd = self.HWnd
        row = height // 16
        col = width // 16
        itemCnt = row * col
        for _ in range(itemCnt):
            l,t,r,b = self.BoundingRect.All
            for y in range(t,b,8):
                for x in range(l,r,8):
                    Mouse.postMove(hwnd, x, y)
#                    win32api.SetCursorPos((x,y))
            time.sleep(0.05)
    
    def __getitem__(self, key):
        if isinstance(key, six.string_types):
            return None
        else:
            for icon in self.Items:
                if icon.ProcessId == key:
                    return icon
            return None
    
class TrayTaskBar(Control):
    """系统的任务栏区域(win7以上不可用)
    """
    def __init__(self):
        from qt4c import qpath
        qp = qpath.QPath("/ClassName='Shell_TrayWnd'/ClassName='ReBarWindow32'/Text='运行应用程序' && ClassName='ToolbarWindow32' && MaxDepth='2'")
        Control.__init__(self, locator=qp)
    
    @property
    def Items(self):
        """返回TrayTaskBar的全部TrayNotifyIcon
        """
        itemcount = win32gui.SendMessage(self.HWnd, commctrl.TB_BUTTONCOUNT, 0, 0)
        tb = wintypes.TBBUTTON()
        tbsize = ctypes.sizeof(wintypes.TBBUTTON)
        td = wintypes.TRAYDATA()
        tdsize = ctypes.sizeof(wintypes.TRAYDATA)
        pm = util.ProcessMem(self.ProcessId, buffer_size=tbsize)
        items = []
        for i in range(itemcount):
            win32gui.SendMessage(self.HWnd, commctrl.TB_GETBUTTON, i, pm.Buffer)
            pm.read(ctypes.byref(tb), tbsize)
            pmtmp = util.ProcessMem(self.ProcessId, remote_buffer=tb.dwData)
            pmtmp.read(ctypes.byref(td), tdsize)
            isSeparator = tb.fsStyle & commctrl.TBSTYLE_SEP
            isEnable = tb.fsState & commctrl.TBSTATE_ENABLED
            if not isSeparator and isEnable:
                items.append(_TrayIcon(tb, td, self))
        
        return items
    
    def __getitem__(self, key):
        if isinstance(key, six.string_types):
            for icon in self.Items:
                if icon.Tips == key:
                    return icon
            return None
        else:
            for icon in self.Items:
                if icon.ProcessId == key:
                    return icon
            return None
        
class _TrayIcon(control.Control):
    """通知栏或任务栏的项
    """
    def __init__(self, tbButton, trayData, notifyBar):
        '''不要直接实例化这个类，应该用TrayNotifyBar.Items得到这个类的实例
        '''
        self._tb = copy.deepcopy(tbButton)
        self._td = copy.deepcopy(trayData)
        self._notifybar = notifyBar

    @property
    def BoundingRect(self):
        """托盘图标的位置
        
        :rtype: util.Rectangle
        :return: util.Rectangle
        """
        barBoundingRect = self._notifybar.BoundingRect
        rcsize = ctypes.sizeof(wintypes.RECT)
        pm = util.ProcessMem(self._notifybar.ProcessId, buffer_size=rcsize)
        rc = wintypes.RECT()
        
        win32gui.SendMessage(self._notifybar.HWnd, 
                             commctrl.TB_GETRECT, 
                             self._tb.idCommand, 
                             pm.Buffer)
        pm.read(ctypes.byref(rc), rcsize)
        left = barBoundingRect.Left + rc.left
        top = barBoundingRect.Top + rc.top
        right = left + rc.right - rc.left
        bottom = top + rc.bottom - rc.top
        return util.Rectangle((left, top, right, bottom))
    
    @property
    def ProcessId(self):
        """图标所代表的进程Id
        """
        return win32process.GetWindowThreadProcessId(self._td.hwnd)[1]
        
    @property
    def State(self):
        """图标状态，隐藏or显示
        """
        return self._tb.fsState
    
    @property
    def Style(self):
        """图标风格，分隔符or自定义图片之类
        """
        return self._tb.fsStyle
    
    @property
    def Tips(self):
        """图标提示
        """
        pm = util.ProcessMem(self._notifybar.ProcessId, remote_buffer=self._tb.iString)
        # tips = ctypes.c_wchar_p('\0' * win32con.MAX_PATH)
        tips = ctypes.create_unicode_buffer(win32con.MAX_PATH)
        pm.read(tips, win32con.MAX_PATH)
        from qt4c.util import myEncode
        if isinstance(tips.value, six.text_type):
            return myEncode(tips.value, 'utf-8', 'UNICODE')
        else:
            return myEncode(tips.value, 'utf-8', 'GBK')
        
    @property
    def Visible(self):
        """是否可见
        """
        isVisible = not (self._tb.fsState & commctrl.TBSTATE_HIDDEN)
        return isVisible
    
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        '''点击控件 (同步操作)
        
        :type mouseFlag: qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: qt4c.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移；
        '''
        self.hover()
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.sendClick(self._notifybar.HWnd, x,y, mouseFlag, clickType)
    
    def destroy(self):
        """销毁该图标使之不再显示
        """
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._td.hwnd, self._td.uID))
        
    def equal(self, other):
        if isinstance(other, _TrayIcon):
            return self.ProcessId==other.ProcessId
        return id(self)==other
 
 
class ComboBox(Control):
    """ComboBox 控件类型
    """
    @property 
    def Count(self):
        '''返回ComboBox的项目数
        '''
        return win32gui.SendMessage(self.HWnd,win32con.CB_GETCOUNT)
               
    @property
    def SelectedIndex(self):
        '''返回当选选中的索引值
        '''
        return win32gui.SendMessage(self.HWnd,win32con.CB_GETCURSEL)

    @SelectedIndex.setter
    def SelectedIndex(self, _item):
        """
        
        :desc: 选择ComboBox的某个item
        :param _item       in, 可以为数字索引值，也可以为文本
        """
#        if not CheckValidHWnd(self.HWnd):
#            return None
        
        itemCount = self.Count
        win32gui.SendMessage(self.HWnd, win32con.CB_SHOWDROPDOWN , True, 0)
        hComboLBoxWnd = win32gui.FindWindow('ComboLBox',None)
        ctrlId = win32gui.GetDlgCtrlID(hComboLBoxWnd)
        
        if isinstance(_item, six.integer_types):
            if((itemCount == win32con.CB_ERR) or
                            (_item >= itemCount) or (_item < -1)):
                raise IndexError("%d超出索引！" % _item)#Exception('Item is disability')
            win32gui.SendMessage(self.HWnd, win32con.CB_SETCURSEL, _item, 0)
            win32gui.PostMessage(self.HWnd, win32con.WM_COMMAND, (win32con.CBN_SELCHANGE << 16) | ctrlId, hComboLBoxWnd)
        else:
            item = _item
            itemList = []
            for i in range(itemCount):
                # pBuf = win32gui.PyMakeBuffer(win32con.MAX_PATH)
                # nchars = win32gui.SendMessage(self.HWnd, win32con.CB_GETLBTEXT, i, pBuf)
                # str_val = pBuf[:nchars]
                # itemList.append(str_val.decode('gbk').encode('utf8'))

                pBuf = ctypes.create_unicode_buffer(win32con.MAX_PATH)
                nchars = ctypes.windll.user32.SendMessageW(self.HWnd, win32con.CB_GETLBTEXT, i, ctypes.byref(pBuf))
                if nchars:
                    str_val = pBuf.value
                    if six.PY2:
                        str_val = str_val.encode('utf8')
                    itemList.append(str_val)
                else:
                    raise ValueError("未找到%s" % item) # Exception('Item is disability')
            if item not in itemList:
                raise ValueError("未找到%s" % item) # Exception('Item is disability')            
            win32gui.SendMessage(self.HWnd, win32con.CB_SETCURSEL, itemList.index(item), 0)
            win32gui.PostMessage(self.HWnd, win32con.WM_COMMAND, (win32con.CBN_SELCHANGE << 16) | ctrlId, hComboLBoxWnd)

    def _getTextByIndex(self, idx=-1):
        if idx < 0 or idx > self.Count - 1:
            return None
        
        # pBuf = win32gui.PyMakeBuffer(win32con.MAX_PATH)
        # nchars = win32gui.SendMessage(self.HWnd, win32con.CB_GETLBTEXT, idx, pBuf)
        # str_val = pBuf[:nchars]
        pBuf = ctypes.create_unicode_buffer(win32con.MAX_PATH)
        nchars = ctypes.windll.user32.SendMessageW(self.HWnd, win32con.CB_GETLBTEXT, idx, ctypes.byref(pBuf))
        if nchars:
            str_val = pBuf.value
            if six.PY2:
                str_val = str_val.encode('utf8')
        else:
            raise ValueError('获取文本失败')
        return str_val
        
    def getFullPath(self):
        retList = []
        curIdx = self.SelectedIndex
        itemTxt = self.Text
        
        if not itemTxt:
            return None
        retList.insert(0, itemTxt)
        for i in range(curIdx-1, -1, -1):
            itemTxt = self._getTextByIndex(i)
            if itemTxt and itemTxt.find(':') > -1:
                retList.insert(0, itemTxt[-3:-1])
                break
            else:
                retList.insert(0, itemTxt)
        bRoot = os.path.exists(retList[0] + '\\')
        bNotRoot = os.path.exists('\\'.join(retList))
        length = len(retList)
        if (length==1 and bRoot) or (length>1 and bNotRoot):
            return '\\'.join(retList)
        elif retList:
            return retList[-1]
        else:
            return None
        
class TreeView(Control):
    """Sys TreeView 32 控件类型
    """
    
    def count(self):
        '''返回TreeView的item数
        '''
        return win32gui.SendMessage(self.HWnd,commctrl.TVM_GETCOUNT)
        
    @property
    def Items(self):
        '''返回TreeView的首层节点列表
        
        :rtype: list
        '''
        itemlist = _ITEMLIST()
        #get root item first
        item = TreeViewItem(self.HWnd, win32gui.SendMessage(self.HWnd, commctrl.TVM_GETNEXTITEM, commctrl.TVGN_ROOT, 0))
        itemlist.append(item)
        #then get sibling of root item
        while True:
            try:
                item = item.NextSibling
            except ControlNotFoundError:
                break
            if item.BoundingRect.Height == 0:
                for subitem in item.Items:
                    itemlist.append(subitem)
            else:
                itemlist.append(item)
        return itemlist


class TreeViewItem(control.Control):
    """TreeView Item类，不要直接实例化这个类，而通过TreeView.Items来获取。
    """
    def __init__(self, hwnd, item):
        '''Constructor
        
        :param hwnd: TreeView的窗口句柄
        :param item: TreeView的内部控件对象
        '''    
        if item == 0:
            raise ControlNotFoundError("TreeView Item is not found or unavailable!")
        self._hwnd = hwnd
        self._pid = win32process.GetWindowThreadProcessId(hwnd)[1]
        self.__item = item
        control.Control.__init__(self)
    
    @property
    def HWnd(self):
        '''窗口句柄
        '''
        return self.hwnd

    @property
    def hwnd(self):
        '''窗口句柄
        '''
        return self._hwnd
    
    def ensureVisible(self):
        '''先保证item完全可见
        '''
        win32gui.SendMessage(self.HWnd, commctrl.TVM_ENSUREVISIBLE, 0, self.__item)
        
    def select(self):
        '''选中自身结点
        '''
        self.ensureVisible()
        win32gui.SendMessage(self.HWnd, commctrl.TVM_SELECTITEM, commctrl.TVGN_CARET, self.__item)
        
        
    @property
    def BoundingRect(self):              
        rect_size = ctypes.sizeof(wintypes.RECT)
        pmrect = ProcessMem(processId=self._pid, buffer_size=rect_size)
        pmrect.write(ctypes.byref(ctypes.c_int(self.__item)), rect_size)
        win32gui.SendMessage(self.HWnd, commctrl.TVM_GETITEMRECT, True, pmrect.Buffer)
        rect = wintypes.RECT()
        pmrect.read(ctypes.byref(rect), rect_size)
        tvrect = win32gui.GetWindowRect(self.HWnd)
        return Rectangle((tvrect[0]+rect.left, tvrect[1]+rect.top, tvrect[0]+rect.right, tvrect[1]+rect.bottom))

    @property
    def Items(self):        
        children_list = _ITEMLIST()
        child = win32gui.SendMessage(self.HWnd, commctrl.TVM_GETNEXTITEM, commctrl.TVGN_CHILD, self.__item)     
        while child:
            children_list.append(TreeViewItem(self.HWnd, child))
            child = win32gui.SendMessage(self.HWnd, commctrl.TVM_GETNEXTITEM, commctrl.TVGN_NEXT, child)            
        return children_list
    
    @property
    def Selected(self):        
        TVM_GETITEMSTATE = commctrl.TV_FIRST+39
        state = win32gui.SendMessage(self.HWnd, TVM_GETITEMSTATE, self.__item, commctrl.TVIS_SELECTED)
        return (state & commctrl.TVIS_SELECTED)>0      
    
    @property
    def Text(self):
        pmbuf = ProcessMem(processId=self._pid, buffer_size=win32con.MAX_PATH)
        pmbuf.write(ctypes.c_char_p(six.b('\0') * win32con.MAX_PATH), win32con.MAX_PATH)                       
        ptext = ctypes.c_char_p(six.b('\0') * win32con.MAX_PATH)
        tvi = wintypes.TVITEM()
        tvi.mask = commctrl.TVIF_TEXT
        tvi.pszText = pmbuf.Buffer
        tvi.cchTextMax = win32con.MAX_PATH
        tvi.hItem = self.__item
        tvisize = ctypes.sizeof(wintypes.TVITEM)        
        pmtvi = ProcessMem(processId=self._pid, buffer_size=tvisize)        
        pmtvi.write(ctypes.byref(tvi), tvisize)        
        win32gui.SendMessage(self.HWnd, commctrl.TVM_GETITEM, 0, pmtvi.Buffer)
        pmbuf.read(ptext, win32con.MAX_PATH)    
        return util.myEncode(ptext.value, 'utf-8', 'gbk') 
    
    @property
    def NextSibling(self):
        return TreeViewItem(self.HWnd, win32gui.SendMessage(self.HWnd, commctrl.TVM_GETNEXTITEM, commctrl.TVGN_NEXT, self.__item))


class _ITEMLIST(list):
    def __getitem__(self, key):
        if isinstance(key, int):
            cnt = len(self)
            if key >= cnt:
                raise IndexError("key(%d)已超出下标范围!" % key)
            else:
                return list.__getitem__(self, key)
        elif isinstance(key, six.string_types):
            if(isinstance(key, six.text_type)):
                key = key.encode('utf8')
            for item in self:
                if item.Text == key:
                    return item
            
class MenuItem(Control):
    '''菜单项控件。不要直接实例化这个类，而通过Menu.MenuItems来获取。
    '''
    class EnumMenuItemState(object):
        DISABLED = "Disabled"
        GRAYED = "Grayed"
        NORMAL = "Normal"
        UNKNOWN = "Unknown"
        
    def __init__(self, menu, index):
        MN_GETHMENU = 0x01E1
        self.menu = menu
        self.hMenu = win32gui.SendMessage(menu.HWnd, MN_GETHMENU, 0, 0)
        self.idx = index
        
    @property
    def IsSeperator(self):
        """返回该子项是否是分割线
        """
        uItemState = win32gui.GetMenuState(self.hMenu, self.idx, win32con.MF_BYPOSITION)
        return (uItemState & win32con.MF_SEPARATOR) > 0
    
    @property
    def State(self):
        """返回菜单项的状态
        
        :rtype: EnumMenuItemState
        """
        uItemState = win32gui.GetMenuState(self.hMenu, self.idx, win32con.MF_BYPOSITION)
        if (uItemState & win32con.MF_GRAYED) > 0:
            return MenuItem.EnumMenuItemState.GRAYED
        elif (uItemState & win32con.MF_DISABLED) > 0:
            return MenuItem.EnumMenuItemState.DISABLED
        elif uItemState == -1:
            return MenuItem.EnumMenuItemState.UNKNOWN
        else:
            return MenuItem.EnumMenuItemState.NORMAL
    
    @property
    def Text(self):
        """可见文本
        """
        if not self.IsSeperator and self.State == MenuItem.EnumMenuItemState.NORMAL:
            pText = ctypes.c_char_p(six.b('\0') * win32con.MAX_PATH)
            ctypes.windll.user32.GetMenuStringA(self.hMenu, 
                                                self.idx, 
                                                pText, 
                                                win32con.MAX_PATH, 
                                                win32con.MF_BYPOSITION)
            text = pText.value
            os_encoding = locale.getdefaultlocale(None)[1]
            try:
                if six.PY3:
                    return text.decode(os_encoding)
                return text.decode(os_encoding).encode('utf-8')
            except UnicodeDecodeError:
                return text
        return None
            
    @staticmethod
    def __enum_childwin_callback(hwnd, hwnds):
        if hwnd and win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
    
    def __getSysMenuWindow(self):
        hwnds = []
        win32gui.EnumWindows(MenuItem.__enum_childwin_callback, hwnds)
        menuWnds = []
        for hwnd in hwnds:
            if '#32768' == Window(root=hwnd).ClassName:
                menuWnds.append(hwnd)
        return len(menuWnds)
    
    @property
    def SubMenu(self):
        """鼠标移动到该子项上，产生子菜单，并返回该子菜单
        
        :rtype: Menu
        """
        MN_GETHMENU = 0x01E1
        x, y = self.BoundingRect.Center.All
        menuWndsCnt = self.__getSysMenuWindow()
        Mouse.click(x, y)
        self._timeout.retry(self.__getSysMenuWindow, (), (), lambda x: x == menuWndsCnt+1)
        hSubMenuWnd = 0
        hSubMenu = win32gui.GetSubMenu(self.hMenu, self.idx)
        hwnds = []
        win32gui.EnumWindows(MenuItem.__enum_childwin_callback, hwnds)
        for hwnd in hwnds:
            hMenu = win32gui.SendMessage(hwnd, MN_GETHMENU, 0, 0)
            if hMenu == hSubMenu:
                hSubMenuWnd = hwnd
                break
        
        if hSubMenuWnd:
            return Menu(root=hSubMenuWnd)
    
    @property
    def BoundingRect(self):
        """返回rect
        """
        left, top, right, bottom = win32gui.GetMenuItemRect(self.menu.HWnd, self.hMenu, self.idx)[-1]
        return util.Rectangle((left, top, right, bottom))
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None,
                    yOffset=None):
        """点击控件
        
        :type mouseFlag: qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: qt4c.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移；
        """
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.click(x,y, mouseFlag, clickType)
        # Mouse.sendClick(self.menu.HWnd, x,y, mouseFlag, clickType)
            
class Menu(Window):
    '''
            菜单控件
    '''
    def __init__(self, root=None, locator=None):
        '''Constructor，当root和locator都是None时找到当前的唯一显示的菜单
        
        :param root: root控件
        :param locator: 定位参数 
        '''
        if root==None and locator==None:
            control.Control.__init__(self)
            hwnd = Menu._timeout.retry(self.__findSysMenuWindow,(),(),lambda x: x != None)
            root = Control(root=hwnd)
        
        Window.__init__(self, root, locator)
    
    def _getSubMenuItemsCount(self):
        MN_GETHMENU = 0x01E1
        hMenu = win32gui.SendMessage(self.HWnd, MN_GETHMENU, 0, 0)
        if hMenu:
            return win32gui.GetMenuItemCount(hMenu)
        return 0
    
    def __findSysMenuWindow(self):
#        import exceptions
        hwnds = []
        win32gui.EnumWindows(Menu.__enum_childwin_callback, hwnds)
        menuWnds = []
        for hwnd in hwnds:
            if '#32768' == Window(root=hwnd).ClassName:
                menuWnds.append(hwnd)
        if not menuWnds:
            return None
        menuCount = len(menuWnds)
        if menuCount > 1:
            raise ControlAmbiguousError("%d menu windows found!" % menuCount)
        return menuWnds[0]
    
    @staticmethod
    def closeAllSysMenuWindow():
        """关闭所有的系统menu窗口
        """
        hwnds = []
        win32gui.EnumWindows(Menu.__enum_childwin_callback, hwnds)
        for hwnd in hwnds:
            menuWnd = Window(root=hwnd)
            if '#32768' == menuWnd.ClassName:
                menuWnd.close()
        
    @staticmethod
    def __enum_childwin_callback(hwnd, hwnds):
        if hwnd and win32gui.IsWindowVisible(hwnd):
            hwnds.append(hwnd)
    
    def __iter__(self):
        cnt = self._getSubMenuItemsCount()
        for i in range(cnt):
            yield MenuItem(self, i)
            
    def __getitem__(self, key):
        '''根据key返回MenuItem
        key: 菜单索引或菜单文字
        '''
        self._timeout.retry(self._getSubMenuItemsCount, (), (), lambda x: x > 0)
        
        cnt = self._getSubMenuItemsCount()
        if isinstance(key, six.integer_types):
            if key >= cnt:
                raise IndexError("key(%d)超出下标范围!" % key)
            return MenuItem(self, key)
        if isinstance(key, six.string_types):
            for i in range(cnt):
                mi = MenuItem(self, i)
                if mi.Text == key:
                    return mi
            raise IndexError("item(%s) not found!" % key)
        raise TypeError("type(%s) error!" % str(type(key)))
       
    @property
    def MenuItems(self):
        '''获取MenuItem。通过MenuItems[菜单项索引]或MenuItems[菜单项文字]返回MenuItem实例。
        '''
        return self


if __name__ == '__main__':
    pass
