"""# -*- coding: utf-8 -*-"""
import pandas as pd
import geopandas as gpd
from geopandas import geodataframe

from shapely import speedups
speedups.disable()


def pandas_to_geopandas(pd: pd.core.frame.DataFrame) -> gpd.geodataframe.GeoDataFrame:
    '''
    перегоняем pandas dataframe в geodataframe
    '''
    geo_pdf = gpd.GeoDataFrame(pd)
    return geo_pdf


def split_gdf_by_unic_val_colum(gdf_src: geodataframe, clm_name: str = "") -> dict:
    """
    функция возвращает словарь фрэймов из фрэйма на основании уникальных знаений одной колонки
    clm_name    -  название колонки по которой собираем уникальные значения фрэйма
    gdf_source  -  источник, GeoDataFrame который нужно разделить по уникальным значениям
    """
    if clm_name == "":
        print(" ERROR - !!!!Введите значение колонки по которой фильтруем!!!")
        raise

    unic_list_contents = set([p for p in gdf_src[clm_name]])

    dic_gdf = {}
    for x in unic_list_contents:
        dic_gdf[x] = gdf_src.loc[gdf_src[clm_name] == x]

    return dic_gdf