# -*- coding: utf-8 -*-
'''
config
=======
'''


import configparser
import os

from typing import Any

from etc.patterns import PatternSingleton


class Config(dict, metaclass=PatternSingleton):

    def __init__(self) -> None:

        self.disable_attrs = []

        self.APP_NAME = 'ProcessWatcher'
        self.APP_ICON = 'res/ico.ico'
        self.DEVELOPER = 'GVCoder09 (https://github.com/GVCoder09/)'
        self.VERSION = '1.0'
        self.BUILDING = '24.06.30'
        self.DESCRIPTION = \
            f'''
WatchDog - ProcessMonitor

Program for monitoring processes. Only for Windows.

Author: {self.DEVELOPER}
Version: {self.VERSION}
'''
        self.SELF_PATH: str = None

        self.DATA_DIR: str = f'C:/Users/{
            os.getlogin()}/AppData/Local/ProcessWatcher'

        self.FILE_CONFIG: str = 'conf.ini'

        self.LOGGING: str = False
        self.DIR_LOGS: str = None

    def __setitem__(self, __key: Any, __value: Any) -> None:

        if __key in self.__dict__.keys() and __key not in self.disable_attrs:
            self.user_config_update(__key, __value)
            return self.__setattr__(__key, __value)

    def __getitem__(self, __key: Any) -> Any:

        return self.__getattribute__(__key)

    def user_config_create(self):

        config = configparser.ConfigParser()

        if not config.has_section('settings'):
            config.add_section('settings')

        config.set('settings', 'logging', 'False')

        with open(os.path.join(self.DATA_DIR, self.FILE_CONFIG), 'w', encoding='utf-8') as file:
            config.write(file)

    def user_config_load(self):

        config = configparser.ConfigParser()
        config.read(os.path.join(self.DATA_DIR, self.FILE_CONFIG))

        if config.has_section('settings'):
            for option, value in config.items('settings'):
                if value.lower() == 'true':
                    value = True
                elif value.lower() == 'false':
                    value = False
                elif value.isnumeric():
                    value = int(value)
                self[option.upper()] = value

    def user_config_update(self, key: str, value: Any):

        config = configparser.ConfigParser()
        config.read(os.path.join(self.DATA_DIR, self.FILE_CONFIG))

        if not config.has_section('settings'):
            config.add_section('settings')
        config.set('settings', key, str(value))

        with open(os.path.join(self.DATA_DIR, self.FILE_CONFIG), 'w', encoding='utf-8') as file:
            config.write(file)


CONFIG = Config()
