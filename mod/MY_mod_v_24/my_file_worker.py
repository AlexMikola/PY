"""# -*- coding: utf-8 -*-"""
import numpy as np
import os
import pathlib
import typing
from typing import Iterator, Tuple, List, Union, Any

class FileFunc:

    @staticmethod
    def save_list_Str_to_file(
            dt: List[str],
            file_name: str = "",
            rlt_path: str = "") -> None:
        """     запись листа строковых значений в файл построчно
        dt          -  сам список строк для записи
        file_name   -  название файла с расширением
        rlt_path   -  куда сохраняем, путь
        """
        # если название файла и пути нет то задаём умолчание
        if file_name == "" and rlt_path == "":
            f_name = "file_from_py.obj"
            full_path = os.path.join(pathlib.Path().resolve(), f_name)
        elif file_name != "" and rlt_path != "":
            full_path = os.path.join(rlt_path, file_name)
        elif rlt_path == "":
            full_path = os.path.join(pathlib.Path().resolve(), file_name)
        elif file_name == "":
            full_path = os.path.join(rlt_path, file_name)

        try:
            with open(f"{full_path}", "w") as file:
                file.writelines(dt)

        except FileNotFoundError:
            print("Невозможно открыть файл")

    @staticmethod
    def open_file(f_path: str) -> list:
        """     чтение файла по пути - возвращает функция лист строк
        f_path      -  откуда читаем файл, путь с названием файла и расширением
        """
        if f_path == "":
            print("Путь к файлу указан не корректно!")
            raise

        try:
            with open(f"{f_path}", mode="r", encoding="utf-8") as file:
                s = file.readlines()
        except FileNotFoundError:
            print("Невозможно открыть файл")
        return s

    @staticmethod
    def is_file_exist(f_path: str) -> Any:
        if not os.path.isfile(f_path):
            return False
        return True

    @staticmethod
    def is_extension_true(f_path: str, ext: str):
        file_name, file_extension = os.path.splitext(f_path)
        if file_extension != ext:
            return False
        return True


