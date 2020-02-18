
# 整体架构

```
+------------------------+                            +-------------------+  
|   Stub/Test Interface  +<---------------------------+    +---------+    |    
+-----------+------------+                            |    |  Mouse  |    |
            ^                                         |    +---------+    |
            |                                         |                   |
  +---------+---------+                               |  +-------------+  |  
  |   Proxy Object    |                               |  |  Keyboard   |  |  
  +---------+---------+                               |  +-------------+  |  
            ^                                         |                   |  
            +-----------------------+                 |   +-----------+   | 
            |                       |                 |   |  Message  |   |  
      +-----+-----+           +-----+----+            |   +-----------+   |    
      |  Control  +           +  Window  |            |       Input       |
      +-----------+           +----------+            +-------------------+
         


```
QT4C中所有的控件类型都可以抽象为Control，每一种控件类型都继承自qt4c.control.Control类，Control封装了Proxy Object，通过Proxy Object可以获取应用程序的属性或者进行操作。而Proxy Object中基于注入测试桩或调用被测程序提供的API来封装获取属性或操作的接口。Window则是特殊的Control，它既是Control的载体，也能够调用Proxy Object中封装的方法来进行操作。

同时QT4C还提供了对应用程序的输入，包括了鼠标操作、键盘操作以及消息传递，这些都是通过调用测试桩或被测程序提供的API来进行实现的。

# QT4C框架原理

QT4C中支持Windows Native控件、Web控件、UIA控件、和Web控件，对于不同控件，QT4C利用了不同的实现来对Win32应用获取属性并进行操作。

| 控件类型             | 技术实现          |  技术原理                          |
| ------------------  | -----            | ----    |
| Windows Native控件     | 基于pywin32库        | 通过调用Windows API来对应用进行操作 |
| UIA控件      | 基于UIAutomation技术     | 调用UIAutomationCore.dll库，调用UIA来对应用进行操作 |
| Web控件              | 基于QT4W          | 参考[QT4W文档](https://qt4w.readthedocs.io/zh_CN/latest/intro.html) |


# 实现方案

在QT4C中，每一种控件类型都继承自qt4c.control.Control类，每一个控件类分别实现封装各自的接口。同时，每一个类型对应的的Window类也都继承自各自的Control类和qt4c.control.ControlContainer类。

在每一个控件类中，最主要的差异在于初始化函数，分别用于初始化各自的Proxy Object。关于每种控件类型的实现方案，可参考对应的设计文档。

## [Native控件设计文档](./wincontrol.md)

## [UIA控件设计文档](./uiacontrol.md)