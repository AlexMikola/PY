"""# -*- coding: utf-8 -*-"""
import os, sys, tempfile
from datetime import datetime
import shutil


class FolderFunc:

    @staticmethod
    def create_new_folder(folder: str = "", name: str = "", *args) -> str:
        """
         создаем (подготавливаем) каталог для файлов
        """
        path = os.path.dirname(folder)
        path_for_result = (f"{path}\{name}")
        # проверяем, есть ли в каталоге указанная папка, если нет то создаём
        if not os.path.exists(path_for_result):
            os.mkdir(path_for_result)
            print("Directory ", path_for_result, " Created ")
        else:
            print("Directory ", path_for_result, " already exists")
        return path_for_result

    @staticmethod
    def clear_all_in_folder(path: str = "") -> None:
            """
            удаляем все в папке по указанному пути
            """
            for root, dirs, files in os.walk(path):
                for f in files:
                    # print(os.path.join(root, f))
                    os.unlink(os.path.join(root, f))
                for d in dirs:
                    # print(os.path.join(root, d))
                    shutil.rmtree(os.path.join(root, d))

    @staticmethod
    def getPathAndNamesFilesInFolderByExtension(path_to_target_folder: str = '', extension: str = '.shp'):
        """получаем все пути к файлам из папки по расширению
        :param path_to_target_folder:  путь к целевому каталогу
        :param extension:              расширение файлов какое ищем? (по умолчанию(.shp)
        :return:                       картеж из списка путей и списка имен файлов
        """
        path_tab = []  # переменная для путей
        name_tab = []  # переменная для имен файлов
        for root, directories, filenames in os.walk(path_to_target_folder):
            for directory in directories:
                print(os.path.join(root, directory))
            for filename in filenames:
                if (str(filename)).lower().endswith(extension):
                    path_tab.append((os.path.join(root, filename).replace('\\', '//')))
                    name_tab.append((os.path.splitext(filename)[0]).replace('\\', '//'))
        return path_tab, name_tab

    @staticmethod
    def create_tmp_folder(f_path: str):
        # создали временный каталог для сохранения результатов svg файлов
        path_to_script_folder = os.path.dirname(f_path)
        tmpdirpath = tempfile.mkdtemp(dir=path_to_script_folder)
        print(f'Временный каталог создан по пути - {tmpdirpath}')

    @staticmethod
    def delite_tmp_folder(f_path: str):
        shutil.rmtree(f_path)  # функция удаляет каталог и все содержимое рекурсивно

    @staticmethod
    def create_folder_in_user_dir(dir_name: str = '*.blend_mrgp'):
        # создаём каталог по пути к каталогу пользователя windows
        home = os.path.expanduser('~')              # получаем путь к домашнему каталогу пользователя
        loc = os.path.join(home, dir_name)          # объединям в путь
        if not os.path.exists(loc):                 # если такого каталога не существует - создаём
            os.mkdir(loc)
        return loc


