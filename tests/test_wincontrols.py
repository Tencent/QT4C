# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''Win32 Control模块单元测试
'''

import unittest
try:
    from unittest import mock
except:
    import mock

from qt4c.wincontrols import Control
from qt4c.util import Rectangle

class ControlTest(unittest.TestCase):
    '''Control类单元测试
    '''
    @mock.patch('win32gui.GetWindowRect', return_value=(0, 0, 100, 200))
    def test_boundingrect(self, mockGetWindowRect):
        control = Control()
        self.assertEqual(control.BoundingRect, Rectangle((0, 0, 100, 200)))

    @mock.patch('win32gui.GetClassName', return_value='desktop')
    def test_classname(self, mockGetClassName):
        control = Control()
        self.assertEqual(control.ClassName, 'desktop')

    @mock.patch('win32gui.GetDlgCtrlID', return_value=0x50)
    def test_controlid(self, mockGetDLGCtrlID):
        control = Control()
        self.assertEqual(control.ControlId, 0x50)

    @mock.patch('win32gui.GetWindowLong', return_value=0x80)
    def test_exstyle(self, mockGetWindowLong):
        control = Control()
        self.assertEqual(control.ExStyle, 0x80)

    @mock.patch('win32gui.IsWindowEnabled', return_value=1)
    def test_enabled(self, mockIsWindowEnabled):
        control = Control()
        self.assertEqual(control.Enabled, True)

    @mock.patch('win32process.GetWindowThreadProcessId', return_value=[800, 4])
    def test_processid(self, mockGetWindowThreadProcessId):
        control = Control()
        self.assertEqual(control.ProcessId, 4)

    @mock.patch('win32process.GetWindowThreadProcessId', return_value=[800, 4])
    def test_threadid(self, mockGetWindowThreadProcessId):
        control = Control()
        self.assertEqual(control.ThreadId, 800)

    @mock.patch('win32gui.GetWindowLong', return_value=0x96000000)
    def test_style(self, mockGetWindowLong):
        control = Control()
        self.assertEqual(control.Style, 0x96000000)

    @mock.patch('win32gui.IsWindow', return_value=1)
    def test_valid(self, mockIsWindow):
        control = Control()
        self.assertEqual(control.Valid, True)

    @mock.patch('win32gui.IsWindowVisible', return_value=1)
    def test_visible(self, mockIsWindowVisible):
        control = Control()
        self.assertEqual(control.Visible, True)

    def test_rect(self):
        with mock.patch.object(Control, 'BoundingRect') as mock_rect:
            mock_rect.__get__ = mock.Mock(return_value=Rectangle((0, 0, 150, 100)))
            control = Control()
            self.assertEqual(control.Width, 150)
            self.assertEqual(control.Height, 100)


if __name__ == '__main__':
    unittest.main()
