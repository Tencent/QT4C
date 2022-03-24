# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#
'''
控件基类模块
'''
from __future__ import division
import six

from testbase.util import Timeout
from qt4c.mouse import Mouse, MouseFlag, MouseClickType
from qt4c.keyboard import Keyboard
from qt4c.util import MetisView
#__all__=['Control']
    
#===============================================================================
# 基础控件类定义
#===============================================================================
class Control(object):
    '''
    控件基类
    '''
    
    _timeout=Timeout(5,0.5) #控件查找timeout时间 
    def __init__(self):
        pass
    
    @property
    def Children(self):
        '''返回此控件的子控件。需要在子类中实现。
        '''
        raise NotImplementedError("请在%s类中实Children属性" % type(self))
    
#     @staticmethod
#     def exist(locator, root=None, timeout=10, interval=0.5):
#         '''在timeout时间内检查控件，返回找到的控件个数。
#         
#         :type locator: QPath
#         :param locator: 查找方式
#         :param root: 开始查找的父控件
#         :param timeout: 控件查找超时时间
#         :param interval: 查找间隔 
#         :return: 找到的控件个数
#         '''
#         
#         import util
#         ctrls = []
#         try: 
#             ctrls = util.Timeout(timeout, interval).retry(locator.search, (root,), (), lambda x: len(x) != 0)
#         except TimeoutError:
#             pass
#         return len(ctrls)
#     
#     @classmethod
#     def exist2(cls, *args, **kwargs):
#         '''在timeout时间内检查控件是否存在，返回True or False
#         
#         :param kwargs: 可变参数。代表控件类实例化所需的参数，比如说通过MainPanel类调用该函数，则参数传入qqapp实例
#         :param args: 可变参数。代表控件类实例化所需的参数，比如说通过MainPanel类调用该函数，则参数传入qqapp实例
#         :return: 该类型控件是否存在，True or False
#         :attention: 如果通过某个类的QPATH能找到多个符合条件的控件，会抛出ControlAmbiguousError，
#                                                     这表明该控件类的QPATH定义是不准确的
#         '''
#         return cls(*args, **kwargs).exist()
    
    def _click(self, mouseFlag, clickType, xOffset, yOffset):
        '''点击控件
        
        :type mouseFlag: qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: qt4c.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域x轴上的中点；
                                                               如果为负值，代表距离控件区域右边的绝对值偏移；
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。
                                                               默认值为None，代表控件区域y轴上的中点；
                                                              如果为负值，代表距离控件区域上边的绝对值偏移；
        '''
        if not self.BoundingRect:
            return
        (l, t, r, b) = self.BoundingRect.All
        if xOffset is None:
            x = (l + r) // 2
        else:
            if xOffset < 0:
                x = r + xOffset
            else:
                x = l + xOffset
        if yOffset is None:
            y = (t + b) // 2
        else:
            if yOffset < 0:
                y = b + yOffset
            else:
                y = t + yOffset        
        Mouse.click(x, y, mouseFlag, clickType)
        
    def click(self, mouseFlag=MouseFlag.LeftButton, 
                    clickType=MouseClickType.SingleClick,
                    xOffset=None, yOffset=None):
        '''点击控件
        
        :type mouseFlag: qt4c.mouse.MouseFlag
        :param mouseFlag: 鼠标按钮
        :type clickType: qt4c.mouse.MouseClickType 
        :param clickType: 鼠标动作
        :type xOffset: int
        :param xOffset: 距离控件区域左上角的偏移。默认值为None，代表控件区域x轴上的中点。 如果为负值，代表距离控件区域右上角的x轴上的绝对值偏移。
        :type yOffset: int
        :param yOffset: 距离控件区域左上角的偏移。 默认值为None，代表控件区域y轴上的中点。如果为负值，代表距离控件区域右上角的y轴上的绝对值偏移。
        '''
        self.hover()
        x, y = self._getClickXY(xOffset, yOffset)
        Mouse.click(x, y, mouseFlag, clickType)
        
    def _getClickXY(self, xOffset, yOffset):
        '''通过指定的偏移值确定具体要点击的x,y坐标
        '''
        if not self.BoundingRect:
            return
        (l, t, r, b) = self.BoundingRect.All
        if xOffset is None:
            x = (l + r) // 2
        else:
            if xOffset < 0:
                x = r + xOffset
            else:
                x = l + xOffset
        if yOffset is None:
            y = (t + b) // 2
        else:
            if yOffset < 0:
                y = b + yOffset
            else:
                y = t + yOffset
        return x, y       
    
    def doubleClick(self, xOffset=None, yOffset=None):
        """左键双击，参数参考click函数
        """
        self.click(MouseFlag.LeftButton, MouseClickType.DoubleClick, xOffset, yOffset)
    
    def hover(self):
        """鼠标移动到该控件上
        """
        if not self.BoundingRect:
            return
#        (l, t, r, b) = (self.BoundingRect.Left, 
#                        self.BoundingRect.Top,
#                        self.BoundingRect.Right,
#                        self.BoundingRect.Bottom
#                        )

        x, y = self.BoundingRect.Center.All
        Mouse.move(x, y)
        
    def rightClick(self, xOffset=None, yOffset=None):
        """右键双击，参数参考click函数
        """
        self.click(MouseFlag.RightButton, xOffset=xOffset, yOffset=yOffset)
    
       
#    def leftClick(self):
#        self.click(MouseFlag.LeftButton)
        
    def drag(self, toX, toY):
        '''拖拽控件到指定位置
        '''
        if not self.BoundingRect:
            return
        (l, t, r, b) = (self.BoundingRect.Left, 
                        self.BoundingRect.Top,
                        self.BoundingRect.Right,
                        self.BoundingRect.Bottom
                        )
        x, y = (l + r) // 2, (t + b) // 2
        Mouse.drag(x, y, toX, toY)

    def scroll(self, backward=True):
        '''发送鼠标滚动命令
        '''
        self.hover()
        Mouse.scroll(backward)
    
    def sendKeys(self, keys):
        '''发送按键命令
        '''
        self.setFocus()
        Keyboard.inputKeys(keys)

    def setFocus(self):
        '''设控件为焦点
        '''
        raise NotImplementedError('please implement in sub class')
    
    def waitForValue(self, prop_name, prop_value, timeout=10, interval=0.5, regularMatch=False):
        """等待控件属性值出现, 如果属性为字符串类型，则使用正则匹配
        
        :param prop_name: 属性名字
        :param prop_value: 等待出现的属性值
        :param timeout: 超时秒数, 默认为10
        :param interval: 等待间隔，默认为0.5
        :param regularMatch: 参数 property_name和waited_value是否采用正则表达式的比较。默认为不采用（False）正则，而是采用恒等比较。
        """
        Timeout(timeout, interval).waitObjectProperty(self, prop_name, prop_value, regularMatch)
    
    @property
    def BoundingRect(self):
        """返回窗口大小。未实现！
        """
        raise NotImplementedError("please implement in sub class")
    
    def equal(self, other):
        '''判断两个对象是否相同。未实现!
        
        :type other: Control
        :param other: 本对象实例
        '''
        raise NotImplementedError("please implement in sub class")
        
    def __eq__(self, other):
        """重载对象恒等操作符(==)
        """
        return self.equal(other)
    
    def __ne__(self, other):
        """重载对象不等操作符(!=)
        """
        return (not self.equal(other))
    
    def get_metis_view(self):
        '''返回MetisView
        '''
        return MetisView(self)
    
class ControlContainer(object):
    '''控件集合接口
    
    当一个类继承本接口，并设置Locator属性后，该类可以使用Controls属于获取控件。如
    
    >>>class SysSettingWin(uia.UIAWindows, ControlContainer)
            def __init__(self):
                locators={'常规页': {'type':uia.Control, 'root':self, 'locator'='PageBasicGeneral'},
                          '退出程序单选框': {'type':uia.RadioButton, 'root':'@常规页','locator'=QPath("/name='ExitPrograme_RI' && maxdepth='10'")}}
                self.updateLocator(locators)
                                 
    则SysSettingWin().Controls['常规页']返回设置窗口上常规页的uia.Control实例,
    而SysSettingWin().Controls['退出程序单选框']，返回设置窗口的常规页下的退出程序单选框实例。
    其中'root'='@常规页'中的'@常规页'表示参数'root'的值不是这个字符串，而是key'常规页'指定的控件。
    '''
    
    def __init__(self):
        self._locators = {}
    
    def __findctrl_recur(self, ctrlkey):
        if not (ctrlkey in self._locators.keys()):
            raise NameError("%s没有名为'%s'的子控件！" % (type(self), ctrlkey))
        params = self._locators[ctrlkey].copy()
        ctrltype = params['type']
        del params['type']
        for key in params:
            value = params[key]
            if isinstance(value, six.string_types) and value.startswith('@'):
                params[key] = self.__findctrl_recur(value[1:])
        if issubclass(ctrltype, Control):
            return ctrltype(**params)
        else:
            root = params.pop("root", None)
            if root == None:
                root = self
            return ctrltype(root, ctrlkey, **params)
        
        
    def __getitem__(self, index):
        '''获取index指定控件
        
        :type index: string
        :param index: 控件索引，如'查找按钮'  
        '''
        return self.__findctrl_recur(index)
    
    def clearLocator(self):
        '''清空控件定位参数
        '''
        self._locators = {}
    
    def hasControlKey(self, control_key):
        '''是否包含控件control_key
        
        :rtype: boolean
        '''
        return control_key in self._locators
    
    def updateLocator(self, locators):
        '''更新控件定位参数
        
        :type locators: dict
        :param locators: 定位参数，格式是 {'控件名':{'type':控件类, 控件类的参数dict列表}, ...}
        '''
        self._locators.update(locators)    
     
    def isChildCtrlExist(self, childctrlname):
        '''判断指定名字的子控件是否存在
        
        :param childctrlname: 指定的子控件名称
        :type childctrlname: str
        :rtype: boolean
        '''
        return self.Controls[childctrlname].exist()
    
    @property
    def Controls(self):
        '''返回控件集合。使用如foo.Controls['最小化按钮']的形式获取控件
        '''
        return self   
  
if __name__ == "__main__":
    pass
