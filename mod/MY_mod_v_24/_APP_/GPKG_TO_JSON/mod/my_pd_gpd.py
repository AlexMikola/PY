"""# -*- coding: utf-8 -*-"""
import pandas as pd
import geopandas as gpd
from geopandas import geodataframe
import geojson

import fiona
from fiona import *


from shapely import speedups
speedups.disable()

class Func_GeoPandas_Pandas:

    @staticmethod
    def pandas_to_geopandas(pd: pd.core.frame.DataFrame) -> gpd.geodataframe.GeoDataFrame:
        '''
        перегоняем pandas dataframe в geodataframe
        '''
        geo_pdf = gpd.GeoDataFrame(pd)
        return geo_pdf

    @staticmethod
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

    @staticmethod
    def chek_and_set_name_index_column(gdf_src: geodataframe):
        """
        проверяем имя колонки индексации, если имя пустое то присваиваем значение
        """
        if gdf_src.index.name == None:
            gdf_src.index.name = "indx_col"

        return gdf_src


    @staticmethod
    def gdf_filter_by_column_val(gdf_src: geodataframe, clm_name: str = "", clm_val: str = "") -> geodataframe:
        """
        функция возвращает geodataframe отфильтрованный по значению из колонки
        gdf_src     -  источник GeoDataFrame
        clm_name    -  название колонки по которой собираем уникальные значения фрэйма
        clm_val     -  искомое значение в колонке
        """
        if clm_name == "":
            print(" ERROR - !!!!Введите имя колонки по которой фильтруем!!!")
            raise

        if clm_val == "":
            print(" ERROR - !!!!Введите значение в колонки по которой фильтруем!!!")
            raise

        gdf = gdf_src.loc[gdf_src[clm_name] == clm_val]

        return gdf


    @staticmethod
    def add_new_unic_column(gdf_src: geodataframe, clm_name: str = ""):
        """
        добавляем уникальную колонку в gdf
        """
        if clm_name == "":
            clm_name = "indx_col"

        # создаём уникальное значение колонки
        i = 0
        while clm_name in list(gdf_src.columns):
            clm_name = f"_{i + 1}_{clm_name}"

        # добавляем колонку к фрэйму и забиваем нулями
        gdf_src[clm_name] = 0

        return gdf_src, clm_name

    @staticmethod
    def get_list_columns_name(gdf_src):
        list_names = [x for x in gdf_src.keys()]
        return list_names

    @staticmethod
    def add_val_to_col_from_col_with_index(gdf_src: geodataframe, clm_name: str = ""):
        """
        обновляем полностью колонку значениями из колонки индексации
        """
        gdf_src[clm_name] = gdf_src.index

        gdf_src = gdf_src.copy()

        return gdf_src

    @staticmethod
    def reprojection_apu_wgs(f_path: str, fltr_lr: str):
        apu_src = r"+proj=tmerc +lat_0=55.66666666667 +lon_0=37.5 +k=1 +x_0=12 +y_0=14 +ellps=bessel +towgs84=316.151,78.924,589.65,-1.57273,2.69209,2.34693,8.4507 +units=m +no_defs"
        wgs = "EPSG:4326"
        val = 4326

        for layername in fiona.listlayers(f_path):
            if layername == fltr_lr:
                geopkg = gpd.read_file(f_path, layer=layername)
                gdf_wgs = geopkg.to_crs(wgs)

        return gdf_wgs


    @staticmethod
    def gdf_to_geojson(gdf_src: geodataframe, clm_name: str = ""):
        if clm_name == "":
            print(" ERROR - !!!!Введите имя колонки откуда брать названия для файлов!!!")
            raise
        # # экспортировали geojson в ПАПКУ С НАЗВАНИЕМ = ИМЕНИ ИСХОДНОГО ФАЙЛА MAPINFO !!!!
        # gdf_src.to_file(resust_path + '\excel' + '\\' + f_name + '\\' + f_name + '.geojson', driver='GeoJSON')

