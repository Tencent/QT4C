# Native Control

Native Control对应系统原生控件，在Native Control中所有操作都是通过调用Windows API实现的。在Native Control中封装了_CWindow作为桥接，通过_CWindow使用pywin32库实现了对Windows API的封装。

Native Control的实现在qt4c.wincontrols.Control中，它继承于qt4c.control.Control类。在Native控件类的初始化函数_init_wndobj中，首先通过传入的root参数（类型为qt4c.wincontrols.Control 或者为空）锁定根节点，如果root为空，则获取DeskTop作为根节点，通过传入的locator利用win32gui.EnumWindows递归搜索根节点的子孙节点，锁定封装的控件，利用其句柄来封装_CWindow对象。Native控件的所有属性、操作都是利用其句柄来调用Windows API进行实现的。相关实现如下:
```
def _init_wndobj(self):
    '''初始化Win32窗口对象
    '''
    if self._locator is None and self._root is None:
        wndobj =  _CWindow(int(win32gui.GetDesktopWindow()))
    elif self._locator is None:
        if isinstance(self._root, int) or isinstance(self._root, long): #root is a hwnd
            wndobj = _CWindow(self._root)
        elif isinstance(self._root, Control):
            wndobj = _CWindow(self._root.HWnd)
        elif isinstance(self._root, _CWindow):
            wndobj = self._root
    else:
        try:
            kwargs = {'root':self._root}
            foundctrls =  self._timeout.retry(self._locator.search, kwargs, (), lambda x: len(x)>0 )
        except TimeoutError, erro:
            raise ControlNotFoundError("<%s>中的%s查找超时：%s" % (self._locator, self._locator.getErrorPath(), erro))
        nctrl = len(foundctrls)
        if (nctrl>1):
            raise ControlAmbiguousError("<%s>找到%d个控件" % (self._locator, nctrl))
        wndobj = _CWindow(foundctrls[0].HWnd)
    return wndobj
```