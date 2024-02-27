"""# -*- coding: utf-8 -*-"""
import typing
from typing import Iterator, Tuple, List, Union, Any
import numpy as np
from ..mod import my_list as ml     # функции работы с листами

def add_coll_to_arr_from_right_side(np_arr: List[Tuple[float, float]]) -> np.ndarray:
    """     добавляем колонку к текущем массиву справа и забиваем нулями
    np_arr      -  массив numpy
    """
    if np_arr == "":
        print("Не передан в функцию массив numpy")
        raise
    zero = np.pad(np_arr, [(0, 0), (0, 1)])
    return zero

def get_copy_arr_and_set_z_coord(np_arr: np.ndarray, h_z: float) -> np.ndarray:
    """     возвращает копию Numpy массива и меняет значения в третьей колонке на указанное
    np_arr      -  массив numpy
    h_z         -  значения заносимое в третий столбик входящего массива
    """
    if np_arr == "":
        print("Не передан в функцию массив numpy")
        raise
    pts_z = np_arr.copy()
    pts_z[:, 2] = h_z
    return pts_z

def get_vrts_and_fcs_from_simple_poly(pts: List[Tuple[float, float]], h_obj: float) -> list:
    """     функция возвращает список точек и faces
    pts         -  точки (последовательные) в порядке создания полигона !!!
    h_obj       -  высота объекта, на сколько поднимать точки верхнего полигона
    """
    pts_zero = add_coll_to_arr_from_right_side(pts)
    pts_z_hm = get_copy_arr_and_set_z_coord(pts_zero, h_obj)
    pts_full = np.concatenate((pts_zero, pts_z_hm), axis=0)
    x = pts_full[:, 0]
    y = pts_full[:, 1]
    z = pts_full[:, 2]
    pts_full = (np.vstack([x, y, z])).T
    # list_str_pts_full = ['v ' + ' '.join([str(x) for x in y]) + "\n" for y in pts_full.tolist()]
    # FACES
    fcs_button, fcs_top, fcs_side = ml.get_fcs_from_polygon(pts, start_vrts_numeration=0)
    list_vrts_fcs = []
    list_vrts_fcs.append(pts_full)
    list_vrts_fcs.append(fcs_button)
    list_vrts_fcs.append(fcs_top)
    [list_vrts_fcs.append(x) for x in fcs_side]
    return [list_vrts_fcs[0], list_vrts_fcs[1:]]
