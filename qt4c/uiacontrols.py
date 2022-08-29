# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''
使用UIA方式去访问控件
'''

import time
import six
from comtypes.client import CreateObject, GetModule
from ctypes import *

from testbase import logger
from testbase.util import LazyInit

from qt4c import wincontrols
from qt4c import control
from qt4c.util import Rectangle,Timeout
from qt4c.mouse import Mouse,MouseFlag,MouseClickType
from qt4c.keyboard import Keyboard
from qt4c.exceptions import ControlAmbiguousError, ControlNotFoundError, ControlExpiredError, TimeoutError


IUIAutomation = GetModule("UIAutomationCore.dll")
UIAutomationClient = CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=IUIAutomation.IUIAutomation)
RawWalker = UIAutomationClient.RawViewWalker
ControlWalker = UIAutomationClient.controlViewWalker
UIAControlType={50000: 'Button',
                 50001: 'Calendar', 
                 50002: 'CheckBox', 
                 50003: 'ComboBox', 
                 50004: 'Edit', 
                 50005: 'Hyperlink', 
                 50006: 'Image', 
                 50007: 'ListItem', 
                 50008: 'List', 
                 50009: 'Menu', 
                 50010: 'MenuBar', 
                 50011: 'MenuItem', 
                 50012: 'ProgressBar', 
                 50013: 'RadioButton', 
                 50014: 'ScrollBar', 
                 50015: 'Slider', 
                 50016: 'Spinner', 
                 50017: 'UStatusBar', 
                 50018: 'Tab', 
                 50019: 'TabItem', 
                 50020: 'Text', 
                 50021: 'ToolBar', 
                 50022: 'ToolTip', 
                 50023: 'Tree', 
                 50024: 'TreeItem', 
                 50025: 'Custom control type', 
                 50026: 'Group', 
                 50027: 'Thumb', 
                 50028: 'DataGrid', 
                 50029: 'DataItem', 
                 50030: 'Document', 
                 50031: 'SplitButton', 
                 50032: 'Window', 
                 50033: 'Pane', 
                 50034: 'Header', 
                 50035: 'HeaderItem', 
                 50036: 'Table', 
                 50037: 'TitleBar', 
                 50038: 'Separator', 
                 50039: 'SemanticZoom', 
                 50040: 'AppBar'}

def find_UIAElm(Condition,timeout=10):
    start = time.time()
    try_count = 0
    while time.time() - start < timeout:
        try:
            desk_elm = UIAutomationClient.GetRootElement()
            elm = desk_elm.FindFirst(IUIAutomation.TreeScope_Descendants,Condition)
            elm.CurrentName#验证获取到是不是空elm
            return elm
        except ValueError:
            logger.info("未查找到有效uia元素，尝试重新查找")
            time.sleep(0.5)
            try_count += 1
    raise TimeoutError("在%d秒里尝试了%d次" %(timeout,try_count))



class Control(control.Control):
    '''
    UIA方式访问控件基类
    '''
    def __init__(self,root=None,locator=None):
        '''构造函数        
        :type root: UIA.Control or None
        :param root: 开始查找的UIA控件或包含UIA的win32control.Window；
        :type locator: str or qt4c.qpath.QPath(后面支持）
        :param locator: UIA控件的name属性  or qpath(后面支持）
        :attention: 参数root和locator不能同时为None
        '''
        control.Control.__init__(self)
    
        if locator is None and root is None:
            raise RuntimeError("传入参数locator和root不能同时为None!")
        self._root = root
        self._locator = locator
        self._uiaobj = LazyInit(self,'_uiaobj',self._init_uiaobj)
        
    def _init_uiaobj(self):
        '''初始化uia对象
        '''
        if self._root is None:
            self._root = Control(root=UIAutomationClient.GetRootElement())
            self._root.empty_invoke()
            
            
        if isinstance(self._root, wincontrols.Control):
                pid = self._root.ProcessId
                if not pid or not self._root.Valid:
                    raise ControlExpiredError("父控件/父窗口已经失效，查找中止！")
                if self._locator is None:
                    cnd = UIAutomationClient.CreatePropertyCondition(IUIAutomation.UIA_NativeWindowHandlePropertyId,self._root.HWnd)
                    self._root = find_UIAElm(cnd)
                            
        if self._locator is None:
            if isinstance(self._root, Control):
                self._root.empty_invoke()
                elm = self._root._uiaobj
            elif isinstance(self._root, IUIAutomation.IUIAutomationElement):
                elm = self._root
            else:
                raise TypeError("root应为uiacontrols.Control类型或者UIA element，实际类型为：%s" % type(self._root))
        else:                        
            if isinstance(self._locator, six.string_types):
                if isinstance(self._root, Control):
                    args = (self._root,self._locator)
                    try:
                        from qt4c.qpath import _find_by_name
                        foundctrl = self._timeout.retry(_find_by_name, args, (ControlNotFoundError))
                        foundctrl.empty_invoke()
                        elm = foundctrl._uiaobj
                    except TimeoutError:
                        raise  ControlNotFoundError("找不到name为 (%s)的UIA子控件！" % self._locator)
                else:
                    raise TypeError("root应为uiacontrols.Control类型，实际类型为：%s" % type(self._root))
            else:
                try:
                    kwargs = {'root':self._root}
                    foundctrls =  self._timeout.retry(self._locator.search, kwargs, (), lambda x: len(x)>0)
                except TimeoutError as erro:
                    raise ControlNotFoundError("<%s>中的%s查找超时：%s" % (self._root,self._locator.getErrorPath(),erro))
                nctrl = len(foundctrls)
                if(nctrl>1):
                    raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
                foundctrls[0].empty_invoke()
                elm = foundctrls[0]._uiaobj
        return elm
    
    def empty_invoke(self):
        '''无意义调用，用于主动初始化对象
        '''
        self._uiaobj.CurrentName
        
    def SetFocus(self):
        self._uiaobj.SetFocus()#这个接口没有作用

    @property
    def Valid(self):
        """是否是有效控件
        """
        return self.Enabled
    
    @property
    def Width(self):
        """控件宽度
        """
        rect = self._getrect()
        return rect['Width']
        
    @property
    def Height(self):
        """控件高度
        """
        rect = self._getrect()
        return rect['Height']
    
    @property    
    def BoundingRect(self):
        """返回控件
        """
        rect = self._getrect()
        return Rectangle((int(rect['Left']),
                          int(rect['Top']),
                          int(rect['Left']+rect['Width']),
                          int(rect['Top']+rect['Height'])
                          ))
        
    def _getrect(self):
        rect = {'Left':0,'Top':0,'Width':0,'Height':0}
        ( rect['Left'], rect['Top'], rect['Width'], rect['Height'])=self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_BoundingRectanglePropertyId)
        return rect
    
    def click(self, mouseFlag = MouseFlag.LeftButton,
              clickType=MouseClickType.SingleClick,
              xOffset=None, yOffset=None):
        """点击控件
        :type mouseFlag:qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮类型
        :type clickType:qt4c.mouse.MouseClickType
        :param clickType:点击动作类型
        :type xOffset:int
        :param 横向偏移量
        :type yOffset:int
        :param 纵向偏移量
        """
        Timeout(5,0.5).waitObjectProperty(self, 'Enabled', True)
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.click(int(x),int(y), mouseFlag, clickType)
        
    @property
    def ProcessId(self):
        pid = self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_ProcessIdPropertyId)
        return pid
        
    @property
    def ControlType(self):
        """返回UIA控件的类型
        """
        typeint = self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_ControlTypePropertyId)
        return UIAControlType[typeint]
    
    @property
    def Enabled(self):
        """此控件是否可用
        """
        return self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_IsEnabledPropertyId)
    
    @property
    def Children(self):
        """返回子控件列表
        :rtype ListType
        """
        self.empty_invoke()
        children = []
        child = RawWalker.GetFirstChildElement(self._uiaobj)
        while(child != None):
            try:
                child.CurrentName#测试uiaelm对象是否有效
                children.append(Control(root=child))
                child = RawWalker.GetNextSiblingElement(child)
            except ValueError:
                child= None
        return children
    
    @property
    def Parent(self):
        self.empty_invoke()
        parent = RawWalker.GetParentElement(self._uiaobj)
        try:
            parent.CurrentName#测试uia elm对象是否有效
        except ValueError:
            parent =None
        else:
            return Control(root=parent)
    
    @property
    def Name(self):
        """返回control的name属性
        """
        return self._uiaobj.CurrentName
    
    @property
    def Type(self):
        """返回控件类型
        """
        return self._uiaobj.CurrentLocalizedControlType
    
    @property
    def Value(self):
        """返回控件value属性（通常是文本信息）
        """
        return self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_LegacyIAccessibleValuePropertyId)
    
    def equal(self, other):
        if not isinstance(other, Control):
            return False
        if self.ProcessId != other.ProcessId:
            return False
        return self._uiaobj == other._uiaobj
    
    def exist(self):
        """判断控件是否存在
        """
        try:
            self._init_uiaobj()
        except Exception as e:
            print("判断UIA控件存在失败,UIA elm实例化异常:%s" %e)
            return False
        return True
    
    def wait_for_exist(self,timeout,interval):
        """等待控件存在
        """
        Timeout(timeout,interval).retry(self.exist,(),(),lambda x:x==True)
    
    @property    
    def Hwnd(self):
        """返回控件句柄
        """
        return self.hwnd

    @property
    def HWnd(self):
        """兼容其他类型控件
        """
        return self.hwnd

    @property
    def hwnd(self):
        return self._uiaobj.CurrentNativeWindowHandle
    
    @property
    def HasKeyboardFocus(self):
        """返回是否被选为键盘输入
        """
        return self._uiaobj.CurrentHasKeyboardFocus
    
    @property
    def ClassName(self):
        """返回ClassName
        """
        return self._uiaobj.CurrentClassName

    @property
    def AutomationId(self):
        """返回AutomationId
        """
        return self._uiaobj.CurrentAutomationId
   

        
        
            
class UIAWindows(Control, control.ControlContainer):
    '''UIA控件窗体定义
    '''
    def __init__(self,root=None, locator=None):
        Control.__init__(self,root=root,locator=locator)
        control.ControlContainer.__init__(self)
    
    
    @property
    def Window(self):
        """返回wincontrols.Window
        """   
        return wincontrols.Window(root=self.Hwnd)

    @property
    def Visible(self):
        """窗口是否可见
        """
        if not self.Valid:
            return False
        return self.Window.Visible
    
    @property
    def Minimized(self):
        """该窗口是否最小化
        """
        if not self.Valid:
            raise RuntimeError("句柄无效，窗口已销毁!")
        return self.Window.Minimized
    
    


class Edit(Control):
    
    def input(self,data):
        """对Edit类型控件进行输入
        :type keys: utf-8 str or unicode
        :param keys: 键盘输入字符串,可输入组合键，如"{CTRL}{MENU}a"
        """
        self.click()
        time.sleep(0.5)
        keys = "{CTRL}a"
        Keyboard.inputKeys(keys)
        keys = "{DEL}"
        Keyboard.inputKeys(keys)
        Keyboard.inputKeys(data)

class ComboBox(Control):
    
    def input(self,data):
        """对Edit类型控件进行输入
        :type keys: utf-8 str or unicode
        :param keys: 键盘输入字符串,可输入组合键，如"{CTRL}{MENU}a"
        """
        self.click()
        time.sleep(0.5)
        keys = "{CTRL}a"
        Keyboard.inputKeys(keys)
        keys = "{DEL}"
        Keyboard.inputKeys(keys)
        Keyboard.inputKeys(keys)
        Keyboard.inputKeys(data)

    def expand(self):
        pattern = self._uiaobj.GetCurrentPattern(IUIAutomation.UIA_ExpandCollapsePatternId)
        dllpoint = cast(pattern, POINTER(IUIAutomation.IUIAutomationExpandCollapsePattern))
        ret = dllpoint.Expand() == 0
        return ret

    def collapse(self):
        pattern = self._uiaobj.GetCurrentPattern(IUIAutomation.UIA_ExpandCollapsePatternId)
        dllpoint = cast(pattern, POINTER(IUIAutomation.IUIAutomationExpandCollapsePattern))
        ret = dllpoint.Collapse() == 0
        return ret

    @property
    def Value(self):
        return self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_LegacyIAccessibleValuePropertyId)

    @Value.setter
    def Value(self, _item):
        """对Combobox类型控件设置value值
        :type keys: utf-8 str or unicode
        :param keys: 被设置选项的值
        """
        pattern = self._uiaobj.GetCurrentPattern(IUIAutomation.UIA_ValuePatternId)
        dllpoint = cast(pattern, POINTER(IUIAutomation.IUIAutomationValuePattern))
        ret = dllpoint.SetValue(_item) == 0
        return ret

class RadioButton(Control):
    def is_select(self):
        pattern = self._uiaobj.GetCurrentPattern(IUIAutomation.UIA_SelectionItemPatternId)
        dllpoint = cast(pattern, POINTER(IUIAutomation.IUIAutomationSelectionItemPattern))
        return dllpoint.CurrentIsSelected
        
if __name__ == '__main__':
    pass
