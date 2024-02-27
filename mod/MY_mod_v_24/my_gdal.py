"""# -*- coding: utf-8 -*-"""
import typing
from typing import List, Tuple, Dict, Union

import pandas as pd

import geopandas as gpd

import osgeo
from osgeo.ogr import DataSource
from osgeo import ogr

import shapely as sh
from shapely.geometry import  MultiLineString, mapping, shape
from shapely.ops import transform as tr
import pyproj

import fiona
from fiona import *

from shapely import speedups
speedups.disable()

class GdalFunc:
    bl_label = 'GIS_Function'
    bl_idname = 'gis.gis_op'

    lst_src_layer = {
        "bld_pr": 'total_building_pr',
        "lnd_pr": 'total_a_landscaping_pr',
        "road_s": 'ROAD_POLY',
        "bld_s": 'BUILDING',
        "tr": 'total_terr_razvitie',
        "ld": 'ld_region'}                           # словарь слоёв с которыми работаем
    str_layer_grn = 'GRANICA_OBREZKI'               # слой в котором граничка лежит
    col_filtr_name = "GR_OBREZKI"                   # название колонки для фильтрации в слое где граничка обрезки
    col_split_name = "t_from_contents"              # название колонки для фильтрации по слоям

    def get_list_layers_gpkg_fiona(self, f_path):
        """
        получаем список слоёв при помощи фиона fiona
        """
        return fiona.listlayers(f_path)

    @staticmethod
    def open_gpkg_with_fiona(f_path):
        for layername in fiona.listlayers(f_path):
            with fiona.open(f_path, layer=layername) as src:
                print(layername, len(src))



    @staticmethod
    def open_file_by_gdal(path_to_file: str = "") -> osgeo.ogr.DataSource:
        """
        открываем file GDAL - ом по пути
        получаем osgeo.ogr.DataSource в результате
        """
        ds = ogr.Open(path_to_file, 1)
        return ds

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def pandas_to_geopandas(pd: pd.core.frame.DataFrame) -> gpd.geodataframe.GeoDataFrame:
        '''
        перегоняем pandas dataframe в geodataframe
        '''
        geo_pdf = gpd.GeoDataFrame(pd)
        return geo_pdf

    @staticmethod
    def get_list_all_layers_names(ds) -> Union[Tuple[List, List]]:
        l_names = [x.GetName() for x in ds]
        return l_names

    @staticmethod
    def get_all_type_lrs(ds):
        pass

    @staticmethod
    def get_all_lrs(ds) -> List:
        lrs = [x for x in ds]
        return lrs

    @staticmethod
    def get_lr_by_name(ds, lr_name) -> Union[Tuple[List, List]]:
        lr = [x for x in ds if x.GetName() == lr_name]
        return lr


    @staticmethod
    def get_dic_ds_filter(ds: osgeo.ogr.DataSource, gr_name: str = "", dic_lrs_names: dict = "",
                          lr_gr_obr: str = "", col_obr: str = "") -> dict:

        if gr_name == "":
            raise Exception(u"Введите имя объекта для получения границ установки фильтра")

        if dic_lrs_names == "":
            dic_lrs_names = GdalFunc.lst_src_layer  # словарь названий слоёв

        if lr_gr_obr == "":
            lr_gr_obr = GdalFunc.str_layer_grn   # СЛОЙ GRANICA_OBREZKI'

        if col_obr == "":
            col_obr = GdalFunc.col_filtr_name    # КОЛОНКА "GR_OBREZKI"

        # получаем словарь отфильтрованых datasource по каждому слою
        dct_ds = {}
        for i in dic_lrs_names.keys():
            dct_ds[i] = GdalFunc.filter_by_coordinate(
                name_granica=gr_name,
                name_column=col_obr,
                name_f_layer=lr_gr_obr,
                nm_lr_for_flt=dic_lrs_names[i],
                ds=ds
            )
        return dct_ds

    @staticmethod
    def from_dic_ds_to_mem(dic: dict = ""):
        if dic == "":
            print(f"словарь с ds пуст")
            raise Exception

        # сохраняем datasource gdal в оперативке (в словаре DataSources
        dct_ds_mem = {}  # словарь DataSource в памяти пк
        for i in dic.keys():
            dct_ds_mem[i] = GdalFunc.save_lr_to_mem(dic[i], i)

    @staticmethod
    def union_dic_ds(dct_ds: dict):
        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        ds_mem = GdalFunc.save_Dict_With_Ds_To_Mem(dct_ds)
        return ds_mem

    @staticmethod
    def lrs_from_mem_to_df(ds_mem):
        # перегоняем DataSource в DataFrame
        df_ds_buil = GdalFunc.lr_to_dataframe(ds_mem[0])  # bld_pr
        df_ds_land = GdalFunc.lr_to_dataframe(ds_mem[1])  # lnd_pr
        df_ds_road = GdalFunc.lr_to_dataframe(ds_mem[2])  # road_s
        df_ds_blds = GdalFunc.lr_to_dataframe(ds_mem[3])  # bld_s
        df_ds_tr = GdalFunc.lr_to_dataframe(ds_mem[4])  # tr
        df_ds_ld = GdalFunc.lr_to_dataframe(ds_mem[5])  # ld

        l_df = [df_ds_buil, df_ds_land, df_ds_road, df_ds_blds, df_ds_tr, df_ds_ld]

        return l_df

    @staticmethod
    def df_to_gdf(*args):
        # pandas Dataframe -> GeoPandas GeoDataFrame
        gdf_ds_buil = GdalFunc.pandas_to_geopandas(args[0])
        gdf_ds_land = GdalFunc.pandas_to_geopandas(args[1])
        gdf_ds_road_s = GdalFunc.pandas_to_geopandas(args[2])
        gdf_ds_bld_s = GdalFunc.pandas_to_geopandas(args[3])
        gdf_ds_tr = GdalFunc.pandas_to_geopandas(args[4])
        gdf_ds_ld = GdalFunc.pandas_to_geopandas(args[5])









