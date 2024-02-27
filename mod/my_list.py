"""# -*- coding: utf-8 -*-"""
import typing
from typing import Iterator, Tuple, List, Union
def get_fcs_from_polygon(
        pts_boundary: List[Tuple[float, float]],
        start_vrts_numeration: int = 1
        ) -> Union[List[int], List[int], List[Tuple[float, float]]]:
    """     на основании последовательных точек полигона получаем нумерацию индексов для faces
    pts_boundary        -  точки внешней границы полигона
    start_pos           -  начальная позиция для нумерации faceses, у *.obj файлов нумерация с единицы
                           у других плагинов и программ нумерация с нуля
    """
    start_pos = start_vrts_numeration  # начальная позиция нумерации vertex, у obj файлов с единицы!!!
    fcs_button = [x for x in range(start_pos, len(pts_boundary) + start_pos)]
    fcs_top = [x + len(pts_boundary) for x in range(start_pos, len(pts_boundary) + start_pos)]
    fcs_aa = fcs_button
    fcs_ab = fcs_aa[1:] + fcs_aa[:1]
    fcs_ac = fcs_top
    fcs_ad = fcs_ac[1:] + fcs_ac[:1]
    fcs_outside = list(tuple(zip(fcs_aa, fcs_ab, fcs_ad, fcs_ac)))
    return (fcs_button, fcs_top, fcs_outside)
