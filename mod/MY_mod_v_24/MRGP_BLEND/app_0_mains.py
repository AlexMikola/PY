# -*- coding: utf-8 -*-
"""
Все основные алгоритмы запускаем отсюда
"""
import os
import subprocess as sp
from functools import wraps
import tempfile
import textwrap
import pathlib
import time
import shutil

import re
import xml.dom.minidom
from math import cos, sin, tan, atan2, pi, ceil

import pandas as pd
import geopandas as gpd

import shapely
from shapely import wkt

import bpy
from mathutils import Vector, Matrix
from bpy import context
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, CollectionProperty, EnumProperty
from bpy.types import Panel, Operator, OperatorFileListElement

import osgeo
from osgeo import ogr
from osgeo.ogr import DataSource


class LUCK:
    def __init__(self):
        self.work_list_svg: list = []                   # список путей к svg отличных от объектов в сцене
        self.scene = context.scene                      # сцена
        # self.mrgp = context.scene.mrgp                  # mrgp утилита
        self.path_to_GPKG: str = ""                     # путь к gpkg
        self.file_name: str = ""                        # название файла gpkg
        self.file_extension: str = ""                   # расширения файла *.gpkg
        self.ds = None                                  # osgeo.ogr.DataSource
        self.dict_ds: dict = None                       # словарь с ds отфильтрованных по wkt
        self.dict_ds_mem: dict = None                   # словарь с ds скопировали в память
        self.dict_df: dict = None                       # словарь DataFrames pandas
        self.dict_gdf: dict = None                      # словарь GeoDataFrames geopandas
        self.ds_mem = None                              # DataSource со слоями
        self.str_layer_grn: str = 'GRANICA_OBREZKI'     # слой в котором граничка лежит
        self.col_filtr_name: str = "GR_OBREZKI"         # название колонки для фильтрации в слое где граничка обрезки
        self.col_split_name: str = "t_from_contents"    # название колонки для фильтрации по слоям
        self.name_granica: str = ""                     # название гранички обрезки
        self.tmp_path_fldr: str = ""                    # путь к временному каталогу
        self.svg_path_names: tuple = ()                 # картеж с листами путей и именами svg файлов
        self.blds_pr_mat = ["ZH", "NZH", "PR", "OB"]    # список материалов проектной застройки
        # список материалов для lands
        self.lnds_pr_mat = ["SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV"]
        self.coll_list: list = [
            '1_LD_BUILD',
            '2_LD_LAND',
            '3_Build_S',
            '4_Road_S',
            '5_tr',
            '6_ld']                    # лист коллекций для blender
        self.lst_src_layer: dict = {
            "bld_pr": 'total_building_pr',
            "lnd_pr": 'total_a_landscaping_pr',
            "road_s": 'ROAD_POLY',
            "bld_s": 'BUILDING',
            "tr": 'total_terr_razvitie',
            "ld": 'ld_region'}                # словарь слоёв с которыми работаем
        self.dic_pul_layers: dict = {
            'OP1': {"bld_pr": 'total_building_pr', "lnd_pr": 'total_a_landscaping_pr'},
            'OP2': {"road_s": 'ROAD_POLY', "bld_s": 'BUILDING'},
            'OP3': {"tr": 'total_terr_razvitie', "ld": 'ld_region'},
            'OP4': {"bld_pr": 'total_building_pr'},
            'OP5': {"lnd_pr": 'total_a_landscaping_pr'},
            'OP6': {"bld_s": 'BUILDING'},
            'OP7': {"road_s": 'ROAD_POLY'},
            'OP8': {"tr": 'total_terr_razvitie'},
            'OP9': {"ld": 'ld_region'}
        }                                                # словарь слоёв для работы с выборками

    # декоратор
    def timer_func(func):
        # This function shows the execution time of
        # the function object passed
        def wrap_func(*args, **kwargs):
            t1 = time.time()
            result = func(*args, **kwargs)
            t2 = time.time()
            print(f'time | {(t2 - t1):.4f}s  |  {func.__name__!r} | function \n')
            return result
        return wrap_func

    @staticmethod
    def filter_by_coordinate(
            name_granica: str,
            name_column: str,
            name_f_layer: str,
            nm_lr_for_flt: str,
            ds: osgeo.ogr.DataSource
    ) -> osgeo.ogr.DataSource:
        """
        Получаем из одного или нескольких слоёв из DataSource
        один определенный слой отфильтрованный по WKT...
        WKT берем из этого DataSource слой и в нем берем wkt координаты
        из определенного объекта который выбрали из колонки по определенному значению

        WKT ПОЛУЧАЕМ        / name_f_layer / name_column / name_granica /
        РЕЗУЛЬТ СЛОЙ        /nm_lr_for_flt/

        name_granica      -  название границы по которой фильтруем, должно быть уникальным
        name_column       -  название колонки в слое в котором уникальное название гранички
        name_f_layer      -  название слоя в котором лежит граничка по которой фильтруем
        nm_lr_for_flt     -  название слоя который фильтруем
        """
        if name_granica == "":
            ms = (u'Неверное название границы обрезки')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

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

    @timer_func
    def open_file_by_gdal(self):
        """открываем file GDAL - ом по пути """
        ds = ogr.Open(self.path_to_GPKG, 1)
        return ds

    @timer_func
    def get_dict_from_ds(self):
        """
        получаем словарь отфильтрованых datasource по каждому слою
        """
        dct_ds = {}
        for i in self.lst_src_layer.keys():
            dct_ds[i] = LUCK.filter_by_coordinate(
                name_granica=self.name_granica,
                name_column=self.col_filtr_name,
                name_f_layer=self.str_layer_grn,
                nm_lr_for_flt=self.lst_src_layer[i],
                ds=self.ds
            )
        return dct_ds

    @staticmethod
    def save_lr_to_mem(lr: osgeo.ogr.Layer = "", name_layer: str = "") -> osgeo.ogr.DataSource:
        """ перегоняем слой в память
        lr                  -  слой ogr
        name_layer          -  имя создаваемого слоя в памяти
        """
        if name_layer == "":
            ms = (u'Укажите название слоя для сохранения, текущее значение не указано!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
        ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
        driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

        # скопировали слои в память и разрешили перезаписать если потребутеся
        ds_mem.CopyLayer(lr, name_layer, ['OVERWRITE=YES'])
        return ds_mem

    @timer_func
    def save_dict_of_lrs_to_mem(self):
        """
        сохраняем datasource gdal в оперативке (в словаре DataSources)
        """
        dct_ds_mem = {}  # словарь DataSource в памяти пк
        for i in self.dict_ds.keys():
            dct_ds_mem[i] = LUCK.save_lr_to_mem(self.dict_ds[i], i)
        return dct_ds_mem

    @timer_func
    def save_Dict_With_Ds_To_Mem(self) -> osgeo.ogr.DataSource:
        """ из словаря с отдельными DataSource по каждому слою
        делаем один DataSource со всеми слоями, названия слоёв берем из ключа словаря
        dict_ds             -  dict - словарь с DataSources с отдельными слоями
        """
        if len(self.dict_ds.keys()) == 0:
            ms = (u'Нет данных в словаре :err func "save_Dict_With_Ds_To_Mem"')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
        ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
        driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

        # скопировали слои в память и разрешили перезаписать если потребутеся
        for key, val in self.dict_ds.items():
            ds_mem.CopyLayer(val, key, ['OVERWRITE=YES'])
        return ds_mem

    @timer_func
    def lr_to_dataframe(self) -> dict:
        '''
        перегоняем слои из DataSource в словарь pandas dataframes с инфой по семантике и геометрией
        '''

        rslt_dic = {}   # словарь для сбора результатов
        for lr in self.ds_mem:

            if isinstance(lr, osgeo.ogr.Layer) != True:
                msg = (u' ERROR - !!!! Полученные данные не являются слоем gdal.ogr')
                sp.Popen(f'msg * {ms} ', shell=True)
                return None

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

                # СОЗДАНИЕ DATAFRAME ИЗ СЛОВАРЯ СЛОВАРЕЙ
                df_feature = pd.DataFrame.from_dict(dic_feature, orient='index')

                # добавляем dataframe в словарь
                rslt_dic[l_name] = df_feature

        # первый выход из функции, если только один слой в источнике данных и нет других условий
        return rslt_dic

    @timer_func
    def pandas_to_geopandas(self) -> dict:
        '''
        перегоняем словарь с pandas dataframes в словарь geodataframes
        '''
        dict_result = {}
        for x, y in self.dict_df.items():
            dict_result[x] = gpd.GeoDataFrame(y)
            # geo_pdf = gpd.GeoDataFrame(pd)
        return dict_result

    @timer_func
    def create_tmp_folder_by_path(self):
        """
        создаём временный каталог по пути к родительскому каталогу
        """
        rslt_fldr = self.tmp_path_fldr
        tmp = os.path.dirname(rslt_fldr)
        tmp = tempfile.mkdtemp(dir=tmp)      # cсоздаём временных каталог
        print(f'Временный каталог создан по пути - {tmp}')
        return tmp

    @staticmethod
    def export_wkt_to_svg(coord: str, f_path: str, f_name: str) -> None:
        """     экспорт wkt координат в svg файл
        coord       -  координаты в формате wkt (строка)
        f_path      -  путь к каталогу, куда сохраняем
        f_name      -  имя файла, который сохраняем
        """

        if f_name == "" and f_path == "":
            f_name = "file_from_py.svg"
            full_path = os.path.join(pathlib.Path().resolve(), f'{f_name}')
        elif f_name != "" and f_path != "":
            full_path = os.path.join(f_path, f'{f_name}')
        elif f_path == "":
            full_path = os.path.join(pathlib.Path().resolve(), f'{f_name}')
        elif f_name == "":
            full_path = os.path.join(f_path, f'{f_name}')

        key_color = {"NZH": "#e89816", "OB": "#e89816", "PR": "#c27ede", "ZH": "#c63c38", "DE": "#ffe8d0",
                     "DE2": "#ffe8d0",
                     "DO": "#c8c8c8", "HP": "#75b7dd", "OV": "#fbc6c5", "PP": "#c8c8c8", "SP": "#83b8ff",
                     "TP": "#e6e6e6",
                     "TR": "#e6e6e6", "VD": "#bc0064", "VP": "#a5bfdd", "VS": "#e78bb7", "ZE": "#bedebe"}

        if f_name.split("_")[0] in key_color.keys():
            clr_hex = key_color[f_name.split("_")[0]]
        else:
            clr_hex = "#D0D0D0"

        # shapely svg
        area = wkt.loads(coord)
        # area = tr(geom_w, xoff=0, yoff=10000, zoff=0)  # смещаем геометрии по y оси
        with open(full_path, 'w') as f:
            # масштаб
            scale = 10000
            bound = area.bounds

            props = {
                'version': '1.1',
                'baseProfile': 'full',
                'width': '{width:.0f}cm'.format(width=10 * scale),
                'height': '{height:.0f}cm'.format(height=10 * scale),
                'viewBox': '%.1f,%.1f,%.1f,%.1f' % (0, -1 * scale, 1 * scale, 1 * scale),
                'transform': "scale(-1, 1)",
                # 'viewBox': '%f,%f,%f,%f' % (0, 0, 1*scale, 1*scale),
                'xmlns': 'http://www.w3.org/2000/svg',
                'xmlns:ev': 'http://www.w3.org/2001/xml-events',
                'xmlns:xlink': 'http://www.w3.org/1999/xlink'
            }

            f.write(textwrap.dedent(r'''
                 <?xml version="1.0" encoding="utf-8" ?>
                 <svg {attrs:s}>
                 {data:s}
                 </svg>
             ''').format(
                attrs=' '.join(['{key:s}="{val:s}"'.format(key=key, val=props[key]) for key in props]),
                data=area.svg(fill_color=clr_hex)
            ).strip())

    @timer_func
    def export_gdf_to_svg(self):
        """export каждого объекта из gdf в отдельный файл stl
        gdf_src                 -   источник объектов, GeoDataFrame
        name_t_from_con         -   колонка "t_from_contents"
        fltr_clmn               -   значение колонки "t_from_contents" для данного объекта
        path_rslt               -   куда сохраняем результаты (сам stl file)
        """
        for x, y in self.dict_gdf.items():
            if len(y.keys()) == 0:
                continue
            geom_clmn = y._geometry_column_name                         # получаем название колонки геометрии
            name_t_from_con = self.col_split_name                       # название колонки для для сортировки
            cur_gdf = y.loc[:, (name_t_from_con, geom_clmn)]            # срез по геодатафрэйму только нужных столбиков
            cur_gdf['index'] = cur_gdf.index                            # присваиваем значения индексов новой колонке
            cur_gdf = cur_gdf.loc[:, ('index', name_t_from_con, geom_clmn)]  # упорядочили колонки по списку

            # цикл по каждой строке геодатафрэйма
            for index, val in cur_gdf.iterrows():

                # экспорт в svg
                fltr_clmn = val[name_t_from_con]
                filter_par = x
                if filter_par in ['bld_pr', 'lnd_pr']:
                    name_for_file_svg = f'{fltr_clmn}_fid_{index}.svg'
                elif filter_par in ['road_s', 'bld_s', 'tr', 'ld']:
                    name_for_file_svg = f'{filter_par}_fid_{index}.svg'

                LUCK.export_wkt_to_svg(val[geom_clmn], self.tmp_path_fldr, name_for_file_svg)

    # @timer_func
    def export_selection_gdf_to_svg(self):
        """export каждого объекта из gdf в отдельный файл stl
        gdf_src                 -   источник объектов, GeoDataFrame
        name_t_from_con         -   колонка "t_from_contents"
        fltr_clmn               -   значение колонки "t_from_contents" для данного объекта
        path_rslt               -   куда сохраняем результаты (сам stl file)
        """
        for x, y in self.dict_gdf.items():
            if x in self.sel_lrs.keys():
                if len(y.keys()) == 0:
                    continue
                geom_clmn = y._geometry_column_name                         # получаем название колонки геометрии
                name_t_from_con = self.col_split_name                       # название колонки для для сортировки
                cur_gdf = y.loc[:, (name_t_from_con, geom_clmn)]            # срез по геодатафрэйму только нужных столбиков
                cur_gdf['index'] = cur_gdf.index                            # присваиваем значения индексов новой колонке
                cur_gdf = cur_gdf.loc[:, ('index', name_t_from_con, geom_clmn)]  # упорядочили колонки по списку

                # цикл по каждой строке геодатафрэйма
                for index, val in cur_gdf.iterrows():

                    # экспорт в svg
                    fltr_clmn = val[name_t_from_con]
                    filter_par = x
                    if filter_par in ['bld_pr', 'lnd_pr']:
                        name_for_file_svg = f'{fltr_clmn}_fid_{index}.svg'
                    elif filter_par in ['road_s', 'bld_s', 'tr', 'ld']:
                        name_for_file_svg = f'{filter_par}_fid_{index}.svg'

                    LUCK.export_wkt_to_svg(val[geom_clmn], self.tmp_path_fldr, name_for_file_svg)


    @timer_func
    def create_collection_in_blend_scene(self):
        for i in self.coll_list:
            if i not in [x.name for x in bpy.context.blend_data.collections]:
                my_collection = bpy.context.blend_data.collections.new(name=i)
                bpy.context.collection.children.link(my_collection)
        return {'FINISHED'}

    @staticmethod
    def get_path_names_files_by_exten(path_to_target_folder: str = '', extension: str = '.shp'):
        """получаем все пути к файлам из папки по расширению
        :param path_to_target_folder:  путь к целевому каталогу
        :param extension:              расширение файлов какое ищем? (по умолчанию(.shp)
        :return:                       картеж из списка путей и списка имен файлов
        """
        path_tab = []  # переменная для путей
        name_tab = []  # переменная для имен файлов
        for root, directories, filenames in os.walk(path_to_target_folder):
            for directory in directories:
                print(os.path.join(root, directory))
            for filename in filenames:
                if (str(filename)).lower().endswith(extension):
                    path_tab.append((os.path.join(root, filename).replace('\\', '//')))
                    name_tab.append((os.path.splitext(filename)[0]).replace('\\', '//'))
        return path_tab, name_tab

    @timer_func
    def import_svg_to_scen(self):
        """
        импортируем все svg в сцену
        """
        for x in self.svg_path_names[0]:
            bpy.ops.import_curve.svg(filepath=x)  # импорт svg по пути
            bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        # переименовываем все объекты по названию коллекции которой они принадлежат
        for x in bpy.data.objects:
            x.name = x.users_collection[0].name[:-4]
            x.data.name = x.users_collection[0].name[:-4]

        # удаляем все коллекции если в имени коллекции в конце есть .svg
        for x in bpy.data.collections:
            if x.name.endswith('.svg'):
                bpy.data.collections.remove(x)

        # удаляем все материалы если их название начинается с 'SVGMat'
        for x in bpy.data.materials:
            if x.name.startswith('SVGMat'):
                bpy.data.materials.remove(x)

    @timer_func
    def iter_import_svg_to_scen(self):
        """
        импортируем все svg в сцену
        """
        # получаем список curves присутствующих в сцене
        crvs_name = [r.name for r in bpy.data.curves]

        # objcts_name = [r.name for r in bpy.data.objects]
        # meshs_name = [r.name for r in bpy.data.objects]
        # colls_name = [r.name for r in bpy.data.collections]
        # selected_name = [x.name for x in bpy.context.selected_objects]

        # получаем список путей к объектам имен которых нет в curves сцены
        self.work_list_svg = [x for x in self.svg_path_names[0] if os.path.basename(x)[:-4] not in crvs_name]

        # определяем длину списка объектов которых обрабатывем
        cnt = len([x for x in self.work_list_svg])
        if cnt == 0:
            return None

        # создаём итератор обхода путей файлов
        it = iter([x for x in self.work_list_svg])

        # импортируем svg в сцену
        for x in range(cnt):
            x = next(it)
            # заносим в сцену только те объекты имен которых еще нет (проверяем имена по curves)
            if os.path.basename(x)[:-4]:
                bpy.ops.import_curve.svg(filepath=x)  # импорт svg по пути
                bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        # текущие имена из svg путей
        cur_names = [os.path.basename(x)[:-4] for x in self.work_list_svg]

        # переименовываем все объекты по названию коллекции которой они принадлежат
        # дополнительные проверки типа объекта и окончания имени коллекции svg
        for col in bpy.data.collections:
            if col.name not in self.coll_list:
                for ob in col.objects:
                    ob.name = ob.users_collection[0].name[:-4]        # переименовываем объект
                    ob.data.name = ob.users_collection[0].name[:-4]   # переименовываем curve входящую в объект



        # for y in cur_names:
        #     ob = bpy.data.objects.get(y)  # получаем объект по имени
        #     for x in bpy.data.objects:
        #         # if x.users_collection[0].name not in self.coll_list:
        #         if x.users_collection[0].name in cur_names:
        #             x.name = x.users_collection[0].name[:-4]            # переименовываем объект
        #             x.data.name = x.users_collection[0].name[:-4]       # переименовываем curve входящую в объект


        # удаляем все коллекции если в имени коллекции в конце есть .svg
        for x in bpy.data.collections:
            if x.name not in self.coll_list:
                bpy.data.collections.remove(x)

        # удаляем все материалы если их название начинается с 'SVGMat'
        for x in bpy.data.materials:
            if x.name.startswith('SVGMat'):
                bpy.data.materials.remove(x)

    @timer_func
    def extrude_curves_in_data(self):
        """
        выдавливаем по умолчанию
        """
        prefix = ("road_s", "bld_s", "tr", "ld")      # начало у файлов (те которые не pr)
        bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        for x in bpy.data.curves:
            if not x.name.startswith(prefix):
                r = x.name.split('_fid_')[0]
                h = float(r.split('_')[2])  # получаем высоту в метрах
                x.extrude = h/2
                bpy.data.objects[x.name].location.z += h/2

    @timer_func
    def iter_extrude_curves_in_data(self):
        """
        выдавливаем по умолчанию
        """
        prefix = ("road_s", "bld_s", "tr", "ld")      # начало у файлов (те которые не pr)
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land
        bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        # текущие имена из svg путей
        cur_names = [os.path.basename(x)[:-4] for x in self.work_list_svg]

        cnt = len(cur_names)
        if cnt == 0:
            return None

        obj_crv = []
        for x in bpy.data.curves:
            if x.name in cur_names:
                obj_crv.append(x)

        it = iter(obj_crv)
        for i in range(cnt):
            x = next(it)
            r = x.name.split('_fid_')[0]
            if r not in prefix:
                try:
                    h = float(r.split('_')[2])  # получаем высоту в метрах
                    x.extrude = h / 2           # при экструдии не создаётся новый объект
                    # ob = bpy.data.objects[x.name]
                    # ob.location.z += h / 2
                except:
                    print(x.name)










        # cnt = len([x for x in bpy.data.curves if not x.name.startswith(prefix) or not x.name in cur_names])
        # it = iter([x for x in bpy.data.curves if not x.name.startswith(prefix) or not x.name in cur_names])
        # for i in range(cnt):
        #     x = next(it)
        #     r = x.name.split('_fid_')[0]
        #     if r not in prefix:
        #         try:
        #             h = float(r.split('_')[2])  # получаем высоту в метрах
        #             x.extrude = h / 2           # при экструдии не создаётся новый объект
        #             # ob = bpy.data.objects[x.name]
        #             # ob.location.z += h / 2
        #         except:
        #             print(x.name)

        # for x in bpy.data.curves:
        #     if not x.name.startswith(prefix):
        #         r = x.name.split('_fid_')[0]
        #         h = float(r.split('_')[2])  # получаем высоту в метрах
        #         x.extrude = h/2
        #         bpy.data.objects[x.name].location.z += h/2

    @timer_func
    def convert_curve_to_mesh(self):
        """
        конвертирем curve to mesh
        """
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

        bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        # выбрали объекты из двух коллекций
        pr_coll = ['1_LD_BUILD', '2_LD_LAND']
        objects = [x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll]

        # выделили объекты из коллекции
        for x in objects:
            obj = bpy.data.objects.get(x.name)
            obj.select_set(True)

        # активировали объекты, конвертировали в mesh и сохранили по коллекциям
        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]  # активировали объект
            msh = bpy.context.active_object.to_mesh().copy()                    # создали mesh
            ob = bpy.data.objects.new(obj.name, msh)                            # сохранили mesh как объект
            r = obj.name.split('_fid_')[0]
            h = float(r.split('_')[2])  # получаем высоту в метрах
            ob.location.z += h/2
            # bpy.data.objects[x.name].location.z += h / 2

            if ob.name.startswith(build_list):
                bpy.data.collections['1_LD_BUILD'].objects.link(ob)
            if ob.name.startswith(land_list):
                bpy.data.collections['2_LD_LAND'].objects.link(ob)

        # удаляем curve из двух коллекций
        for x in objects:
            bpy.ops.collection.objects_remove_all()

    @timer_func
    def iter_convert_curve_to_mesh(self):
        """
        конвертирем curve to mesh
        """
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

        bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        cnt = len([x for x in self.work_list_svg])
        if cnt == 0:
            return None

        # список имен объектов с которыми работаем
        cur_names = [os.path.basename(x)[:-4] for x in self.work_list_svg]

        obj_crv = []
        for x in bpy.data.curves:
            if x.name in cur_names and x.name.startswith(build_list + land_list):
                obj_crv.append(x)

        cnt = len(obj_crv)
        it = iter(obj_crv)

        for obj in range(cnt):
            obj = next(it)
            # нужно создавать меши еще до отправки в коллекции !!!!!!!!!!!!!!!!!!!!!!

            ob = bpy.data.objects.new(obj.name, obj)        # создаём объекты из curve
            msh = ob.to_mesh().copy()                       # создаём mesh из объекта
            bpy.data.objects.remove(ob)                     # удаляем объект из curve

            ob = bpy.data.objects.new(obj.name, msh)        # создаём объект из mesha
            r = obj.name.split('_fid_')[0]
            h = float(r.split('_')[2])                      # получаем высоту в метрах
            ob.location.z += h/2                            # поднимаем объект на высоту

            # bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]  # активировали объект
            #
            #
            # bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]  # активировали объект
            # msh = bpy.context.active_object.to_mesh().copy()                    # создали mesh
            # ob = bpy.data.objects.new(obj.name, msh)                            # сохранили mesh как объект
            # r = obj.name.split('_fid_')[0]
            # h = float(r.split('_')[2])  # получаем высоту в метрах
            # ob.location.z += h/2


        # cnt = len([x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll])
        # it = iter([x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll])





        # # выбрали объекты из двух коллекций
        # pr_coll = ['1_LD_BUILD', '2_LD_LAND']
        # cnt = len([x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll])
        # it = iter([x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll])


        # # выделили объекты из коллекции
        # for x in range(cnt):
        #     x = next(it)
        #     obj = bpy.data.objects.get(x.name)
        #     obj.select_set(True)
        #
        # cnt = len(bpy.context.selected_objects)
        # it = iter(bpy.context.selected_objects)
        # # активировали объекты, конвертировали в mesh и сохранили по коллекциям
        # for obj in range(cnt):
        #     obj = next(it)
        #     bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]  # активировали объект
        #     msh = bpy.context.active_object.to_mesh().copy()                    # создали mesh
        #     ob = bpy.data.objects.new(obj.name, msh)                            # сохранили mesh как объект
        #     r = obj.name.split('_fid_')[0]
        #     h = float(r.split('_')[2])  # получаем высоту в метрах
        #     ob.location.z += h/2
        #     # bpy.data.objects[x.name].location.z += h / 2
        #
        #     if ob.name.startswith(build_list):
        #         bpy.data.collections['1_LD_BUILD'].objects.link(ob)
        #     if ob.name.startswith(land_list):
        #         bpy.data.collections['2_LD_LAND'].objects.link(ob)
        #
        # # удаляем curve из двух коллекций
        # objects = [x for x in bpy.data.objects if x.type == "CURVE" and x.users_collection[0].name in pr_coll]
        # for x in objects:
        #     bpy.ops.collection.objects_remove_all()

    @timer_func
    def make_shade_flat(self):
        """
        убираем сглаживание curve to mesh
        """
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

        bpy.ops.object.select_all(action='DESELECT')                        # сняли выделение со всего
        bpy.ops.object.select_all(action='SELECT')                          # выделение всего
        bpy.ops.object.shade_flat()                                         # убрали сглаживание
        bpy.ops.object.select_all(action='DESELECT')                        # сняли выделение со всего

    @timer_func
    def sort_all_obj_by_collections(self):

        collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

        bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов

        try:
            for x in bpy.data.objects:
                if x.name.startswith("bld_s") and x.type == "CURVE":
                    if not x.users_collection:
                        bpy.data.collections['3_Build_S'].objects.link(x)
                        continue
                if x.name.startswith("road_s") and x.type == "CURVE":
                    if not x.users_collection:
                        bpy.data.collections['4_Road_S'].objects.link(x)
                        continue
                if x.name.startswith("tr") and x.type == "CURVE":
                    if not x.users_collection:
                        bpy.data.collections['5_tr'].objects.link(x)
                        continue
                if x.name.startswith("ld") and x.type == "CURVE":
                    if not x.users_collection:
                        bpy.data.collections['6_ld'].objects.link(x)
                        continue
                if x.name.split('_')[0] in build_list and x.type == "MESH":
                    if not x.users_collection:
                        bpy.data.collections['1_LD_BUILD'].objects.link(x)
                        continue
                if x.name.split('_')[0] in land_list and x.type == "MESH":
                    if not x.users_collection:
                        bpy.data.collections['2_LD_LAND'].objects.link(x)
        except:
            print(f"объект {x.name} уже в коллекции"  )

    @timer_func
    def move_by_z(self):
        bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
        collection_list = ['1_LD_BUILD']

        # имена объектов с которыми работаем
        cur_names = [os.path.basename(x)[:-4] for x in self.work_list_svg]

        # цикл по всем объектам которые нужно оработать
        for x in cur_names:
            for col in collection_list:
                for obj in bpy.data.collections[col].all_objects:
                    if obj.name.startswith(x):
                        r = x.split('_fid_')[0]
                        try:
                            z_val = r.split('_')[3]
                            if z_val:
                                z_val = float(z_val)
                                obj.location.z += z_val
                        except:
                            pass

    @timer_func
    def del_empty_collections(self):
        """
        удаляем ненужные пустые коллекции
        """
        bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов

        for col in bpy.context.blend_data.collections:
            if len(col.objects.keys()) == 0:
                bpy.data.collections.remove(col)  # удалили коллекции

    @timer_func
    def set_normal_view_in_scene(self):
        """
        устанавливаем нормальное отображение в сцене
        """
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        s.clip_start = 1
                        s.clip_end = 900000

    def del_tmp_folder(self):
        """
        удаляем временный каталог
        """
        tmp_fldr = self.tmp_path_fldr
        shutil.rmtree(tmp_fldr)

    def vwport_hide(self):
        """
        Скроем сущпольные коллекции в сцене
        """
        for i, x in enumerate(bpy.data.collections.items()):
            if x[0] in ['1_LD_BUILD']:
                # bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_viewport = False
            if x[0] in ['2_LD_LAND']:
                # bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_viewport = False
            if x[0] in ['3_Build_S']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True
            if x[0] in ['4_Road_S']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True
            if x[0] in ['5_tr']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True
            if x[0] in ['6_ld']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True

    def vwport_show_all(self):
        """
        откроем все коллекции в сцене
        """
        for i, x in enumerate(bpy.data.collections.items()):
            bpy.data.collections[i].hide_viewport = False
            bpy.data.collections[i].hide_render = False

    def del_cub_mesh_coll(self):
        objs = [x for x in bpy.data.objects if x.name.startswith("Collec")]
        for x in objs:
            if x.type == "MESH":
                bpy.data.objects.remove(x)

    @timer_func
    def run_selection_import(self):
        """
        выборочный импорт, только тех слоёв что выбрал пользователь
        """
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! РАСКОМЕНТИРОВАТЬ
        # получаем путь к GPKG
        self.path_to_GPKG = (bpy.context.scene.mrgp.my_path.replace('"', ''))

        # проверка, по этому пути есть ли файл
        if not os.path.isfile(self.path_to_GPKG):
            ms = (u'По указанному пути нет gpkg!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # проверка, по этому пути есть ли файл с нужным расширением
        self.file_name, self.file_extension = os.path.splitext(self.path_to_GPKG)
        if self.file_extension != '.gpkg':
            ms = (u'Неверное расширение файла! Нужен *.gpkg')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! РАСКОМЕНТИРОВАТЬ
        # граница обрезки
        self.name_granica = bpy.context.scene.mrgp.my_string_add
        if self.name_granica == "граничка название" or self.name_granica == "":  # если не ввели граничку то присвоить по умлочанию
            ms = (u'Неверное название границы обрезки!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # получаем ссылку на DataSource Gdal
        self.ds = LUCK.open_file_by_gdal(self)

        # получаем словарь отфильтрованых datasource по каждому слою
        self.dict_ds = LUCK.get_dict_from_ds(self)

        # переросим словарь с отдельными ds по слоям - в память пк
        self.dict_ds_mem = LUCK.save_dict_of_lrs_to_mem(self)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        self.ds_mem = LUCK.save_Dict_With_Ds_To_Mem(self)

        # перегоняем DataSource в DataFrame
        self.dict_df = LUCK.lr_to_dataframe(self)

        # словарь pandas Dataframe -> словарь GeoPandas GeoDataFrame
        self.dict_gdf = LUCK.pandas_to_geopandas(self)

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! РАСКОМЕНТИРОВАТЬ
        # получаем путь к временному каталогу для сохранения промежуточных результатов
        self.tmp_path_fldr = (bpy.context.scene.mrgp.my_string_tmp.replace('"', ''))

        # # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ЗАКОМЕНТИРОВАТЬ
        # self.tmp_path_fldr = r"C:\Users\dolgushin_an\Desktop\\"


        # проверка, чтоб путь был не пустым
        if self.tmp_path_fldr == "" or not os.path.isdir(self.tmp_path_fldr):
            ms = (f'Pick correctly path to save tmp files!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # создали временный каталог для сохранения результатов svg файлов
        self.tmp_path_fldr = LUCK.create_tmp_folder_by_path(self)


        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! РАСКОМЕНТИРОВАТЬ
        # получаем значение какого набора слоёв нужно получить в выборку
        sel_layer = bpy.context.scene.mrgp.my_enum

        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! РАСКОМЕНТИРОВАТЬ
        # определяем какие слои выбрал пользователь для импорта
        self.sel_lrs = self.dic_pul_layers[sel_layer]

        # # # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ЗАКОМЕНТИРОВАТЬ
        # self.sel_lrs = {"road_s": 'ROAD_POLY', "bld_s": 'BUILDING'}

        print(f"граничка {self.name_granica}  выборка слоёв {self.sel_lrs}\n")
        print(f"{self.sel_lrs} | {type(self.sel_lrs)}")

        # экспорт в svg только выбранных слоёв
        LUCK.export_selection_gdf_to_svg(self)


        # получаем список всех путей и названий файлов во временном каталоге по расширению '*.svg'
        self.svg_path_names = LUCK.get_path_names_files_by_exten(self.tmp_path_fldr, extension=".svg")

        # # импортируем svg в blender
        # LUCK.import_svg_to_scen(self)

        # импортируем svg в blender через итер
        LUCK.iter_import_svg_to_scen(self)

        # удаляем временный каталог
        LUCK.del_tmp_folder(self)

        # # extrude всех curve
        # LUCK.extrude_curves_in_data(self)

        # extrude всех curve через iter
        LUCK.iter_extrude_curves_in_data(self)

        # # конвертируем в mesh все curve
        # LUCK.convert_curve_to_mesh(self)

        # конвертируем в mesh все curve
        LUCK.iter_convert_curve_to_mesh(self)

        # создаём коллекции в blender scene
        LUCK.create_collection_in_blend_scene(self)

        # рассортировать объекты по сценам в зависимости от названия объекта
        LUCK.sort_all_obj_by_collections(self)

        # удаляем пустые коллекции из сцены
        LUCK.del_empty_collections(self)

        # перемещаем объекты по Z если есть необходимость
        LUCK.move_by_z(self)

        # убираем сглаживание углов
        LUCK.make_shade_flat(self)

        # устанавливаем нормальное отображение в сцене
        LUCK.set_normal_view_in_scene(self)

        # Скроем сущпольные коллекции в сцене
        LUCK.vwport_hide(self)

        # удаляем объекты mesh чьи имена начинаются с Collect
        LUCK.del_cub_mesh_coll(self)


        # # откроем все коллекции в сцене
        # LUCK.vwport_show_all(self)

    @timer_func
    def run_import(self):
        """
        ОСНОВНАЯ ФУНКЦИЯ MAIN для LUCK
        """
        # получаем путь к GPKG
        self.path_to_GPKG = (bpy.context.scene.mrgp.my_path.replace('"', ''))

        # проверка, по этому пути есть ли файл
        if not os.path.isfile(self.path_to_GPKG):
            ms = (u'По указанному пути нет gpkg!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # проверка, по этому пути есть ли файл с нужным расширением
        self.file_name, self.file_extension = os.path.splitext(self.path_to_GPKG)
        if self.file_extension != '.gpkg':
            ms = (u'Неверное расширение файла! Нужен *.gpkg')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # граница обрезки
        self.name_granica = bpy.context.scene.mrgp.my_string
        if self.name_granica == "граничка название" or self.name_granica == "":  # если не ввели граничку то присвоить по умлочанию
            ms = (u'Неверное название границы обрезки!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # получаем ссылку на DataSource Gdal
        self.ds = LUCK.open_file_by_gdal(self)

        # получаем словарь отфильтрованых datasource по каждому слою
        self.dict_ds = LUCK.get_dict_from_ds(self)

        # переросим словарь с отдельными ds по слоям - в память пк
        self.dict_ds_mem = LUCK.save_dict_of_lrs_to_mem(self)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        self.ds_mem = LUCK.save_Dict_With_Ds_To_Mem(self)

        # перегоняем DataSource в DataFrame
        self.dict_df = LUCK.lr_to_dataframe(self)

        # словарь pandas Dataframe -> словарь GeoPandas GeoDataFrame
        self.dict_gdf = LUCK.pandas_to_geopandas(self)

        # получаем путь к временному каталогу для сохранения промежуточных результатов
        self.tmp_path_fldr = (bpy.context.scene.mrgp.my_string_tmp.replace('"', ''))

        # проверка, чтоб путь был не пустым
        if self.tmp_path_fldr == "" or not os.path.isdir(self.tmp_path_fldr):
            ms = (f'Pick correctly path to save tmp files!')
            sp.Popen(f'msg * {ms} ', shell=True)
            return None

        # создали временный каталог для сохранения результатов svg файлов
        self.tmp_path_fldr = LUCK.create_tmp_folder_by_path(self)

        # экспорт в *.svg каждого GeoDataFrame из словаря с gdf
        LUCK.export_gdf_to_svg(self)

        # получаем список всех путей и названий файлов во временном каталоге по расширению '*.svg'
        self.svg_path_names = LUCK.get_path_names_files_by_exten(self.tmp_path_fldr, extension=".svg")

        # # импортируем svg в blender
        # LUCK.import_svg_to_scen(self)

        # импортируем svg в blender через итер
        LUCK.iter_import_svg_to_scen(self)

        # удаляем временный каталог
        LUCK.del_tmp_folder(self)

        # # extrude всех curve
        # LUCK.extrude_curves_in_data(self)

        # extrude всех curve через iter
        LUCK.iter_extrude_curves_in_data(self)

        # # конвертируем в mesh все curve
        # LUCK.convert_curve_to_mesh(self)

        # конвертируем в mesh все curve
        LUCK.iter_convert_curve_to_mesh(self)

        # создаём коллекции в blender scene
        LUCK.create_collection_in_blend_scene(self)

        # рассортировать объекты по сценам в зависимости от названия объекта
        LUCK.sort_all_obj_by_collections(self)

        # удаляем пустые коллекции из сцены
        LUCK.del_empty_collections(self)

        # перемещаем объекты по Z если есть необходимость
        LUCK.move_by_z(self)

        # убираем сглаживание углов
        LUCK.make_shade_flat(self)

        # устанавливаем нормальное отображение в сцене
        LUCK.set_normal_view_in_scene(self)

        # Скроем сущпольные коллекции в сцене
        LUCK.vwport_hide(self)

        # удаляем объекты mesh чьи имена начинаются с Collect
        LUCK.del_cub_mesh_coll(self)


        # # откроем все коллекции в сцене
        # LUCK.vwport_show_all(self)


class AssMaterials:

    @staticmethod
    def assign_mat_to_each_face(ob, list_indx_face, list_indx_face_Z, mat_name):
        """
        назначаем материалы отдельно по полигонам (пара
        """
        build_list = ["ZH", "NZH", "PR", "OB"]

        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        name_mat_gis = ((ob.name).split('_fid_')[0]).split('_')[0]  # получили имя материала из названия объекта
        mat = bpy.data.materials.get(name_mat_gis)  # материал загнали в переменную
        ob.data.materials.append(mat)  # добавили материал к объекту
        if name_mat_gis in build_list:  # если это здание, то еще материал крыш берем
            name_mat = name_mat_gis + "_DF"
            mat_top = bpy.data.materials.get(name_mat)
            ob.data.materials.append(mat_top)  # добавили материал крыши к объекту

        # назначаем материал каждому полигону объекта по списку индексов и названию материала
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]  # активировали объект
        slot_indx = ob.data.materials.find(mat_name)  # индекс слота по названию
        bpy.ops.object.mode_set(mode='OBJECT')
        for indx in list_indx_face:  # активировали полигоны по списку индексов
            ob.data.polygons[indx].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        ob.active_material_index = slot_indx  # активировали слот
        bpy.ops.object.material_slot_assign()  # назначили материал из слота выборке полигонов
        bpy.ops.mesh.select_all(action='DESELECT')  # снять выделение со всего
        bpy.ops.object.mode_set(mode='OBJECT')

        if name_mat_gis in build_list:  # если это здание, то еще материал крыш назначаем на face
            slot_indx = ob.data.materials.find(name_mat)  # индекс слота по названию
            for indx in list_indx_face_Z:  # активировали полигоны по списку индексов
                ob.data.polygons[indx].select = True

            bpy.ops.object.mode_set(mode='EDIT')
            ob.active_material_index = slot_indx  # активировали слот
            bpy.ops.object.material_slot_assign()  # назначили материал из слота выборке полигонов
            bpy.ops.mesh.select_all(action='DESELECT')  # снять выделение со всего
            bpy.ops.object.mode_set(mode='OBJECT')

    @staticmethod
    def get_indx_polygon(ob):
        """
        получаем 2 списка индексов полигонов объекта (список паралелльных z полигонов и полигонов под текстуры)
        """
        polygons = ob.data.polygons  # get all polygons from obj in variable
        list_inx_poly_z = []
        list_inx_poly_for_texture = []
        for p in polygons:
            # cur_verts = [vert for vert in polygons[0].vertices]
            cur_verts = [vert for vert in p.vertices]  # get number vertex curent polygon
            coord_sel_polygon = [ob.data.vertices[x].co.xyz for x in cur_verts]  # get coord vertex cur polygon
            z = [format(x[2], ".4f") for x in coord_sel_polygon]  # get z coord with raunding befor 4 sign
            z_set = set(z)  # set (get only unic z coord)
            if len(z_set) == 1:  # if z coord only 1, then it parallel face
                list_inx_poly_z.append(p.index)
            if len(z_set) > 1:  # if z coord > 1, then it not parallel z face
                list_inx_poly_for_texture.append(p.index)
        return list_inx_poly_z, list_inx_poly_for_texture

    @staticmethod
    def append_mat_from_file():
        filepath = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\default.blend"
        # data_to = bpy.data
        with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
            # data_to.objects = [name for name in data_from.objects if name.startswith("Cube")]

            lst_cur_mat = [x.name for x in bpy.data.materials]
            lst_new_mat = [x for x in data_from.materials]
            for x, y in enumerate(lst_new_mat):
                if y not in lst_cur_mat:
                    data_to.materials.append(data_from.materials[x])
            # [data_to.materials.append(m) for m in data_from.materials if m not in data_to.materials]
            # data_to.materials = [m for m in data_from.materials if m not in data_to.materials]

        # sc_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\default.blend"
        # dir_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\"
        # with bpy.data.libraries.load(filepath=sc_path, directory=dir_path, link=False) as (data_from, data_to):
        #     # data_to.materials = [m for m in data_from.materials if m.startswith("MATLIB_")]
        #     data_to.materials = [m for m in data_from.materials]

    @staticmethod
    def asign_mat_to_obj(ob, name_mat_gis):
        """
        назначаем материал на весь объект
        """
        mat = bpy.data.materials.get(name_mat_gis)
        if ob.data.materials:
            ob.data.materials[0] = mat
        else:
            ob.data.materials.append(mat)

    def ass_mat(self):
        """
        основная процедура назначения материалов объектам
        """
        build_list = ["ZH", "NZH", "PR", "OB"]
        land_list = ["SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV"]

        sel_objs = [ob for ob in bpy.context.selected_objects]  # получаем в переменную все выбранные объекты
        if len(sel_objs) > 0:
            # назначаем материалы на каждый face (polygon)
            for x in sel_objs:
                if x.name not in ['Camera', 'Cube', 'Light'] and x.type == 'MESH':

                    mat_name = ((x.name).split('_fid_')[0]).split('_')[0]  # получили назв основного материала

                    if mat_name in build_list:
                        AssMaterials.asign_mat_to_obj(x, mat_name)  # назначили на весь объект материал
                    if mat_name in land_list:
                        AssMaterials.asign_mat_to_obj(x, mat_name)  # назначили на весь объект материал для landscaping

        else:
            # назначаем материалы на каждый face (polygon)
            for x in bpy.data.objects:
                # if x.name not in ['Camera', 'Cube', 'Light'] and x.type == 'MESH':
                if x.name not in ['Camera', 'Cube', 'Light'] and x.type == 'MESH':
                    mat_name = ((x.name).split('_fid_')[0]).split('_')[0]  # получили назв основного материала

                    if mat_name in build_list:
                        # получаем листы с индексами полигонов паралельных z и нет
                        lz, lt = AssMaterials.get_indx_polygon(x)
                        # назначили основной материал каждому полигону из списка
                        AssMaterials.assign_mat_to_each_face(x, lt, lz, mat_name)

                    if mat_name in land_list:
                        AssMaterials.asign_mat_to_obj(x, mat_name)  # назначили на весь объект материал для landscaping

        bpy.ops.object.select_all(action='DESELECT')

    # декоратор
    def timer_func(func):
        # This function shows the execution time of
        # the function object passed
        def wrap_func(*args, **kwargs):
            t1 = time.time()
            result = func(*args, **kwargs)
            t2 = time.time()
            print(f'Function {func.__name__!r} executed in {(t2 - t1):.4f}s')
            return result
        return wrap_func

    @timer_func
    def run_ass_materials(self):
        """
        ОСНОВНАЯ ФУНКЦИЯ MAIN для AssMaterials
        """

        # добавляем материалы из файла blend
        AssMaterials.append_mat_from_file()

        # назначаем материалы объектам
        AssMaterials.ass_mat(self)

    @timer_func
    def delite_mat_from_obj(self):
        """
         удаляем назначенные материалы с выделенного объекта
         """
        sel_objs = [ob for ob in bpy.context.selected_objects]  # получаем в переменную все выбранные объекты
        if len(sel_objs) > 0:
            for obj in sel_objs:
                obj.active_material_index = 0
                for i in range(len(obj.material_slots)):
                    bpy.ops.object.material_slot_remove({'object': obj})


class CamSun:
    def __init__(self):
        self.crd = ""               # координаты объекта по которому выставляем камеры, солнце
        self.sun_name = "00_SUN"
        self.cam_dict = {
            '01_North': 'N.png',
            '02_South': 'S.png',
            '03_East': 'E.png',
            '04_West': 'W.png'}      # словарь соответствия названий камер и названий растровых файлов

    @staticmethod
    def del_cam(ob):
        if ob != None:
            bpy.data.cameras.remove(ob)

    @staticmethod
    def get_cam(ob):
        if ob != None:
            cam = bpy.data.cameras.get(ob.name)
            return cam

    @staticmethod
    def del_sun(ob):
        if ob != None:
            bpy.data.lights.remove(ob)

    @staticmethod
    def get_sun(ob):
        if ob != None:
            sun = bpy.data.lights.get(ob.name)
            return sun

    def get_coord_obj(self):
        ob = bpy.context.active_object          # получили в переменную активный объект

        # если объект не выбран то присваиваем эти координаты для выставления камер и солнца
        try:
            bpy.context.scene.mrgp.fgm_path
        except:
            return Vector((-5346.04638671875, -6428.54248046875, 2.072999954223633))

        object = bpy.data.objects.get(ob.name)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
        v_global = bpy.context.object.location
        return v_global

    def creat_cam(self):
        """
        добавляем камеры по ключам словаря и координатам
        """
        for new_cam_name in self.cam_dict.keys():
            camera_data = bpy.data.cameras.new(name=new_cam_name)
            camera_object = bpy.data.objects.new(new_cam_name, camera_data)
            bpy.context.scene.collection.objects.link(camera_object)
            bpy.context.view_layer.objects.active = camera_object
            camera_object.scale[0] = 70
            camera_object.scale[1] = 70
            camera_object.scale[2] = 70
            if new_cam_name == '01_North':
                camera_object.location = (self.crd[0], self.crd[1] - 600, 300)
                camera_object.rotation_euler[0] = 1.22522
            if new_cam_name == '02_South':
                camera_object.location = (self.crd[0], self.crd[1] + 600, 300)
                camera_object.rotation_euler[0] = -2.1
                camera_object.rotation_euler[1] = 3.14159
            if new_cam_name == '03_East':
                camera_object.location = (self.crd[0] - 600, self.crd[1], 300)
                camera_object.rotation_euler[0] = 4.3
                camera_object.rotation_euler[2] = 1.71
                camera_object.rotation_euler[1] = 3.14159
            if new_cam_name == '04_West':
                camera_object.location = (self.crd[0] + 600, self.crd[1], 300)
                camera_object.rotation_euler[0] = 4.3
                camera_object.rotation_euler[2] = -1.71
                camera_object.rotation_euler[1] = -3.14159

    def custom_camera_clip_end(self, ob):
        """
        настраиваем clip_start and clip_end в камерах
        """
        if ob != None:
            try:
                if ob.name in self.cam_dict.keys():
                    name_cam = ob.name
                    bpy.data.cameras[name_cam].clip_start = 1
                    bpy.data.cameras[name_cam].clip_end = 900000
            except:
                print('функция custom_camera_clip_end  -  Warning')
                pass

    def custom_camera_background(self):
        try:
            path_to_FGM = ((bpy.context.scene.mrgp.fgm_path).replace('\\', '//').replace('"', ''))
        except:
            path_to_FGM = (r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\03_FGM").replace('\\', '//')

        # получили список текущих камер в сцене
        cur_img_name_sc = [x.name for x in bpy.data.images]

        # перебираем ключи словаря камер в классе
        for x in self.cam_dict.keys():
            if self.cam_dict[x] not in cur_img_name_sc:      # если такой фотки еще не загружено в сцену то грузим
                name_cam = x                                 # получаем имя камеры
                name_foto = self.cam_dict[x]                 # название фото
                file_path = path_to_FGM + "\\" + name_foto   # путь к загружаемой фотоки
                active_cam = bpy.data.cameras.get(name_cam)  # получаем камеру по имени
                bg = active_cam.background_images.new()      # создаём background в камере
                bg.image = bpy.data.images.load(file_path)   # загружаем background в камеру
                active_cam.show_background_images = True     # показываем background в камере

    def customize_cameras_background(self):
        # customize cameras
        [CamSun.custom_camera_clip_end(self, x) for x in bpy.data.objects if x.type == 'CAMERA']  # clip_end
        CamSun.custom_camera_background(self)  # add background image to cameras
        try:
            for x in self.cam_dict.keys():
                y = bpy.data.cameras.get(x)
                y.background_images[0].alpha = 1
        except:
            print('повторный вызов функции сustomize_cameras_background')

    def add_sun_light(self):
        x, y, z = (self.crd[0] + 300, self.crd[1], self.crd[2] + 800)

        light_data = bpy.data.lights.new(name="00_SUN", type='SUN')
        light_object = bpy.data.objects.new(name="00_SUN", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (x, y, z + 100)
        bpy.data.lights["00_SUN"].energy = 11
        bpy.data.lights["00_SUN"].angle = pi * 50.0 / 180.0

    def del_default_sun_cum(self):
        """
        удаляем все камеры и свет если их нет в классе
        """
        for x in bpy.data.cameras:
            if x.name not in self.cam_dict.keys():
                bpy.data.cameras.remove(x)

        for x in bpy.data.lights:
            if x.name != self.sun_name:
                bpy.data.lights.remove(x)


    # декоратор
    def timer_func(func):
        # This function shows the execution time of
        # the function object passed
        def wrap_func(*args, **kwargs):
            t1 = time.time()
            result = func(*args, **kwargs)
            t2 = time.time()
            print(f'Function {func.__name__!r} executed in {(t2 - t1):.4f}s')
            return result
        return wrap_func


    @timer_func
    def run_camsun(self):
        """
        ОСНОВНАЯ ФУНКЦИЯ MAIN для CamSun
        """
        # удаляем все камеры
        [CamSun.del_cam(CamSun.get_cam(x)) for x in bpy.data.objects if x.type == 'CAMERA']

        # удаляем все SUN из сцены
        [CamSun.del_sun(CamSun.get_sun(x)) for x in bpy.data.lights if x.type == 'SUN']

        # получаем координаты выбранного пользователем объекта
        self.crd = CamSun.get_coord_obj(self)

        # создаем камеры и добавляем в сцену
        CamSun.creat_cam(self)

        # настраиваем камеры, устанавливаем FGM на задний фон
        CamSun.customize_cameras_background(self)

        # добавляем солнце
        CamSun.add_sun_light(self)

        # удаляем все камеры и свет если их нет в классе
        CamSun.del_default_sun_cum(self)


class ClearScene:
    @staticmethod
    def clear_scene():
        if bpy.context.selected_objects:
            for obj in bpy.context.selected_objects:
                print(obj.name)
                nm0 = obj.name.split("fid")[0]
                nm1 = obj.name.split("fid")[1].split(".")[0]
                del_nm = nm0+"fid"+nm1

                crv = [x for x in bpy.data.curves if x.name.startswith(del_nm)]
                objs = [x for x in bpy.data.objects if x.name.startswith(del_nm)]
                msh = [x for x in bpy.data.meshes if x.name.startswith(del_nm)]
                for o in objs:
                    print(f"{o.name}  --  удалён объект")
                    bpy.data.objects.remove(o)
                for m in msh:
                    print(f"{m.name}  --  удалена mesh")
                    bpy.data.meshes.remove(m)
                for c in crv:
                    print(f"{c.name}  --  удалена curve")
                    bpy.data.curves.remove(c)


        else:
            for obj in bpy.data.objects:
                bpy.data.objects.remove(obj)

            for m in bpy.data.meshes:
                bpy.data.meshes.remove(m)

            for img in bpy.data.images:
                bpy.data.images.remove(img)

            for cam in bpy.data.cameras:
                bpy.data.cameras.remove(cam)

            for col in bpy.context.blend_data.collections:
                bpy.data.collections.remove(col)

            for crv in bpy.data.curves:
                bpy.data.curves.remove(crv)

            for lt in bpy.data.lights:
                bpy.data.lights.remove(lt)


    def run_clear_scene(self):
        # очищаем все кроме материалов
        ClearScene.clear_scene()


class Settings_scen:
    def __init__(self):
        self.sc_lst = ["Scene", "Scene2"]  # инициируем класс со списком имен двух сцен

    def create_new_scene(self, name_sc: str = "Scene2"):
        """
        создаём новую сцену, если сцена с таким именем существует - пропуск
        """
        if name_sc not in bpy.data.scenes.keys():
            new_sc = bpy.data.scenes.new(name_sc)

    def set_settings_to_scene(self):
        """
        устанавливаем настройки сценам по списку
        """
        for sc in self.sc_lst:
            bpy.data.scenes[sc].render.engine = 'CYCLES'
            bpy.data.scenes[sc].cycles.device = 'GPU'
            bpy.data.scenes[sc].render.film_transparent = True
            bpy.data.scenes[sc].cycles.progressive = 'PATH'
            bpy.data.scenes[sc].cycles.samples = 256
            bpy.data.scenes[sc].cycles.preview_samples = 128
            bpy.data.scenes[sc].render.resolution_x = 3680
            bpy.data.scenes[sc].render.resolution_y = 2600

    def run_scene_settings(self):

        # создаём новую сцену в бленд файле
        Settings_scen.create_new_scene(self, name_sc="Scene2")

        # применяем настройки к сцене
        Settings_scen.set_settings_to_scene(self)


class Border_Scene:

    def new_dimension_LD_TR(self):
        """
        устанавливаем размерность объектов в 3d в двух коллекциях
        """
        bpy.ops.object.select_all(action='DESELECT')
        collection_list = ['5_tr', '6_ld']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.data.dimensions = '3D'

    def new_style_obj_bevel_ass_mat(self):
        """
        назначаем толщину и материалы границам TR LD
        """
        collection_list = ['5_tr', '6_ld']
        # выделяем все объекты коллекции 5_tr
        try:
            for obj in bpy.data.collections['5_tr'].all_objects:
                # obj.select_set(True)
                obj.data.bevel_depth = 1.5                        # задали толщину граничке
                mat = bpy.data.materials.get("TR_GRAN")           # взяли материал из библиотеке
                if bpy.data.materials:                            # назначили материалы выбранным объектам
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
        except:
            pass

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

        # выделяем все объекты коллекции 5_tr
        try:
            for obj in bpy.data.collections['6_ld'].all_objects:
                # obj.select_set(True)
                obj.data.bevel_depth = 2                        # задали толщину граничке

                mat = bpy.data.materials.get("LD_GRAN")         # взяли материал из библиотеке
                if bpy.data.materials:                          # назначили материалы выбранным объектам
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
        except:
            pass

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

    def new_style_obj_smoth_link(self):
        """
        линкуем гранички в новую сцену Scene2 и сглаживаем
        """
        # выделяем все объекты из двух коллекций
        collection_list = ['5_tr', '6_ld']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)
                bpy.ops.object.make_links_scene(scene='Scene2')

        # получаем все выделенные объекты в переменную
        sel_objs = [ob for ob in bpy.context.selected_objects]

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

        collection_list = ['5_tr', '6_ld']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)
                bpy.ops.object.shade_smooth()  # сгладили граничку
                obj.select_set(False)

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

    def new_style_cam_sun_link(self):
        """
        линкуем камеры и солнце в новую сцену
        """
        # создаём ссылки на новую сцену для камер и солнца
        name_for_link = ['00_SUN', '01_North', '02_South', '03_East', '04_West']
        obj_s = [x for x in bpy.data.objects if x.name in name_for_link]
        for ob in obj_s:
            ob.select_set(True)
            bpy.ops.object.make_links_scene(scene='Scene2')
            ob.select_set(False)
            # ob.make_links_scene(scene='S_2')

    def run_border_set(self):

        # устанавливае размерность в 3d
        Border_Scene.new_dimension_LD_TR(self)

        # назначаем толщину и материалы границам TR LD
        Border_Scene.new_style_obj_bevel_ass_mat(self)

        # линкуем гранички в новую сцену Scene2 и сглаживаем
        Border_Scene.new_style_obj_smoth_link(self)

        # линкуем камеры и солнце в новую сцену
        Border_Scene.new_style_cam_sun_link(self)


