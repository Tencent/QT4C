.. _app_struct:

封装App
=======

=========
App类概述
=========
App类是QT4C中的应用程序基类模块，它可以理解为提供一个特定功能的软件，一般来说可能是对应操作系统的一个进程、一个线程、或者多个进程集合。App类提供了Windows上应用程序的部分相关功能，包括退出程序、退出所有应用程序等等。

=========
App类封装
=========
App基类中维护了一个记录所有打开的应用程序的列表，并且提供了一些静态方法来对当前记录的所有应用程序进行操作，如App.quitAll()退出所有应用程序，更多使用方法可查看 :class:`qt4c.app.App` 进行查看。

我们以Windows系统自带的计算器为例，你可以在demolib/calcapp.py封装你的测试基类CalcApp，实现App类所需的基本功能，用法参考如下::

    # -*- coding: utf-8 -*-

    from qt4c.app import App
    import subprocess, time

    class CalcApp(App):
        '''计算器App
        '''
        def __init__(self):
            App.__init__(self)
            self._process = subprocess.Popen('calc.exe')

        def quit(self):
            self._process.kill()
            App.quit(self)


上述代码实现了最基本的功能，你可以根据需要去定义更多的接口。__init__函数中需要实现应用程序的启动，这里我们通过subprocess启动一个calc.exe的子进程并获取其pid。而quit函数中需要实现程序退出。

.. warning:: 重载quit函数时，必须显示调用基类的函数,以通知基类该程序退出。

===================
App类自定义接口
===================
可能上面demo实现的基本功能无法满足你的需求，你可以自定义一些操作,然后自行实现。例如我们希望在实例化App之后直接调用App进行计算，那么可以修改如下::

    # -*- coding: utf-8 -*-
    from qt4c.app import App
    import subprocess, time

    
    class CalcApp(App):
        '''计算器App
        '''

        def __init__(self, cmd, params=[]):
            App.__init__(self)
            params.insert(0, cmd)
            self._process = subprocess.Popen(params)
        
        @property
        def ProcessId(self):
            return self._process.pid

        def quit(self):
            self._process.kill()
            App.quit(self) 

        def calculate(self, expression, expect_value):
            '''计算表达式并比较运算结果
            '''
            pass

之后我们可以通过调用calculate方法来直接进行计算::

    calcapp = CalcApp('calc.exe')
    calcapp.calculate('3*3', 9)


=========
App类使用
=========
在测试用例中，实例化一个被测应用程序,参考如下::

    from demolib.calcapp import CalcApp
    calc = CalcApp()

实例化之后，我们就可以看到一个计算器进程被启动。