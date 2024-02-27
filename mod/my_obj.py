import typing
from typing import Iterator, Tuple, List, Union
import numpy as np
from ..mod import my_file_worker as mf         # функции для работы с файлами (открыть, записать)
from ..mod import my_numpy as mnp              # функции для работы с numpy
from ..mod import my_list as ml                # функции для работы с листами

def create_obj_from_simple_polygon(pts: list, type_obj: str, name_obj: str, idx: int, f_path: str) -> None:
    """     функция создаёт и сохраняет obj файл на основании простого полигона
    pts         -  точки (последовательные) в порядке создания полигона !!!
    type_obj    -  тип объекта, будет указан в названии файла (базовый полигон или отверстие) 'base', 'hole'
    name_obj    -  название объекта по семантике, типа NZH_1_3
    idx         -  индекс объекта, уникальные по семантике fid из gpkg
    f_path      -  путь, куда сохранять объект
    """
    pts_zero = mnp.add_coll_to_arr_from_right_side(pts)
    pts_z_hm = mnp.get_copy_arr_and_set_z_coord(pts_zero, float(name_obj.split('_')[2]))
    pts_full = np.concatenate((pts_zero, pts_z_hm), axis=0)
    # x = pts_full[:, 0]
    # y = pts_full[:, 1]
    # z = pts_full[:, 2]
    pts_full = (np.vstack([pts_full[:, 0], pts_full[:, 2], pts_full[:, 1]])).T
    list_str_pts_full = ['v ' + ' '.join([str(x) for x in y]) + "\n" for y in pts_full.tolist()]
    # FACES
    fcs_button, fcs_top, fcs_side = ml.get_fcs_from_polygon(pts)
    str_button = 'f ' + ' '.join(str(x) for x in fcs_button) + "\n"
    str_top = 'f ' + ' '.join(str(x) for x in fcs_top) + "\n"
    list_str_side = ['f ' + ' '.join([str(x) for x in y]) + "\n" for y in fcs_side]
    # UNION TO EXPORT все в лист строк для экспорта в *.obj формат
    list_to_obj = []
    list_to_obj.append(f'o {name_obj}_fid_{idx}\n')
    [list_to_obj.append(x) for x in list_str_pts_full]
    list_to_obj.append(f's off\n')
    list_to_obj.append(str_button)
    list_to_obj.append(str_top)
    [list_to_obj.append(x) for x in list_str_side]
    # запись в файл
    file_name = f"{type_obj}_{idx}.obj"
    dt = list_to_obj
    mf.save_list_Str_to_file(dt=dt, file_name=file_name, rlt_path=f_path)
    return None