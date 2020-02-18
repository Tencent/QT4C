.. include:: ../links/link.ref

封装测试基类
============

============
测试基类概述
============

QTAF中实现的测试基类《|qtaf-testcase|_》提供了很多功能接口，如环境准备和清理、断言、日志相关等功能,详细见测试基类的相关说明。QT4C的测试基类ClientTestCase重载了QTAF中的测试基类TestCase，在TestCase的基础上复用了其功能并重写了部分方法。

============
测试基类封装
============

QT4C的测试基类 :class:`qt4c.testcase.ClientTestCase` 实现了部分Windows端运行测试用例所需功能。你可以在demolib/testcase.py封装你的测试基类DemoTestCase,并且根据测试项目的实际需要重载各个接口，用法参考如下::

    # -*- coding: utf-8 -*-
    '''示例测试用例
    '''

    from testbase import testcase
    from qt4c.testcase import ClientTestCase 

    class DemoTestCase(ClientTestCase):
        '''demo测试用例基类
        '''
        pass

============
测试基类使用
============
封装的测试基类DemoTestCase可以直接作为测试用例的基类使用，例如在demotest/hello.py使用如下::

    class HelloTest(DemoTestCase):