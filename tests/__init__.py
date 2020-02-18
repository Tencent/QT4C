# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''单元测试
'''

import unittest
import os
import sys

test_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(test_dir))

def main():
    runner = unittest.TextTestRunner(verbosity=10 + sys.argv.count('-v'))
    suite = unittest.TestLoader().discover(test_dir,  pattern='test_*.py')
    raise SystemExit(not runner.run(suite).wasSuccessful())


if __name__ == '__main__':
    main()
