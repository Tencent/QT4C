# -*- coding: UTF-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

'''IWebWiew接口定义及Windows平台上的实现
'''

import sys, logging
fmt = logging.Formatter('%(asctime)s %(thread)d %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fmt)
logging.root.addHandler(handler)
