输入操作
=========

在Win32应用自动化过程中,避免不了的是对设备的各种操作，例如鼠标点击、拖拽、键盘输入等等。QT4C通过Mouse类 :class:`qt4c.mouse.Mouse` 和 Keyboard类 :class:`qt4c.keyboard.Keyboard`，提供了常用的鼠标操作和键盘输入操作。

用户可以调用控件内已封装的接口进行设备操作，也可以调用Mouse类和Keyboard类的方法进行设备操作。

.. warning:: 请尽量使用控件内已封装的方法进行设备操作，不推荐直接调用Mouse类和Keyboard类的方法进行设备操作。

================
控件的点击及输入
================

QT4C在Control类和Window类中都封装有用于鼠标点击的接口，你可以直接调用这些接口进行设备操作::

    from demolib.mainpanel import MainPanel
    main_panel = MainPanel()
    main_panel.click(xOffset=100, yOffset=100)
    main_panel.Controls['按键1'].click()

对于部分Edit类控件，你可以直接修改其Text属性来达到键盘输入的效果，假设main_panel.Controls['密码框']是一个密码输入框::

    main_panel.Controls['密码框'].Text = 'XXXXXXXX'

=========
鼠标输入
=========

Mouse类中提供了鼠标移动、点击、拖拽等等操作，这里对一些比较常用的操作进行说明。除了以下操作之外，其他操作请具体参照接口文档 :class:`qt4c.mouse.Mouse` 进行使用。

--------
鼠标移动
--------
在Mouse类封装了move、sendMove、PostMove等方法，可以对鼠标进行移动操作。使用参考如下::

    from qt4c.mouse import Mouse
    Mouse.move(650, 200)                    # 移动鼠标到(650, 200)位置
    Mouse.sendMove(0x7001B8, 650, 200)      #通过发消息的方式产生鼠标移动的操作

sendMove和PostMove是在目标窗口通过发消息的方式产生鼠标移动的操作，所以需要额外传入目标窗口句柄作为参数，具体使用请参照接口文档。

--------
鼠标点击
--------
在Mouse类封装了click、sendClick、PostClick等方法，可以对鼠标进行点击操作。使用参考如下::

    from qt4c.mouse import Mouse, MouseFlag, MouseClickType
    Mouse.click(650, 200, MouseFlag.LeftButton, MouseClickType.SingleClick) # 在(650, 200)位置点击鼠标左键

其中MouseFlag.LeftButton和MouseClickType.SingleClick分别用于控制点击的鼠标键类型和点击方式，更多类型请参考接口文档进行使用。

而sendClick和PostClick同样是在目标窗口通过发消息的方式产生鼠标点击的操作，所以需要额外传入目标窗口句柄作为参数，使用方式参照鼠标移动，除此之外，Mouse类还提供了缓慢点击等其他点击功能，具体使用请参照接口文档。

--------
鼠标拖拽
--------
在Mouse类封装了drag方法用于鼠标拖拽。使用参考如下::

    from qt4c.mouse import Mouse
    Mouse.drag(0, 0, 650, 200)     # 鼠标从(0, 0)拖拽到(650, 200)

--------
鼠标滚动
--------
在Mouse类封装了scroll方法用于鼠标滚动。使用参考如下::

    from qt4c.mouse import Mouse
    Mouse.scroll(False)          # 鼠标向后滚动

=========
键盘输入
=========
Keyboard类中提供了两种键盘输入方式，一种使用模拟键盘输入的方式，另外一种则是使用Windows消息的机制将字符串直接发送到窗口。

Keyboard类支持以下字符的输入：

1.特殊字符：^, +, %,  {, }

    * '^'表示Control键，同'{CTRL}'。'+'表示Shift键，同'{SHIFT}'。'%'表示Alt键，同'{ALT}'。

    * '^', '+', '%'可以单独或同时使用，如'^a'表示CTRL+a，’^%a'表示CTRL+ALT+a。

    * {}： 大括号用来输入特殊字符本身和虚键，如‘{+}’输入加号，'{F1}'输入F1虚键，'{}}'表示输入'}'字符。 

2、ASCII字符：除了特殊字符需要｛｝来转义，其他ASCII码字符直接输入，

3、Unicode字符：直接输入，如"测试"。

4、虚键：

    * {F1}, {F2},...{F12}

    * {Tab},{CAPS},{ESC},{BKSP},{HOME},{INSERT},{DEL},{END},{ENTER}

    * {PGUP},{PGDN},{LEFT},{RIGHT},{UP},{DOWN},{CTRL},{SHIFT},{ALT},{APPS}..

.. warning:: 当使用联合键时，请注意此类的问题：对于inputKeys('^W')和inputKeys('%w')，字母'w'的大小写产生的效果可能不一样

--------
键盘输入
--------

Keyboard类封装了inputKeys和postKeys方法用于键盘输入，使用方式如下::

    from qt4c.keyboard import Keyboard
    Keyboard.inputKeys("QT4C")              #模拟键盘输入"QT4C"
    Keyboard.postKeys(0x7001B8, "QT4C")     #将"QT4C"字符串以窗口消息的方式发送到指定win32窗口