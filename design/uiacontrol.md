# UIA Control

UIA Control的实现在qt4c.uiacontrols.Control中，它和其他QT4C的Control保持一致，都是继承于qt4c.control.Control类。具体实现会依赖以下UI Automation模块：

* IUIAutomation:IUIAutomation用于提供一些UIAutomationCore.dll中定义的对象和属性，主要用于获取UIAutomationCore.dll库中定义的一些类和属性值。

```
IUIAutomation = GetModule("UIAutomationCore.dll")
```

* RawViewWalker:RawViewWalker.GetFirstChildElement(IUIAutomationElement)和RawViewWalker.GetNextSiblingElement(IUIAutomationElement)用于获取到IUIAutomationElement的孩子节点或者兄弟节点，实现Control.Children方法兼容QPath的search方法来遍历控件树，具体实现如下：
```
RawWalker = UIAutomationClient.RawViewWalker
@property
def Children(self):
    """返回子控件列表
    :rtype ListType
    """
    self.Enabled
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
```

* UIAutomationClient:UIAutomationClient是UIA的客户端，用于提供UIA的一些通用接口，例如生产RawViewWalker对象，提供GetRootElement方法获取桌面对应的UIA_Element,提供CreatePropertyCondition方法来生成控件属性的Condition对象。
```
UIAutomationClient = CreateObject("{ff48dba4-60ef-4201-aa87-54103eef594e}", interface=IUIAutomation.IUIAutomation)

# 生成控件属性为HWnd查找的Condition对象
cnd = UIAutomationClient.CreatePropertyCondition(IUIAutomation.UIA_NativeWindowHandlePropertyId,self._root.HWnd)
```

* IUIAutomationElement:每个IUIAutomationElement对象对应一个UIA控件，因此QT4C的每个UIA Control也拥有一个IUIAutomationElement成员变量用于提供基础的控件能力，例如对应的控件属性获取，查找子母控件等。
```
@property
def ControlType(self):
    """返回UIA控件的类型
    """
    typeint = self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_ControlTypePropertyId)
    return UIAControlType[typeint]
```

关于UIA模块更多使用可参照[UIA文档](https://docs.microsoft.com/en-us/windows/desktop/winauto/entry-uiauto-win32)。

## 初始化UIA窗口对象

在UIA的Control类的初始化函数_init_uiaobj中，首先将传入的root参数（类型为UIA的Control类或Native的Control类或者为空）利用UIA模块转换为UIA_Element，将该UIA_Element作为根节点。


```
#root为空，将桌面作为根节点
self._root = Control(root=UIAutomationClient.GetRootElement())

#root非空，使用HWnd定位根节点
cnd = UIAutomationClient.CreatePropertyCondition(IUIAutomation.UIA_NativeWindowHandlePropertyId,self._root.HWnd)
self._root = find_UIAElm(cnd)
```

之后通过RawWalker可以获取其子节点对应的UIA_Element，利用获取到的子节点通过传入的locator在根节点的子孙节点中进行递归搜索锁定封装的控件，返回其对应的UIA_Element中的_uiaobj，如果locator为空，直接返回根节点的_uiaobj。相关代码如下：

```
def _init_uiaobj(self):
    '''初始化uia对象
    '''
    if self._root is None:
        self._root = Control(root=UIAutomationClient.GetRootElement())
        self._root.Enabled
        
    # 将Native类型转换为uia类型控件
    if isinstance(self._root, wincontrols.Control):
            pid = self._root.ProcessId
            if not pid or not self._root.Valid:
                raise ControlExpiredError("父控件/父窗口已经失效，查找中止！")
            if self._locator is None:
                cnd = UIAutomationClient.CreatePropertyCondition(IUIAutomation.UIA_NativeWindowHandlePropertyId,self._root.HWnd)
                self._root = find_UIAElm(cnd)
                        
    if self._locator is None:
        # locator为空返回根节点
        if isinstance(self._root, Control):
            self._root.Enabled#激活init函数调用
            elm = self._root._uiaobj
        elif isinstance(self._root, IUIAutomation.IUIAutomationElement):
            elm = self._root
        else:
            raise TypeError("root应为uiacontrols。Control类型或者UIA element，实际类型为：%s" %type(self._root))
    else:
        # 根据locator查找控件树,与Native类型类似             
        ......
        elm = foundctrl._uiaobj
    return elm
```

通过_uiaobj，就可以调用接口去对应用程序获取属性并进行操作:
```
@property
def Enabled(self):
    """此控件是否可用
    """
    return self._uiaobj.GetCurrentPropertyValue(IUIAutomation.UIA_IsEnabledPropertyId)
```