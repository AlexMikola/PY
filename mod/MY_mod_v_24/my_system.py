import os
import sys


# from PyQt5.QtCore import *
# from PyQt5.QtGui import *
# from qgis.core import *
# from qgis.gui import *
# from qgis.utils import iface
# from qgis.core import Qgis
# from qgis.core import QgsVectorLayerJoinInfo

# layer = iface.activeLayer()
# iter = layer.getFeatures()

import platform
import site
import pkg_resources
import builtins

# PLATFORM  ----------------------------------------------------------------------------------------------------------
platform.architecture()             # ('64bit', 'WindowsPE')
platform.machine()                  #  'AMD64'
platform.node()                     #  'DolgushinAN'
platform.platform()                 #  'Windows-10-10.0.19041-SP0'
platform.version()                  #  '10.0.19041'
platform.system()                   #  'Windows'                                            # имя операционной системы
platform.release()                  #  '10'                                                     # выпуск системы
platform.processor()                #  'Intel64 Family 6 Model 85 Stepping 7, GenuineIntel'     # что за процессор
platform.python_build()             #   ('v3.7.0:1bf9cc5093', 'Jun 27 2018 04:59:51')           # сборка винды
platform.python_compiler()          #  'MSC v.1914 64 bit (AMD64)'                              # компилятор python
platform.python_branch()            #  'v3.7.0'                                                 # версия питона
platform.python_version()           #  'v3.7.0'                                                 # версия питона
platform.python_version_tuple()     #  ('3', '7', '0')                                          # версия питона
platform.python_implementation()    #  'CPython'                                                # реализация питона
platform.python_revision()          #   '1bf9cc5093'                                            # SCM реализация Python
platform.uname()                    #                                           # куча инфы одной строкой
platform.version()

# SITE  ----------------------------------------------------------------------------------------------------------
site.PREFIXES                       # ['C:\\OSGEO4~1\\apps\\Python37', 'C:\\OSGEO4~1\\apps\\Python37']# Список префиксов

# путь к пользовательским пакетам
site.USER_SITE                      # 'C:\\Users\\dolgushin_an\\AppData\\Roaming\\Python\\Python37\\site-packages'

# путь к базовому каталогу для пользовательских сайтов-пакетов
site.USER_BASE                      # 'C:\\Users\\dolgushin_an\\AppData\\Roaming\\Python'

site.addsitedir(sitedir, known_paths=None)    # Добавьте каталог в sys.path и обработайте его .pth файлы.
site.getsitepackages()                        # Вернуть список, содержащий все глобальные каталоги пакетов сайтов.
site.getuserbase()                            # Возвращает путь базовой директории пользователя
site.getusersitepackages()                    # Возвращает путь к пользователю определенного каталога сайтов-пакеты

# pkg_resources  -------------------------------------------------------------------------------------------------
pkg_resources.get_build_platform()      #   'win-amd64'
pkg_resources.get_default_cache()       #  'C:\\Users\\dolgushin_an\\AppData\\Local\\Python-Eggs\\Python-Eggs\\Cache'
pkg_resources.get_platform()            #   'win-amd64'
pkg_resources.get_supported_platform()  #   'win-amd64'








print('asdf')