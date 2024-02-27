"""# -*- coding: utf-8 -*-"""
import pandas as pd
import osgeo
from osgeo.ogr import DataSource
from osgeo import ogr

import geopandas as gpd

from shapely import speedups
speedups.disable()

def open_file_by_gdal(path_to_file: str = "") -> osgeo.ogr.DataSource:
    """
    открываем file GDAL - ом по пути
    получаем osgeo.ogr.DataSource в результате
    """
    ds = ogr.Open(path_to_file, 1)
    return ds

def filter_by_coordinate(
        name_granica: str,
        name_column: str,
        name_f_layer: str,
        nm_lr_for_flt: str,
        ds: osgeo.ogr.DataSource
                    ) -> osgeo.ogr.DataSource:
    """
    name_granica      -  название границы по которой фильтруем, должно быть уникальным
    name_column       -  название колонки в слое в котором уникальное название гранички
    name_f_layer      -  название слоя в котором лежит граничка по которой фильтруем
    nm_lr_for_flt     -  название слоя который фильтруем
    """
    if name_granica == "":
        print(f"Укажите название границы для фильтра, текущее значение не указано")
        raise

    layer_granica_obrezki = ds.GetLayerByName(name_f_layer)  # получили слой по которому будем фильтровать

    # отфильтравали по значению атрибута, по названию полигона получили его объект в фильтре (в слое)
    layer_granica_obrezki.SetAttributeFilter(f"{name_column} = %r" % name_granica)

    # получаем WKT координаты из отфильтрованной выборки
    for feature in layer_granica_obrezki:
        geom = feature.GetGeometryRef()
        wkt = geom.ExportToWkt()

    layer_for_filtr = ds.GetLayerByName(nm_lr_for_flt)  # получили слой который нужно фильтровать
    layer_for_filtr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))  # отфильтровали отфильтровали

    return layer_for_filtr


def save_lr_to_mem(lr: osgeo.ogr.Layer = "", name_layer: str = "") -> osgeo.ogr.DataSource:
    """ перегоняем слой в память
    lr                  -  слой ogr
    name_layer          -  имя создаваемого слоя в памяти
    """
    if name_layer == "":
        print(f"Укажите название слоя для сохранения, текущее значение не указано")
        raise

    driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
    ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
    driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

    # скопировали слои в память и разрешили перезаписать если потребутеся
    ds_mem.CopyLayer(lr, name_layer, ['OVERWRITE=YES'])
    return ds_mem

def save_ds_to_mem(ds: osgeo.ogr.DataSource) -> osgeo.ogr.DataSource:
    """ перегоняем слои в память
    ds                  -  ogr.DataSource
    name_layer          -  имя создаваемого слоя в памяти
    """
    if ds.GetLayerCount() == 0:
        print(f"Нет слоёв в данном DataSource")
        raise

    driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
    ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
    driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

    # скопировали слои в память и разрешили перезаписать если потребутеся
    for i in ds:
        ds_mem.CopyLayer(i, i.GetName(), ['OVERWRITE=YES'])
    return ds_mem

def save_Dict_With_Ds_To_Mem(dict_ds: dict) -> osgeo.ogr.DataSource:
    """ сливаем в память в один DataSource словарь с DataSources
    dict_ds             -  dict - словарь с DataSources
    """
    if len(dict_ds.keys()) == 0:
        print(f"Нет данных в данном словаре")
        raise

    driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
    ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
    driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

    # скопировали слои в память и разрешили перезаписать если потребутеся
    for key, val in dict_ds.items():
        ds_mem.CopyLayer(val, val.GetName(), ['OVERWRITE=YES'])
    return ds_mem

def ds_or_lr_to_dataframe(db: osgeo.ogr.DataSource) -> dict:
    '''
    перегоняем DataSource в dict с pandas dataframes с инфой по колонкам и семантике [FEATURE, COL]
    - если слой в DataSource один, то получим один DataFrame
    - если слоёв в DataSource несколько, то получим словарь c DataFrames
    '''

    # условие по количеству слоев в базе и перечню обязательных слоёв к открытию
    if isinstance(db, osgeo.ogr.Layer):
        layer = db                                  # открываем слой из базы
        l_name = layer.GetName()                    # получаем имя слоя
        l_dfn = layer.GetLayerDefn()                # получаем конструктор слоя
        col_count = l_dfn.GetFieldCount()           # количиство колонок в слое
        feature_count = layer.GetFeatureCount()     # количиство строк в слое

        # словарь свойств колонок
        dic_col = {
            l_dfn.GetFieldDefn(x).GetName():  # ключи словаря как названия колонок
                {
                    'col_type': l_dfn.GetFieldDefn(x).GetType(),
                    'col_name_type': l_dfn.GetFieldDefn(x).GetFieldTypeName(l_dfn.GetFieldDefn(x).GetType()),
                    'col_size': l_dfn.GetFieldDefn(x).GetWidth(),
                    'col_precision': l_dfn.GetFieldDefn(x).GetPrecision()
                }
            for x in range(col_count)
        }

        # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ - ОТЛИЧНО СМОТРИТСЯ !!!!!!!!!
        df_col = pd.DataFrame.from_dict(dic_col, orient='index')  # фрэйм из колонок и их свойств

        # словарь значений колонок
        dic_feature = {
            x.GetFID():  # загоняем ROWID из слоя в ключ словаря
                {**x.items(), **{'geometry': x.geometry().ExportToWkt()}}  # объединяем два словаря
            for x in layer
        }

        # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ - ОТЛИЧНО СМОТРИТСЯ !!!!!!!!!
        df_feature = pd.DataFrame.from_dict(dic_feature,
                                            orient='index')  # фрэйм из объектов (строк) семнтики + geom

        # первый выход из функции, если только один слой в источнике данных и нет других условий
        return {"FEATURE": df_feature, "COL": df_col}

    # условие по количеству слоев в источнике данных и перечню обязательных слоёв к открытию
    if db.GetLayerCount() > 1:
        all_data = {}
        for layer in db:
            l_name = layer.GetName()  # получаем имя слоя
            l_dfn = layer.GetLayerDefn()  # получаем конструктор слоя
            col_count = l_dfn.GetFieldCount()  # количиство колонок в слое
            feature_count = layer.GetFeatureCount()  # количиство строк в слое

            # словарь свойств колонок
            dic_col = {
                l_dfn.GetFieldDefn(x).GetName():  # ключи словаря как названия колонок
                    {
                        'col_type': l_dfn.GetFieldDefn(x).GetType(),
                        'col_name_type': l_dfn.GetFieldDefn(x).GetFieldTypeName(l_dfn.GetFieldDefn(x).GetType()),
                        'col_size': l_dfn.GetFieldDefn(x).GetWidth(),
                        'col_precision': l_dfn.GetFieldDefn(x).GetPrecision()
                    }
                for x in range(col_count)
            }

            # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ - ОТЛИЧНО СМОТРИТСЯ !!!!!!!!!
            df_col = pd.DataFrame.from_dict(dic_col, orient='index')  # фрэйм из колонок и их свойств

            # словарь значений колонок
            dic_feature = {
                x.GetFID():  # загоняем ROWID из слоя в ключ словаря
                    {**x.items(), **{'geometry': x.geometry().ExportToWkt()}}  # объединяем два словаря
                for x in layer
            }

            # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ - ОТЛИЧНО СМОТРИТСЯ !!!!!!!!!
            df_feature = pd.DataFrame.from_dict(dic_feature,
                                                orient='index')  # фрэйм из объектов (строк) семнтики + geom

            all_data[l_name] = {"FEATURE": df_feature, "COL": df_col}
        return all_data

def lr_to_dataframe(lr: osgeo.ogr.Layer) -> pd.core.frame.DataFrame:
    '''
    перегоняем слой в pandas dataframes с инфой по семантике
    '''
    if isinstance(lr, osgeo.ogr.Layer)!=True:
        print(" ERROR - !!!!Полученные данные не являются слоем gdal.ogr")
        raise

    # условие по количеству слоев в базе и перечню обязательных слоёв к открытию
    if isinstance(lr, osgeo.ogr.Layer):
        layer = lr  # открываем слой из базы
        l_name = layer.GetName()  # получаем имя слоя
        l_dfn = layer.GetLayerDefn()  # получаем конструктор слоя
        col_count = l_dfn.GetFieldCount()  # количиство колонок в слое
        feature_count = layer.GetFeatureCount()  # количиство строк в слое

        # словарь значений колонок
        dic_feature = {
            x.GetFID():  # загоняем ROWID из слоя в ключ словаря
                {**x.items(), **{'geometry': x.geometry().ExportToWkt()}}  # объединяем два словаря
            for x in layer
        }

        # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ - ОТЛИЧНО СМОТРИТСЯ !!!!!!!!!
        df_feature = pd.DataFrame.from_dict(dic_feature,
                                            orient='index')  # фрэйм из объектов (строк) семнтики + geom

        # первый выход из функции, если только один слой в источнике данных и нет других условий
        return df_feature


def pandas_to_geopandas(pd: pd.core.frame.DataFrame) -> gpd.geodataframe.GeoDataFrame:
    '''
    перегоняем pandas dataframe в geodataframe
    '''
    geo_pdf = gpd.GeoDataFrame(pd)
    return geo_pdf
