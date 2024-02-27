"""# -*- coding: utf-8 -*-"""
import os
import shutil


def create_new_folder(folder: str = "", name: str = "", *args) -> str:
    """
     создаем (подготавливаем) каталог для файлов
    """
    path = os.path.dirname(folder)
    path_for_result = (f"{path}/{name}")
    # проверяем, есть ли в каталоге указанная папка, если нет то создаём
    if not os.path.exists(path_for_result):
        os.mkdir(path_for_result)
        print("Directory ", path_for_result, " Created ")
    else:
        print("Directory ", path_for_result, " already exists")
    return path_for_result

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

