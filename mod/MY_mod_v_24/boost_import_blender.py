import time
import subprocess as sp
import os
import pathlib

from itertools import cycle, chain

import re
import mathutils
from mathutils import Vector
import textwrap
import array

import numpy as np
import ast

import osgeo
from osgeo import ogr
import fiona

import geopandas as gpd
from geopandas.tools import overlay
import shapely
from shapely import wkt
from shapely.ops import linemerge, unary_union, polygonize, triangulate
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon

import pandas as pd

from matplotlib import pyplot as plt

import scipy
from scipy.spatial import delaunay_plot_2d, voronoi_plot_2d, Delaunay

import bpy
import math
import mathutils
from mathutils import *
from mathutils.geometry import tessellate_polygon, delaunay_2d_cdt

from shapely import speedups
speedups.disable()


class NeedFastLoadInBlender:
    def __init__(self, path_gpkg):
        self.path_to_GPKG: str = path_gpkg  # путь к gpkg
        self.ds = None  # osgeo.ogr.DataSource
        self.dict_ds: dict = {}  # словарь с ds отфильтрованных по wkt
        self.dict_ds_mem: dict = {}  # словарь с ds скопировали в память
        self.dict_df: dict = {}  # словарь DataFrames pandas
        self.dict_gdf: dict = {}  # словарь GeoDataFrames geopandas
        self.ds_mem: dict = {}  # DataSource со слоями
        self.str_layer_grn: str = 'GRANICA_OBREZKI'  # слой в котором граничка лежит
        self.col_filtr_name: str = "GR_OBREZKI"  # название колонки для фильтрации в слое где граничка обрезки
        self.col_split_name: str = "t_from_contents"  # название колонки для фильтрации по слоям
        self.name_granica: str = ""  # название гранички обрезки
        self.tmp_path_fldr: str = ""  # путь к временному каталогу
        self.lst_src_layer: dict = {
            "bld_pr": 'total_building_pr',
            "lnd_pr": 'total_a_landscaping_pr',
            "road_s": 'ROAD_POLY',
            "bld_s": 'BUILDING',
            "tr": 'total_terr_razvitie',
            "ld": 'ld_region'}  # словарь слоёв с которыми работаем

    # декоратор время
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

    def open_file_by_gdal(self):
        """открываем file GDAL - ом по пути """
        self.ds = ogr.Open(self.path_to_GPKG, 1)

    @staticmethod
    def filter_by_coordinate(name_granica: str, name_column: str, name_f_layer: str, nm_lr_for_flt: str,
                             ds: osgeo.ogr.DataSource) -> osgeo.ogr.DataSource:
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

    def get_dict_from_ds(self):
        """
        получаем словарь отфильтрованых datasource по каждому слою
        """
        for i in self.lst_src_layer.keys():
            self.dict_ds[i] = self.filter_by_coordinate(
                name_granica=self.name_granica,
                name_column=self.col_filtr_name,
                name_f_layer=self.str_layer_grn,
                nm_lr_for_flt=self.lst_src_layer[i],
                ds=self.ds
            )

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

    def save_dict_of_lrs_to_mem(self):
        """
        сохраняем datasource gdal в оперативке (в словаре DataSources)
        """
        for i in self.dict_ds.keys():
            self.dict_ds_mem[i] = self.save_lr_to_mem(self.dict_ds[i], i)

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
        self.ds_mem = ds_mem

    def lr_to_dataframe(self) -> dict:
        '''
        перегоняем слои из DataSource в словарь pandas dataframes с инфой по семантике и геометрией
        '''

        rslt_dic = {}  # словарь для сбора результатов
        for lr in self.ds_mem:

            if isinstance(lr, osgeo.ogr.Layer) != True:
                ms = (u' ERROR - !!!! Полученные данные не являются слоем gdal.ogr')
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
        self.dict_df = rslt_dic

    def pandas_to_geopandas(self) -> dict:
        '''
        перегоняем словарь с pandas dataframes в словарь geodataframes
        '''
        apu_src = r"+proj=tmerc +lat_0=55.66666666667 +lon_0=37.5 +k=1 +x_0=12 +y_0=14 +ellps=bessel +towgs84=316.151,78.924,589.65,-1.57273,2.69209,2.34693,8.4507 +units=m +no_defs"
        dict_result = {}
        for x, y in self.dict_df.items():
            gs = gpd.GeoSeries.from_wkt(y['geometry'])
            dict_result[x] = gpd.GeoDataFrame(y, geometry=gs, crs=apu_src)
            # geo_pdf = gpd.GeoDataFrame(pd)
        self.dict_gdf = dict_result

    @staticmethod
    def create_new_column_whith_len_geom(new_name_column, gdf_obj):
        gdf_obj[new_name_column] = gdf_obj['geometry'].apply(lambda x: len(str(x)))

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

    def get_dict_from_wkt(self, wkt_str: str) -> dict:
        """
        получаем из координат wkt мультиполигона словарь
        структура словаря:

        мультиполигон
                     полигон
                            кольца
                                  x - координаты
                                  y - координаты

        """
        # подключаем регулярку
        # паттерн поиска мультиполигонов
        patt_mult = r"(?:\({3}.*?\){3})"
        # паттерн поиска полиогонов
        patt_poly = r"(?:\({2}.*?\){2})"
        # паттерн поиска колец в полигоне
        patt_ring = r"(?:\({1}.*?\){1})"

        rslt_mult = re.findall(patt_mult, wkt_str)
        dic_rslt = {}

        # цикл по мультиполигонам)
        for x, mult in enumerate(rslt_mult):
            rslt_poly = re.findall(patt_poly, mult)
            # dic_rslt[x] = [f"count_multPoly| {len(rslt_poly)}"]

            poly_dic = {}
            # цикл по полигонам
            for y, poly in enumerate(rslt_poly):
                rslt_path = re.findall(patt_ring, poly)

                rng = {}
                # цикл по границам (ring)
                for z, pth in enumerate(rslt_path):

                    chr_replace = ['(', ')', ',']
                    for ch in chr_replace:
                        pth = pth.replace(ch, "")

                    pth = pth.split(' ')

                    x_crd = [v for k, v in enumerate(pth) if not k % 2]
                    y_crd = [v for k, v in enumerate(pth) if k % 2]

                    rng[z] = (x_crd, y_crd)

                poly_dic[y] = rng

            dic_rslt[x] = poly_dic

        return dic_rslt

    def get_list_layers_gpkg_fiona(self, f_path):
        """
        получаем список слоёв при помощи фиона fiona
        """
        return fiona.listlayers(f_path)

    @staticmethod
    def create_new_column_whith_count_geoms(new_name_column, gdf_obj):
        gdf_obj[new_name_column] = gdf_obj['geometry'].apply(
            lambda x: len([y for y in x.geoms])
        )

    @staticmethod
    def triangulate_from_wkt(wkt_crd: str) -> gpd.GeoDataFrame:
        '''
        получаем геодатафрэйм из триангулированных полигонов отфильтрованных по граничке
        !!! если последовательнос соединить точки pts - будет граница полигона
        pts     -  точки numpy массив последовательных точек (граница полигона)
        '''
        poly_from_wkt = wkt.loads(wkt_crd)  # создаем SHAPELY геометрию
        tri = triangulate(poly_from_wkt)
        tri_list = []
        for t in tri:
            if len(poly_from_wkt.geoms) == 1:
                if len(poly_from_wkt.boundary.geoms) > 1:
                    base_crd = Polygon(poly_from_wkt.boundary.geoms[0].coords)
                    if not t.centroid.within(base_crd):
                        continue
                    for x in range(len(poly_from_wkt.boundary.geoms)-1):
                        hole_crd = Polygon(poly_from_wkt.boundary.geoms[x + 1].coords)
                        # if not t.centroid.within(hole_crd):
                        if hole_crd.within(t):
                            break
                        if not hole_crd.within(t):
                            continue
                    tri_list.append(t)

        gdf_base = gpd.GeoDataFrame(base_crd)  # trian - это лист shapely полигонов !!!
        gdf_base = gdf_base.set_geometry(base_crd)  # устанавливем геомтрию
        # gdf_base.plot()

        gdf_trian = gpd.GeoDataFrame(tri_list)  # trian - это лист shapely полигонов !!!
        gdf_trian = gdf_trian.set_geometry(tri_list)  # устанавливем геомтрию
        # gdf_trian.plot()

        base = gdf_base.plot(color="white", alpha=.8, edgecolor="black", linewidth=3, figsize=(20, 20))
        # tri_gdf2.plot(ax=base, color="white", edgecolor="red", linewidth=0.8, zorder=1)
        gdf_trian.plot(ax=base, color="none", edgecolor="red", linewidth=0.8, zorder=1)
        # tri_gdf2.plot(color="white", edgecolor="red", linewidth=0.8, zorder=-1)
        plt.show()



        poly_from_wkt_OGR = ogr.CreateGeometryFromWkt(wkt_crd)  # создаем OGR геометрию
        pl_ogr = ogr.ForceToPolygon(poly_from_wkt_OGR)
        tri_ogr = pl_ogr.DelaunayTriangulation()
        tri_ogr_filter = [tri for tri in tri_ogr if tri.Within(pl_ogr)]

        tri_ogr = [triangle for triangle in ogr.ForceToPolygon(poly_from_wkt_OGR) if triangle.Within(poly_from_wkt_OGR)]
        tri_ogr = pl_ogr.DelaunayTriangulation()



        # # можно посмотреть созданный полигон
        # x, y = poly_from_wkt.exterior.xy
        # plt.plot(x, y)
        # plt.show()

        # триангулируем и берем полигоны только внутри исходного
        trian = [triangle for triangle in triangulate(poly_from_wkt) if triangle.within(poly_from_wkt)]
        # переносим треангулированные объекты в геодатафрэйм + назначаем поле геометрии
        gdf_trian = gpd.GeoDataFrame(trian)  # trian - это лист shapely полигонов !!!
        gdf_trian = gdf_trian.set_geometry(trian)  # устанавливем геомтрию
        gdf_trian.rename(columns={0: 'xy'}, inplace=True)
        gdf_trian['xy'] = [x.exterior.xy for x in gdf_trian['geometry']]
        # gdf_trian[0] = ''
        # it_obj = geom.Boundary().GetPoints()
        # x, y = zip(*it_obj)
        # # визуализируем геодатафрэйм
        # gdf_trian.plot()
        # plt.show()
        return gdf_trian


if __name__ == '__main__':
    # путь к gpkg
    path_gpkg = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg"

    # инициируем класс
    wr = NeedFastLoadInBlender(path_gpkg)

    # получаем спиок слоёв в gpkg
    list_layers = wr.get_list_layers_gpkg_fiona(path_gpkg)

    # загружаем слой 'GRANICA OBREZKI' в geopandas
    gr_obr = gpd.read_file(path_gpkg, layer='GRANICA_OBREZKI')

    # получаем geodataframe только с граничкой по которой фильтруем
    mask_gdf = gr_obr.loc[gr_obr["GR_OBREZKI"] == "2"]

    # загружаем весь gpkg в словарь из geopandas
    dict_gpd = {}
    for x, y in enumerate(list_layers):
        if y != "layer_styles":
            dict_gpd[y] = gpd.read_file(path_gpkg, layer=y, mask=mask_gdf[mask_gdf["GR_OBREZKI"] == "2"])














    # выбираем geodataframe из словаря
    cur_gdf = dict_gpd['total_a_landscaping_pr']

    # добавляем колонку с длиной геометрии (длина текста)
    wr.create_new_column_whith_len_geom("len_geom", cur_gdf)

    # объект с которым работать будем, максимальной длины геометрия
    gdf = cur_gdf.loc[cur_gdf["len_geom"] == cur_gdf["len_geom"].max()]

    # получаем wkt в строку
    geom_str = gdf.geometry.values[0].to_wkt()

    # gdf_fun = wr.triangulate_from_wkt(geom_str)


    # создаём геометрию из wkt координат
    # str_wkt = "Polygon ((6790.0 7390.0, 6135.0 7930.0, 7235.0 8000.0, 6790.0 7390.0),(6530.0 7770.0, 6395.0 7844.0, 6591.0 7837.0, 6530.0 7770.0),(6894.0 7801.0, 7056.0 7892.0, 6835.0 7893.0, 6894.0 7801.0))"
    # mult = wkt.loads(str_wkt)
    mult = wkt.loads(geom_str)

    # пример полигона
    # pl_wkt = "Polygon((6790.0 7390.0, 6135.0 7930.0, 7235.0 8000.0, 6790.0 7390.0))"
    # pl_wkt = "Polygon((6790.0 7390.0, 6135.0 7930.0, 7235.0 8000.0, 6790.0 7390.0),(6530.0 7770.0, 6395.0 7844.0, 6591.0 7837.0, 6530.0 7770.0))"
    pl_wkt = "Polygon((6790.0 7390.0, 6135.0 7930.0, 7235.0 8000.0, 6790.0 7390.0),(6530.0 7770.0, 6395.0 7844.0, 6591.0 7837.0, 6530.0 7770.0), (6894.0 7801.0, 7056.0 7892.0, 6835.0 7893.0, 6894.0 7801.0))"
    pl_wkt2 = "Polygon((7528.0 7374.0, 7527.0 7468.0, 7620.0 7470.0, 7620.0 7376.0, 7528.0 7374.0), (7552.0 7456.0,7552.0 7437.0, 7569.0 7437.0, 7568.0 7454.0, 7552.0 7456.0))"
    pl_wkt3 = "Polygon((7528.0 7374.0, 7527.0 7468.0, 7620.0 7470.0, 7620.0 7376.0, 7528.0 7374.0))"

    pl = wkt.loads(geom_str)

    ## получаем координаты
    # xc, yc = pl.boundary.xy  # если просто одна граница
    # получаем координаты
    xcrd, ycrd = [], []
    for geom in pl.boundary.geoms:
        for xx in geom.xy[0]:
            xcrd.append(xx)
        for yy in geom.xy[1]:
            ycrd.append(yy)

    aa = np.array(list(zip(xcrd, ycrd)))
    vs_2d = [Vector((x, y)) for x, y in aa]
    vs_3d = [(v.to_3d()) for v in vs_2d]
    pol = tessellate_polygon([vs_3d])

    es = []
    for geom in pl.boundary.geoms:
        pl_pts = np.array(geom.coords)
        l_pts = []
        for x in range(len(pl_pts)):
            l_pts.append(np.where(aa == pl_pts[x])[0][1])
        es.append(l_pts)

    es_list = []
    for l in es:
        for x, y in enumerate(l[:-1]):
            es_list.append(tuple((y, l[x + 1])))


    verts, edges, faces, _, _, _ = delaunay_2d_cdt(vs_2d, es_list, es, 2, 1e-5)
    # verts, edges, faces, _, _, _ = delaunay_2d_cdt(vs_2d, es_list, pol, 2, 1e-5)

    # vs_3d = [(v.to_3d()) for v in verts]
    vs_3d = [(v.to_3d()) for v in verts]

    mesh = bpy.data.meshes.new(name='tost5')
    # mesh.from_pydata(vs, [], pol)
    mesh.from_pydata(vs_3d, [], faces)
    mesh.update()













    vs = [Vector((x, y)) for x, y in aa_unic]  # переводим координаты в вектор
    vs = [(v.to_3d()) for v in vs]        # переводим координаты 2d в 3d размерность, добавляем z=0

    pol = tessellate_polygon([vs])

    # триангуляция
    # mult_tri1 = [shapely.ops.triangulate(x) for y in gdf.geometry.values for x in y]
    # mult_tri2 = [shapely.ops.triangulate(x) for x in gdf.geometry.values]
    # mult_tri3 = shapely.ops.triangulate(mult)
    mult_tri = shapely.ops.triangulate(pl2)

    # из shapely в geoseries
    # g = gpd.GeoSeries([mult])
    # g = gpd.GeoSeries([mult_tri])
    g = gpd.GeoSeries(mult_tri)
    # g1 = gpd.GeoSeries(mult_tri1[0])
    # g2 = gpd.GeoSeries(mult_tri2[0])
    # g3 = gpd.GeoSeries(mult_tri3)

    # создаём geodataframe из geosiries с переименованием колонки !!!!!!!!
    tri_gdf = gpd.GeoDataFrame(g)
    tri_gdf = tri_gdf.rename(columns={0: 'geometry'}).set_geometry('geometry')

    # визуализируем
    tri_gdf.plot(edgecolor="black", linewidth=1)
    plt.show()

    mesh = bpy.data.meshes.new(name='tost')
    mesh.from_pydata(vs, [], pol)
    mesh.update()







    xc, yc = pl.boundary.xy  # если просто одна граница
    xc, yc = [], []
    for y in pl.boundary:
        for x in y.xy[0][:-1]:
            xc.append(x)

    for y in pl.boundary:
        for x in y.xy[1][:-1]:
            yc.append(x)





    # получаем координаты
    xc, yc = gdf.geometry.values[0].geoms[0].boundary[0].xy
    xc, yc = gdf.geometry.values[0].geoms[0].boundary[0].xy
    aa = np.array(list(zip(xc, yc)))
    vs = [Vector((x, y)) for x, y in aa]
    es = [(i, i + 1) for i in range(0, (aa.shape[0])-1)]
    verts, edges, faces, _, _, _ = delaunay_2d_cdt(vs, es, [], 2, 1e-5)
    # verts, edges, faces, overts, oedges, ofaces = delaunay_2d_cdt(vs, [], [], 0, 0.1)

    vs = [(v.to_3d()) for v in verts]
    ed = [[vs[i1], vs[i2]] for i1, i2 in edges]

    pol = tessellate_polygon([vs])

    mesh = bpy.data.meshes.new(name='tost')
    mesh.from_pydata(vs, [], pol)
    mesh.update()

    bpy.ops.wm.save_as_mainfile(
        filepath=r"C:\Users\Alex\Desktop\tester999.blend")



    mesh.from_pydata(verts, edges, faces)
    # Update mesh geometry after adding stuff.
    mesh.update()


    # получаем кол-во составной геометрии в объекте и загоняем в столбец !!!!!!!! НЕ ПРОВЕРЕНА ДО КОНЦА !!!!!!!!!!
    gms = len([x for x in gdf.geometry.values[0].geoms])
    wr.create_new_column_whith_count_geoms("count_geoms", cur_gdf)

    # получаем координаты рамки описанную вокруг данной геометрии
    bound = gdf.geometry.values[0].bounds

    # получаем координаты из одного из колец объекта
    xc, yc = gdf.geometry.values[0].geoms[0].boundary[0].xy
    xv, yv = gdf.geometry.values[0].geoms[0].boundary[0].coords.xy

    # генератор по каждой геометрии из которых состоит объект
    [(x.geometryType()) for x in gdf.geometry.values[0].geoms]


    # триангуляция
    # mult_tri1 = [shapely.ops.triangulate(x) for y in gdf.geometry.values for x in y]
    # mult_tri2 = [shapely.ops.triangulate(x) for x in gdf.geometry.values]
    # mult_tri3 = shapely.ops.triangulate(mult)
    mult_tri = shapely.ops.triangulate(mult)



    # # фильтрация только тех треугольников которые пересекают исходный объект
    # tri = []
    # for triangle in triangulate(mult):
    #     if mult.intersects(triangle):
    #         tri.append(triangle)



    # mult_tri = shapely.ops.triangulate(mult, tolerance=1)
    # tri = [triangle for triangle in triangulate(mult) if triangle.centroid.within(mult)]
    # tri = [triangle for triangle in triangulate(mult) if mult.covers(triangle.centroid)]
    # tri = [triangle for triangle in triangulate(mult) if mult.within(triangle.centroid)]
    # tri = [triangle for triangle in triangulate(mult) if triangle.covers(gdf['geometry'].geometry.values[0])]
    # # tri = [triangle for triangle in triangulate(mult) if triangle.centroid.intersects(gdf['geometry'].geometry.values[0])]
    # # tri = [triangle for triangle in triangulate(mult) if triangle.centroid.intersects(gdf['geometry'].geometry.values[0])]
    # tri = [tngl for tngl in mult_tri if tngl.centroid.buffer(distance=1).intersects(mult)]


    # получаем словарь с координатами объекта
    dic_from_wkt = wr.get_dict_from_wkt(geom_str)

    # # объединяем полигоны в мультиполигон
    # polygons_tri = shapely.geometry.MultiPolygon([x for x in mult_tri])

    # из shapely в geoseries
    # g = gpd.GeoSeries([mult])
    # g = gpd.GeoSeries([mult_tri])
    g = gpd.GeoSeries(mult_tri)
    # g1 = gpd.GeoSeries(mult_tri1[0])
    # g2 = gpd.GeoSeries(mult_tri2[0])
    # g3 = gpd.GeoSeries(mult_tri3)

    # создаём geodataframe из geosiries с переименованием колонки !!!!!!!!
    tri_gdf = gpd.GeoDataFrame(g)
    tri_gdf = tri_gdf.rename(columns={0: 'geometry'}).set_geometry('geometry')
    #
    # tri_gdf1 = gpd.GeoDataFrame(g1)
    # tri_gdf1 = tri_gdf1.rename(columns={0: 'geometry'}).set_geometry('geometry')
    #
    # tri_gdf2 = gpd.GeoDataFrame(g2)
    # tri_gdf2 = tri_gdf2.rename(columns={0: 'geometry'}).set_geometry('geometry')
    #
    # tri_gdf3 = gpd.GeoDataFrame(g3)
    # tri_gdf3 = tri_gdf3.rename(columns={0: 'geometry'}).set_geometry('geometry')

    # # приводим к единой системе координат (EGKO)
    crs = gdf.crs
    tri_gdf['geometry'].crs = crs
    tri_gdf.crs = crs

    # # получаем пересечение геометрии!!!!
    gdf1 = gdf.copy()
    tri_gdf1 = tri_gdf.copy()

    gdf1 = gdf1.to_crs(4326)
    tri_gdf1 = tri_gdf1.to_crs(4326)

    res_difference = overlay(gdf1, tri_gdf1, how='intersection')
    res_difference = overlay(gdf1, tri_gdf1, how='intersection', keep_geom_type=False)
    res_difference = gpd.overlay(gdf, tri_gdf, how='symmetric_difference')
    res_difference = gpd.overlay(gdf, tri_gdf, how='union')
    res_difference2 = gpd.overlay(res_difference, tri_gdf, how='symmetric_difference')


    # визуализируем несколько gpd
    base = gdf.plot(color="none", alpha=.8, edgecolor="black", linewidth=2, figsize=(20, 20))
    # base = tri_gdf.plot(color="Greys", alpha=.8, edgecolor="black", linewidth=2, figsize=(20, 20))
    # base = tri_gdf1.plot(color="white", alpha=.8, edgecolor="black", linewidth=5, figsize=(20, 20))
    tri_gdf.plot(ax=base, color="none", edgecolor="red", linewidth=1, zorder=1)
    # tri_gdf2.plot(ax=base, color="none", edgecolor="red", linewidth=0.8, zorder=1)
    # # tri_gdf2.plot(color="white", edgecolor="red", linewidth=0.8, zorder=-1)
    plt.show()


    # # приводим к единой системе координат (EGKO)
    crs = gdf.crs
    tri_gdf['geometry'].crs = crs
    tri_gdf.crs = crs

    # # получаем пересечение геометрии!!!!
    res_difference = gpd.overlay(gdf, tri_gdf, how='symmetric_difference')
    res_difference2 = gpd.overlay(res_difference, tri_gdf, how='symmetric_difference')

    # # получаем пересечение триангуляции и базовым объектом
    # # res_intersection = tri_gdf.overlay(gdf, how='intersection')
    # # res_difference = gpd.overlay(tri_gdf, gdf, how='identity')
    # res_difference = gpd.overlay(gdf, tri_gdf, how='intersection')

    # # визуализируем matplotlib
    # # cmap='BuPu' 'OrRd' 'GnBu' 'Blues' 'Greys'
    # # facecolor='#C2C2C2'  linewidth=0.1  edgecolor='red'
    # # g.plot()
    # # res_difference.plot(figsize=(50, 50), color='green', edgecolor='k')
    # # res_difference.plot(figsize=(50, 50), cmap='Greys', linewidth=0.1,  edgecolor='red')
    # res_difference.plot(figsize=(20, 20), facecolor='#C2C2C2', linewidth=0.1,  edgecolor='red')
    # # g.plot(color='green', edgecolor='k')
    # # g.plot(color='none', edgecolor='k')
    # plt.show()

    print('stop')













    # получаем кол-во составной геометрии в объекте и загоняем в столбец !!!!!!!! НЕ ПРОВЕРЕНА ДО КОНЦА !!!!!!!!!!
    gms = len([x for x in gdf.geometry.values[0].geoms])
    wr.create_new_column_whith_count_geoms("count_geoms", cur_gdf)

    # получаем координаты рамки описанную вокруг данной геометрии
    bound = gdf.geometry.values[0].bounds

    # получаем координаты из одного из колец объекта
    xc, yc = gdf.geometry.values[0].geoms[0].boundary[0].xy
    xv, yv = gdf.geometry.values[0].geoms[0].boundary[0].coords.xy

    # генератор по каждой геометрии из которых состоит объект
    [(x.geometryType()) for x in gdf.geometry.values[0].geoms]

    # изменение размера фигуры
    dict_gpd['ROAD_POLY'].plot(figsize=(50, 50))













    wr.open_file_by_gdal()  # открываем gdal-ом gpkg
    wr.name_granica = "2"  # назначаем граничку объекта по которому фильтруем
    wr.get_dict_from_ds()  # получаем словарь ds отфильтрованных по граничке
    wr.save_dict_of_lrs_to_mem()  # переросим словарь с отдельными ds по слоям - в память пк
    wr.save_Dict_With_Ds_To_Mem()  # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
    wr.lr_to_dataframe()  # перегоняем DataSource в DataFrame
    wr.pandas_to_geopandas()  # словарь pandas Dataframe -> словарь GeoPandas GeoDataFrame

    # срез по геодатафрэйму только нужных столбиков
    cur_gdf = wr.dict_gdf['lnd_pr'].loc[:, (wr.col_split_name, "geometry")]

    # добавляем колонку с длиной геометрии (длина текста)
    wr.create_new_column_whith_len_geom("len_geom", cur_gdf)

    # объект с которым работать будем, максимальной длины геометрия
    # gdf = cur_gdf.loc[cur_gdf["len_geom"] == 17628]
    gdf = cur_gdf.loc[cur_gdf["len_geom"] == cur_gdf["len_geom"].max()]

    # путь к рабочему столу
    path_descktop = pathlib.Path.home() / "Desktop"
    # tmp_dir = f"{path_descktop}"

    # получаем wkt в строку
    geom_str = gdf.geometry.values[0].to_wkt()
    # создаём геометрию из wkt в shapely
    geom_shapely = wkt.loads(geom_str)

    # получаем словарь с координатами объекта
    dic_from_wkt = wr.get_dict_from_wkt(geom_str)

    # txt_wkt = r"MULTIPOLYGON(((11 -17, -8 -1, 14 -8, 18 -17, 3 -11, 0 18, -17 -12, -17 -10, -10 -13))), (((11 -17, -8 -1, 14 -8, 18 -17, 3 -11, 0 18, -17 -12, -17 -10, -10 -13)))"

    wr.export_wkt_to_svg(geom_str, path_descktop, 'vot.svg')

    # цвет шестнадцатиричный
    clr_hex = "#D0D0D0"
    sv = geom_shapely.svg(fill_color=clr_hex)  # экспорт в svg

    print("stop")


    # визуализируем объект
    # ax = gdf.plot(figsize=(10, 10), alpha=1)
    fig, axs = plt.subplots()
    axs.set_aspect('equal', 'datalim')
    gg = gdf.geometry.values[0].to_wkt()
    geom_shap = wkt.loads(gg)
    clr_hex = "#D0D0D0"
    sv = geom_shap.svg(fill_color=clr_hex)

    for geom in geom_shap:
        xs, ys = geom.exterior.xy
        axs.fill(xs, ys, alpha=0.5, fc='r', ec='none')
    plt.show()

    fig11, ax1 = plt.subplots(figsize=(15, 15))
    gdf.plot(ax=ax1)
    gdf.plot(column='len_geom', ax=ax1, legend=True)
    plt.show()

    # gdf.plot("len_geom", cmap="Blues")
    # print("stop")
