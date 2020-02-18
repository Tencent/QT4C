# -*- coding: utf-8 -*-
#
# Tencent is pleased to support the open source community by making QT4C available.  
# Copyright (C) 2020 THL A29 Limited, a Tencent company.  All rights reserved.
# QT4C is licensed under the BSD 3-Clause License, except for the third-party components listed below. 
# A copy of the BSD 3-Clause License is included in this file.
#

import os
from setuptools import setup, find_packages

BASE_DIR = os.path.realpath(os.path.dirname(__file__))
  
def generate_version():
    version = "1.0.0"
    if os.path.isfile(os.path.join(BASE_DIR, "version.txt")):
        with open("version.txt", "r") as fd:
            content = fd.read().strip()
            if content:
                version = content
    return version
  
def parse_requirements():
    reqs = []
    if os.path.isfile(os.path.join(BASE_DIR, "requirements.txt")):
        with open(os.path.join(BASE_DIR, "requirements.txt"), 'r') as fd:
            for line in fd.readlines():
                line = line.strip()
                if line:
                    reqs.append(line)
        return reqs

def get_description():
    with open(os.path.join(BASE_DIR, "README.md"), "rb") as fh:
        return fh.read().decode('utf8')


if __name__ == "__main__":
    setup(
      version=generate_version(),
      name="qt4c",
      packages=find_packages(exclude=("tests", "tests.*",)),
      include_package_data=True,
      package_data={'':['*.txt', '*.TXT'], },
      data_files=[(".", ["requirements.txt"])],
      description = "QTA test driver for Win32 application",
      long_description=get_description(),
      long_description_content_type="text/markdown",
      author="Tencent",
      license="Copyright(c)2010-2018 Tencent All Rights Reserved. ",
      install_requires=parse_requirements(),
      classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2.7",
        "Operating System :: Microsoft :: Windows",
      ],
    )
