封装Window
===========

==========
Window概述
==========
每个应用程序都包含多个窗口(Window)，每个窗口可以封装成一个窗口类，在lib库中实现，建议App中一个产品功能模块封装在一个py文件中，例如app的主面板相关作为一个py文件mainpanel.py，app的登录相关作为一个文件login.py，在文件中再具体实现多个相关类的UI封装。

==========
Window封装
==========
封装Window类需要继承QT4C的Window基类，根据当前应用程序的不同，可以选择不同的Window基类。当前QT4C提供两种Window基类：

* Win32窗口： :class:`qt4c.wincontrols.Window`

* UIA窗口： :class:`qt4c.uiacontrols.UIAWindows`

其中Win32窗口是Windows原生窗口，UIA窗口是基于UIA实现的，它是Microsoft Windows的一个辅助功能框架，使用时需要针对不同场景选择不同的Window基类。

在《:ref:`ui_locator`》中已经简单介绍了QPath的设计，你可以利用QPath来封装一个Window类::

    import qt4c.wincontrols as win
    from qt4c.qpath import QPath

    class MainPanel(win.Window):
        def __init__(self):
            qp = QPath("/ClassName='CalcFrame' && Text='计算器' && Visible='True'")
            super(MainPanel, self).__init__(locator=qp)

            locators = {
                '按键1': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x83'")},
                '按键2': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x84'")},
                '加号': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x5D'")},
                '等号': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Button' && MaxDepth='3' && ControlId='0x79'")},
                '结果': {'type': win.Control, 'root': self, 'locator': QPath("/ClassName='Static' && MaxDepth='3' && ControlId='0x96'")}

            }

            self.updateLocator(locators)

这是一个简单的计算器的主界面，因为在一个应用程序中，一个窗口的UI元素的属性基本上不会发生太大变化，所以你可以在封装一个Window类时就定义好QPath，这样子就不需要每一次在实例化窗口的时候都要编写一遍QPath了。
你可以在你的Window类实现你需要的功能，例如封装一个addNum方法来实现两个整数的相加（假设以“按键x”封装了计算器中的数字和小数点按键）::

    def addNums(self, num1, num2):
        self.wait_for_exist(5, 0.2)
        for i in str(num1):
            self.Controls[('按键%s' % i)].click()
        self.Controls['加号'].click()
        for i in str(num2):
            self.Controls[('按键%s' % i)].click()
        self.Controls['等号'].click()

对于UIAWindows，请参照接口文档进行使用。

=============
Window类使用
=============
定义好窗口类之后，在用例中我们可以实例化窗口类，并调用对应的功能接口::

    from demolib.mainpanel import MainPanel
    main_panel = MainPanel()
    main_panel.bringForeground()    # 将窗口设为最前端窗口(QT4C提供)
    main_panel.addNum(1, 2)         # 自定义方法
