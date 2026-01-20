# -*- coding: utf-8 -*-
# !/usr/bin/env python
"""
-------------------------------------------------
   File     : config_getter.py
   Author   : CoderPig
   date     : 2020-11-26 17:18 
   Desc     : 获取配置信息
-------------------------------------------------
"""
import configparser
import os
import os.path


def get_config(section, key, fallback=None):
    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.split(os.path.realpath(__file__))[0], 'config.ini'), encoding='utf8')
    if fallback is not None:
        return config.get(section, key, fallback=fallback)
    return config.get(section, key)
