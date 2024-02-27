import ezdxf
from ezdxf.addons.dxf2code import entities_to_code, block_to_code
from ezdxf.addons import iterdxf

from osgeo import ogr

import geopandas as gpd

import fiona

import shapely
from shapely import *
from shapely import wkb
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon
from shapely.geometry import LineString

import pandas as pd

import numpy as np

from geopandas import GeoSeries

from collections.abc import Iterable
import struct
import copy
import sys
import os
import re

class My_class:

    @staticmethod
    def open_file_by_gdal(path_to_file):
        """открываем file GDAL - ом по пути """
        ds = ogr.Open(path_to_file, 1)
        return ds

    @staticmethod
    def filter_by_coordinate(name_granica_obrezki, ds):
        """" фильтруем объекты слоев по одному объекту из таблицы
        (есть точное название объекта из которого получаем геометрию) """
        layer_granica_obrezki = ds.GetLayerByName('GRANICA_OBREZKI')  # получили слой по которому будем резать
        layer_building_pr = ds.GetLayerByName('total_building_pr')  # получили слой с проектируемой застройкой
        layer_landscaping_pr = ds.GetLayerByName('total_a_landscaping_pr')  # получили слой проектирумым landscaping

        layer_susch_building = ds.GetLayerByName('BUILDING')  # получили слой существующую застройку
        layer_susch_road = ds.GetLayerByName('ROAD_POLY')  # получили слой существующие дороги

        layer_TR = ds.GetLayerByName('total_terr_razvitie')  # получили слой TR
        layer_LD = ds.GetLayerByName('ld_region')  # получили слой LD

        # отфильтравали по значению атрибута, по названию полигона получили его объект в фильтре (в слое)
        layer_granica_obrezki.SetAttributeFilter("GR_OBREZKI = %r" % name_granica_obrezki)

        # получаем WKT координаты из отфильтрованной выборки
        for feature in layer_granica_obrezki:
            geom = feature.GetGeometryRef()
            wkt = geom.ExportToWkt()

        layer_TR.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))               # отфильтровали TR
        layer_LD.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))               # отфильтровали LD

        layer_building_pr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))      # отфильтровали застройку по полигону
        layer_landscaping_pr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))   # отфильтровали landscaping по полигону

        layer_susch_building.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))   # отфильтровали сущ застр по полигону
        layer_susch_road.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))       # отфильтровали сущ дороги по полигону

        return layer_building_pr, layer_landscaping_pr, layer_susch_building, layer_susch_road, layer_TR, layer_LD

    @staticmethod
    def save_to_mem(building_layer, lands_layer):
        """ перегоняем результаты фильтров в память """
        driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
        ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
        driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

        # скопировали слои в память и разрешили перезаписать если потребутеся
        ds_mem.CopyLayer(building_layer, 'Build_Polygon', ['OVERWRITE=YES'])
        ds_mem.CopyLayer(lands_layer, 'Lands_Polygon', ['OVERWRITE=YES'])
        return ds_mem

    @staticmethod
    def open_by_gdal_ogr(db, list_names_layer=''):
        # db = ogr.Open(path)  # загружаем данные в базу

        # условие по количеству слоев в базе и перечню обязательных слоёв к открытию
        if db.GetLayerCount() == 1 and list_names_layer == '':
            layer = db.GetLayer()  # открываем слой из базы
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

            # первый выход из функции, если только один слой в источнике данных и нет других условий
            return {"FEATURE": df_feature, "COL": df_col}

        # условие по количеству слоев в источнике данных и перечню обязательных слоёв к открытию
        if db.GetLayerCount() > 1 and list_names_layer == '':
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
    def createNewFolder(folder, name):
        # создаем (подготавливаем) каталог для файлов
        import os
        path = os.path.dirname(folder)
        path_for_result = (path + name)
        # проверяем, есть ли в каталоге указанная папка, если нет то создаём
        if not os.path.exists(path_for_result):
            os.mkdir(path_for_result)
            print("Directory ", path_for_result, " Created ")
        else:
            print("Directory ", path_for_result, " already exists")
        return path_for_result

    @staticmethod
    def clear_AllIn_Folder(path):
        # удаляем все в папке по указанному пути
        import os
        import shutil

        for root, dirs, files in os.walk(path):
            for f in files:
                # print(os.path.join(root, f))
                os.unlink(os.path.join(root, f))
            for d in dirs:
                # print(os.path.join(root, d))
                shutil.rmtree(os.path.join(root, d))

    @staticmethod
    def createDxf(path, nm_fl='Polygons', filtr_feature='t_from_contents', *args):

        #  ----   ИНИЦИИРУЕМ ЧЕРТЕЖ AUTOCAD    ----   ----   ----   ----   ----   ----

        doc = ezdxf.new('R2004')  # создали пустой чертеж
        msp = doc.modelspace()  # получили пространсвтов имен

        #  ----   КОНЕЦ БЛОКА ИНИЦИАЦИИ DXF    ----   ----   ----   ----   ----   ----

        # цикл по каждому элементу списка аргументов
        for i in args:
            if len(list(i.keys())) == 0: continue

            # создаём фрэйм только с выбранными колонками
            cur_gdf = i.loc[:, (filtr_feature, 'geometry')]

            l_ind = list(cur_gdf.index)
            # for j in range(cur_gdf.shape[0]):
            for j in l_ind:
                # print(cur_gdf['geometry'][j])

                #  получили геометрию первого объекта
                val = cur_gdf['geometry'][j]

                #  получили название слоя из строки объекта первого объекта
                name_layer_for_dxf = cur_gdf[filtr_feature][j]
                if str(cur_gdf[filtr_feature][j]) == "None":
                    name_layer_for_dxf = "free_obj"

                # # добавили новый слой в DXF
                # doc.layers.new(name_layer_for_dxf)

                #  проверка это полигон или мультиполигон (предварительно конвертируем из строки в полигон)
                val = shapely.wkt.loads(val)
                type_geom = val.type

                if type_geom == "MultiPolygon":
                    #  из мультиполигонов нужно создавать блоки
                    #  my_block = doc.blocks.new('MyBlock')

                    # подключаем регулярку для списка всех строк полигонов в координатах
                    shp = str(cur_gdf['geometry'][j])
                    # search_what = r"\(\((.*?)\)\)"
                    ''' 
                            \(     ищем круглую скобку
                            {2}    повторяется два раза
                            [^\(]  кроме круглой скобки
                            .*     любое количество любых символов
                            (.*?)  группировать
                    '''
                    # search_what = r"\({2}([^\(].*?)\){2}"
                    search_what = r"\({1}([^\(].*?)\){1}"
                    result = re.findall(search_what, shp)

                    # m_l.append(m.split(','))
                    # poly = shapely.geometry.Polygon([[p[0].x, p[0].y] for p in m_l[0]])

                    # получаем имя файла (MAP TAB) без расширения по пути
                    # f_name, f_ext = os.path.splitext(os.path.basename(i))

                    # Создали пустой блок с уникальным названием (ИМЯ ТАБЛИЦЫ МАП + НАЗВАНИЕ СТРОКИ + Порядк Номер)
                    name_for_block = str(name_layer_for_dxf) + "_N_" + str(j)
                    flag = doc.blocks.new(name=name_for_block)

                    for z in val.boundary:
                        # получаем картеж массивов координат XY
                        xy_tuple = z.coords.xy

                        # перегоняем массивы в картежи и загоняем в лист картежей
                        s_coord = []
                        for m in range(len(xy_tuple[0])):
                            tupl = (xy_tuple[0][m], xy_tuple[1][m])
                            s_coord.append(tupl)

                        # добавили полилинию в блок DXF
                        flag.add_lwpolyline(s_coord)
                        # flag.add_polyline2d(s_coord)

                    # получаем координаты центроида - тут Можем задать смещение относительно его собственных коорд
                    # tupl_centroid = (val.centroid.xy[0][0], val.centroid.xy[1][0])
                    tupl_centroid = (0, 0)

                    # добавили блок в пространство модели
                    msp.add_blockref(name_for_block, tupl_centroid, dxfattribs={
                        'layer': name_layer_for_dxf,
                        'xscale': 1,
                        'yscale': 1,
                        'rotation': 0})
                    # msp.add_blockref(flag, insert=(0.1, 0.1),dxfattribs={'xscale': 1, 'yscale': 1, 'rotation': 0})
                    # msp.add_auto_blockref(flag, dxfattribs={'xscale': 1, 'yscale': 1, 'rotation': 0})

                #  проверка это полигон или мультиполигон
                if type_geom == "Polygon":
                    # проверка - сколько границ в данном полигоне
                    try:
                        if len(val.boundary) > 1:
                            # получаем имя файла (MAP TAB) без расширения по пути
                            f_name, f_ext = os.path.splitext(os.path.basename(i))

                            # Создали пустой блок с уникальным названием (ИМЯ ТАБЛИЦЫ МАП + НАЗВАНИЕ СТРОКИ + Порядк Номер)
                            name_for_block = f_name + "_" + name_layer_for_dxf + "_N_" + str(j)
                            flag = doc.blocks.new(name=name_for_block)

                            for z in val.boundary:
                                # получаем картеж массивов координат XY
                                xy_tuple = z.coords.xy

                                # перегоняем массивы в картежи и загоняем в лист картежей
                                s_coord = []
                                for m in range(len(xy_tuple[0])):
                                    tupl = (xy_tuple[0][m], xy_tuple[1][m])
                                    s_coord.append(tupl)

                                # добавили полилинию в блок DXF
                                flag.add_lwpolyline(s_coord)
                                # flag.add_polyline2d(s_coord)

                            # получаем координаты центроида - тут Можем задать смещение относительно его собственных коорд
                            # tupl_centroid = (val.centroid.xy[0][0], val.centroid.xy[1][0])
                            tupl_centroid = (0, 0)

                            # добавили блок в пространство модели
                            msp.add_blockref(name_for_block, tupl_centroid, dxfattribs={
                                'layer': name_layer_for_dxf,
                                'xscale': 1,
                                'yscale': 1,
                                'rotation': 0})
                            # msp.add_blockref(flag, insert=(0.1, 0.1),dxfattribs={'xscale': 1, 'yscale': 1, 'rotation': 0})
                            # msp.add_auto_blockref(flag, dxfattribs={'xscale': 1, 'yscale': 1, 'rotation': 0})

                    except TypeError:
                        # получаем картеж массивов координат XY
                        xy_tuple = val.exterior.coords.xy

                        # перегоняем массивы в картежи и загоняем в лист картежей
                        s_coord = []
                        for m in range(len(xy_tuple[0])):
                            tupl = (xy_tuple[0][m], xy_tuple[1][m])
                            s_coord.append(tupl)

                        # добавили полилинию в чертеж DXF
                        msp.add_polyline2d(s_coord, dxfattribs={'layer': name_layer_for_dxf})
            # сохраняем чертёж
            name_file = '\\' + nm_fl
            path_to = (path)
            full_path = (path_to + name_file + '.dxf').replace('\\', '//')
            doc.saveas(full_path, encoding="Windows-1251")

            print('vvv')




# Главная функция
def mainFunction(path_gpkg, gr_obrezki):
    ds = My_class.open_file_by_gdal(path_gpkg)  # получаем в переменнюу GPKG

    # получаем в переменные выборки build, land, и сущ застройку с сущ дорогами
    build, land, s_build, s_road, layer_TR, layer_LD = My_class.filter_by_coordinate(gr_obrezki, ds)

    # datasourc GDAL с слоями build and lands
    tmp_ds = My_class.save_to_mem(build, land)  # сохраняем результаты в оперативку

    # datasourc GDAL с слоями существующие build и сущ road
    tmp_ds_s = My_class.save_to_mem(s_build, s_road)  # сохраняем результаты в оперативку

    # datasourc GDAL с слоями существующие TR и LD
    tmp_ds_ld_tr = My_class.save_to_mem(layer_TR, layer_LD)  # сохраняем результаты в оперативку

    # получаем словари со слоями в формате dataframe по каждому слою и инфой по полям слоя
    # т.е. перегоняем gdal -> dataframe
    data_set_first = My_class.open_by_gdal_ogr(tmp_ds)
    data_set_second = My_class.open_by_gdal_ogr(tmp_ds_s)
    data_set_third = My_class.open_by_gdal_ogr(tmp_ds_ld_tr)

    # создаем (подготавливаем) каталог для файлов
    result_path_dxf = (My_class.createNewFolder(path_gpkg, r'\DXF')).replace('\\', '//')

    # получаем объект GEODATAFRAME из DATAFRAME
    gdf_first_build_pr = gpd.GeoDataFrame(data_set_first['Build_Polygon']['FEATURE'])
    gdf_second_lands_pr = gpd.GeoDataFrame(data_set_first['Lands_Polygon']['FEATURE'])

    gdf_third_build_s = gpd.GeoDataFrame(data_set_second['Build_Polygon']['FEATURE'])
    gdf_fourth_road_s = gpd.GeoDataFrame(data_set_second['Lands_Polygon']['FEATURE'])

    gdf_third_build_TR = gpd.GeoDataFrame(data_set_third['Build_Polygon']['FEATURE'])
    gdf_third_build_LD = gpd.GeoDataFrame(data_set_third['Lands_Polygon']['FEATURE'])

    # очищаем целевой каталог
    b = My_class.clear_AllIn_Folder(result_path_dxf)

    # создаём dxf со слоями build_pr и land_pr
    My_class.createDxf(result_path_dxf, '01_project', 't_from_contents', gdf_first_build_pr, gdf_second_lands_pr)
    My_class.createDxf(result_path_dxf, '02_ld', 't_from_contents', gdf_third_build_LD)
    My_class.createDxf(result_path_dxf, '03_tr', 't_from_contents', gdf_third_build_TR)
    My_class.createDxf(result_path_dxf, '04_bld', 't_from_contents', gdf_third_build_s)
    My_class.createDxf(result_path_dxf, '05_road', 't_from_contents', gdf_fourth_road_s)

    print('stop')

# ---- / ---- / ---- / ---- / MAIN / ---- / ---- / ---- / ---- / ---- / ---- / ---- /

# граница обрезки
name_granica_obrezki = '2'  # берем граничку для обрезки

# путь к GPKG
path_to_GPKG = ((
    r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg").replace('"', ''))


mainFunction(path_to_GPKG, name_granica_obrezki)

# ---- / ---- / ---- / ---- / MAIN / ---- / ---- / ---- / ---- / ---- / ---- / ---- /