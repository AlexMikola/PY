"""# -*- coding: utf-8 -*-"""
import os
import pathlib
import bpy

import osgeo
from osgeo import *

import numpy as np
import pyvista as pv
import pandas as pd
import geopandas as gpd
from osgeo import ogr

import matplotlib.pyplot as plt
import triangle as tr
from descartes import PolygonPatch

import geojson as gjs

import shapely
from shapely import wkt
from shapely.ops import linemerge, unary_union, polygonize, triangulate
from shapely.geometry import LineString
from shapely.geometry import Polygon
from shapely.geometry import MultiPolygon



import trimesh
# import openmesh as om
#for windows users
from shapely import speedups
speedups.disable()


# import sys
# sys.path.append(r'C:\!_Python\_Enviroment\py39\Lib\site-packages\earcut')
# # import earcut
# # from earcut import *
# from earcut.earcut import *
# from earcut.earcut import earcut as ecut_tri
# from earcut.earcut import flatten as flt
# from earcut.earcut import unflatten


class My_class:

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

        # отфильтравали по значению атрибута, по названию полигона получили его объект в фильтре (в слое)
        layer_granica_obrezki.SetAttributeFilter("GR_OBREZKI = %r" % name_granica_obrezki)

        # получаем WKT координаты из отфильтрованной выборки
        for feature in layer_granica_obrezki:
            geom = feature.GetGeometryRef()
            wkt = geom.ExportToWkt()

        layer_building_pr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))  # отфильтровали застройку по полигону
        layer_landscaping_pr.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))  # отфильтровали landscaping по полигону

        layer_susch_building.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))  # отфильтровали сущ застр по полигону
        layer_susch_road.SetSpatialFilter(ogr.CreateGeometryFromWkt(wkt))  # отфильтровали сущ дороги по полигону

        return layer_building_pr, layer_landscaping_pr, layer_susch_building, layer_susch_road

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
    def split_gdf_by_unic_val_colum(clm_name, gdf_source):
        # функция возвращает словарь фрэймов из фрэйма на основании уникальных знаений одной колонки
        # получили уникальные значения колонки из датафрэйма
        unic_list_contents = set([p for p in gdf_source[clm_name]])

        dic_gdf = {}
        for x in unic_list_contents:
            dic_gdf[x] = gdf_source.loc[gdf_source[clm_name] == x]

        return dic_gdf

    @staticmethod
    def see_plot_by_list_shapely_polygons(list_shapely_polygons):
        # визуально смотрим что за полигон (по списку полигонов)
        for ii, pl in enumerate(list_shapely_polygons):  # цикл по каждому полигону в мультиполигоне
            x, y = pl.exterior.xy  # получаем координаты полигона
            plt.plot(x, y, label=(ii))
        plt.show()

    @staticmethod
    def get_triangl_list_coords_edges(points_coords):
        # функция возвращает список полигонов и список ребер faces треугольников
        # с учетом того что треугольники находятся внутри полигона созданного по исходным точкам
        poly = Polygon(points_coords)                   # создали полигон из исходного списка точек
        triangles = shapely.ops.triangulate(poly)       # триангулировали полигон
        mult_poly = MultiPolygon(triangles)             # получили мультиполигон после триангуляции
        # triangles_gdf = gpd.GeoDataFrame()              # создали пустой геодатафрэйм
        # triangles_gdf.geometry = [poly]                 # добавили в геодатафрэйм геометрию
        arr_pts = np.array(points_coords)               # создали np массив с точкам для получения нумерации точек faces
        outmulti = []                                   # создали пустой список для координат ребер
        for ii, pl in enumerate(mult_poly):             # цикл по каждому полигону в мультиполигоне
            if poly.contains(pl) == True:               # проверка входит ли полиго в полигон
                # x, y = pl.exterior.xy                   # получаем координаты полигона
                # plt.plot(x, y, label=(ii))
                # plt.show()
                pl_pts = np.array(pl.exterior.coords)   # массив координат точек текущего полигона
                l_pts = []
                for x in range(len(pl_pts)-1):
                    # l_pts.append(np.where(arr_pts == (pl_pts[x])[..., np.newaxis])[1])
                    l_pts.append(np.where(arr_pts == pl_pts[x])[0][1])
                outmulti.append((pl, l_pts))                     # добавляем полигон в список
        return outmulti

    @staticmethod
    def is_it_polygon_in_wkt(pts_wkt):
        # возвращает строк с координатами wkt если геометрия описывает полигон одиночный
        # создаем геометрию через OGR
        geom = ogr.CreateGeometryFromWkt(pts_wkt)

        # перегоняем мультиполигон в полигон !!!!!!!!!!
        geom = ogr.ForceToPolygon(geom)

        # проверяем количество геометрий и в результате конвертации правильно ли название геометрии IsValid???
        if (geom.IsValid()) == True and geom.GetGeometryCount() == 1:
            # то есть в WKT записан один полигон и всё

            # получаем координаты через итерируемые объекты zip
            it_obj = geom.Boundary().GetPoints()
            # x, y = zip(*it_obj)
            return it_obj

        elif geom.GetGeometryCount() != 1:
            return False

    @staticmethod
    def tri_from_2d_point(pts):
        # получаем триангулированный геодатафрэйм из точек numpy array одиночного полигона
        poly_from_wkt = Polygon(pts)  # создаем shapely полигон

        # # можно посмотреть созданный полигон
        # x, y = poly_from_wkt.exterior.xy
        # plt.plot(x, y)
        # plt.show()

        # триангулируем и берем полигоны только внутри исходного
        trian = [triangle for triangle in triangulate(poly_from_wkt) if triangle.within(poly_from_wkt)]
        # переносим треангулированные объекты в геодатафрэйм + назначаем поле геометрии
        gdf_trian = gpd.GeoDataFrame(trian)
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

    @staticmethod
    def create_mesh_by_extrude_list_pts(var, h_extrude):
        # функция возвращае mesh по точкам

        # добавляем  третий пустой столбец к массиву точек
        points_for_extr = np.pad(var, [(0, 0), (0, 1)])

        # получаем точки по координатам
        x = points_for_extr[:, 0]
        y = points_for_extr[:, 1]
        z = points_for_extr[:, 2]

        # создаем структурированный mesh модулем Pyvista
        grid = pv.StructuredGrid(x, y, z)
        # grid.plot()

        # екструдим модулем Pyvista
        geom = grid.extract_surface()
        mesh_extr = geom.extrude([0, 0, h_extrude])
        return mesh_extr

    @staticmethod
    def boolean_mesh_different(base_mesh, del_mesh):
        # функция возвращает меш после вырезания одного меша из другого
        result = base_mesh.boolean_difference(del_mesh)
        return result

    @staticmethod
    def create_top_button_meshes_by_pts_fcs(pts, fcs, h_obj):
        # получаем два mesha по точкам, граням, высоте объекта
        # добавляем z = 0
        points_3d_z_zero = np.pad(pts[:-1], [(0, 0), (0, 1)])
        points_3d_z_hm = points_3d_z_zero.copy()
        points_3d_z_hm[:, 2] = h_obj

        # создаем tri-mesh стандартными средствами pyvista
        but = pv.make_tri_mesh(points_3d_z_zero, np.array(fcs))
        top = pv.make_tri_mesh(points_3d_z_hm, np.array(fcs))
        # but.plot(show_edges=True)
        # top.plot(show_edges=True)

        return but, top

    @staticmethod
    def merge_meshes_by_list_meshes(list_meshes):
        # объединяем каждый mesh из списка через merge
        mesh_un = pv.PolyData()
        obj = mesh_un.merge(list_meshes)
        full_geom = obj.extract_geometry()
        return full_geom

    @staticmethod
    def save_mesh_as_stl_to_folder(file_mesh, path, name_file):
        # сохраняет mesh как stl file в папку
        file_mesh.save(f'{path}/{name_file}', binary=False)

    @staticmethod
    def create_mesh_from_polygon_wkt(obj_from_wkt_ogr, name_t_from_con):
        # создаем mesh из простого полигона

        geom_polygon = ogr.ForceToPolygon(obj_from_wkt_ogr)     # переводим в полигон
        it_obj = geom_polygon.Boundary().GetPoints()            # получаем картежи точек
        tri = My_class.tri_from_2d_point(np.array(it_obj))      # триангулируем точки одиночного полигона

        # получаем вертексы треангулированного полигона
        vrts = []
        for ii in range(len(tri['geometry'])):
            # fnd_pts.append(list(zip(*tri['geometry'][ii].exterior.xy)))
            vrts.append(list(zip(*tri['geometry'][ii].exterior.xy))[:-1])

        # получаем список faces текущего объекта по индексам списка точек и треангулированного полигона
        fcs = []
        for ii in range(len(vrts)):
            fcs.append([it_obj.index(x) for x in vrts[ii]])

        # получаем экструдированный mesh по точкам полигона
        h_obj = float(name_t_from_con.split('_')[2])  # высота экструдии
        mesh_extr = My_class.create_mesh_by_extrude_list_pts(it_obj, h_obj)

        # получаем крышку и дно в виде мешей
        but_mesh, top_mesh = My_class.create_top_button_meshes_by_pts_fcs(it_obj, fcs, h_obj)

        # объединяем meshes
        full_mesh = My_class.merge_meshes_by_list_meshes([mesh_extr, but_mesh, top_mesh])

        return full_mesh

    @staticmethod
    def cut_polygon_by_line_shepely(polygon, line):
        merged = linemerge([polygon.boundary, line])
        borders = unary_union(merged)
        polygons = polygonize(borders)
        return list(polygons)

    @staticmethod
    def unflatten_var(data, dim=3):
        result = []

        for i in range(0, len(data), dim):
            result.append(tuple(data[i:i + dim]))

        return result


    @staticmethod
    def parse_by_wkt(name_t_from_con, gdf_source, lst_not_worked_obj):

        cur_gdf = gdf_source.loc[:, ('t_from_contents', 'geometry')]  # срез по геодатафрэйму только нужных столбиков
        cur_gdf['index'] = cur_gdf.index  # присваиваем значения индексов колонке
        cur_gdf = cur_gdf.loc[:, ('index', 't_from_contents', 'geometry')]  # упорядочили колонки по списку

        # цикл по каждой строке геодатафрэйма
        for index, values in cur_gdf.iterrows():

            # создали геометрию из WKT координат
            geom_from_wkt = ogr.CreateGeometryFromWkt(values.geometry)

            # парсим по кол-ву вложенной геометрии (если одиночный полигон, и у него нет отверстий !!!!

            if geom_from_wkt.GetGeometryCount() == 1 and geom_from_wkt.Boundary().GetGeometryCount() == 1:
                # обработка полигона, создаёт простой mesh по объекту созданному ogr (простой полигон без отверстий)

                msh = My_class.create_mesh_from_polygon_wkt(geom_from_wkt, name_t_from_con)
                # сохраняем mesh
                file_mesh = msh                                                 # mesh который сохраняем
                path = r"./Stl"                                                 # путь куда сохраняем
                name_file = name_t_from_con + '_fid_' + str(index) + '.stl'     # имя файла с расширением
                My_class.save_mesh_as_stl_to_folder(file_mesh, path, name_file)
                print(f"{index} объект сохранен")

            elif geom_from_wkt.GetGeometryCount() == 1 and geom_from_wkt.Boundary().GetGeometryCount() > 1:
                # обработка полигона с отверстиями

                #   !!! ------------------------------------------------------------------------------------------

                # list_boundary = [x.GetPoints() for x in geom_from_wkt.Boundary()]
                # list_boundary = [(ogr.ForceToPolygon(x)).ExportToWkt() for x in geom_from_wkt.Boundary()]
                pts = [y for x in geom_from_wkt.Boundary() for y in x.GetPoints()]
                pts_set = set(pts)
                pts_np = np.array(pts)
                pts_set_np = np.array(list(zip(*pts_set))).T
                pts_np_z_zero = np.pad(pts_np[:], [(0, 0), (0, 1)])
                pts_set_np_zero = np.pad(pts_set_np[:], [(0, 0), (0, 1)])

                obj_tri = pv.PolyData(pts_np_z_zero)
                obj_tri_set = pv.PolyData(pts_set_np_zero)

                # triangles_pv_set = obj_tri_set.delaunay_2d(bound=True)  # триангулировали
                triangles_pv_set = obj_tri_set.delaunay_2d()  # триангулировали
                triangles_pv_set.is_all_triangles()
                triangles_pv_set.flip_normals()
                # triangles_pv_set.plot_normals(mag=5.0)
                # triangles_pv_set.plot(show_edges=True)

                myPoints = triangles_pv_set.points.tolist()     # точки меша
                myfaces = triangles_pv_set.faces.tolist()       # список индексов точек каждого face
                cnt_fcs = triangles_pv_set.n_faces              # количество faces in mesh
                # получаем faces из pyvista PolyData
                my_list_faces = []
                i = 0
                while i <= len(myfaces)-1:
                    my_list_faces.append(myfaces[i+1: i + myfaces[i]+1])
                    step = myfaces[i] + 1
                    i += step

                myPoints2D = [(a[0], a[1]) for a in myPoints]

                # # формируем словарь структуру полученных данных
                # mesh_dic = {
                #     'gpkg_ind': index,
                #     'gpkg_wkt': list_boundary,
                #     'unic_pts3d': myPoints,
                #     'unic_pts2d': myPoints2D,
                #     'fcs': my_list_faces
                # }
                # мегагенератор индексы полигонов, faces, поинты под каждый фэйс - в одном словаре !!!!
                # pol_pts = {ind:(p, [myPoints2D[m] for m in p], Polygon([myPoints2D[m] for m in p])) for ind, p in enumerate(my_list_faces)}
                # pol_pts = {ind:(p, [myPoints2D[m] for m in p]) for ind, p in enumerate(my_list_faces)}
                pol_pts = {ind:(p, Polygon([myPoints2D[m] for m in p])) for ind, p in enumerate(my_list_faces)}
                zip_obj = zip([val[1][0] for val in pol_pts.items()], [val[1][1] for val in pol_pts.items()])

                # # BPY
                # mesh = bpy.data.meshes.new("myBeautifulMesh")
                # obj = bpy.data.objects.new(mesh.name, mesh)
                # col = bpy.data.collections.get("Collection")
                # col.objects.link(obj)
                # obj = bpy.data.objects.new(mesh.name, mesh)
                # col.objects.link(obj)
                # bpy.context.view_layer.objects.active = obj
                # verts = [( 1.0,  1.0,  0.0), ( 1.0, -1.0,  0.0), (-1.0, -1.0,  0.0), (-1.0,  1.0,  0.0)]
                # edges = []
                # faces = [[0, 1, 2, 3]]
                # mesh.from_pydata(verts, edges, faces)
                # bpy.ops.object.select_all(action='DESELECT')
                # ob = bpy.context.scene.objects["myBeautifulMesh"]  # получаем объект
                # ob.select_set(True)  # выделяем объект
                # bpy.context.view_layer.objects.active = bpy.data.objects["myBeautifulMesh"] # делаем объект активным
                # stl_path = os.path.join(pathlib.Path().resolve(), "from_bpy.stl")
                # obj_path = os.path.join(pathlib.Path().resolve(), "from_bpy.obj")
                # bpy.ops.export_mesh.stl(filepath=stl_path)
                #
                #
                #
                #
                # obj_my = bpy.data.objects["myBeautifulMesh"]
                # bpy.context.scene.objects.active = obj_my
                #
                #
                #
                # ob.select_set(True)  # выделяем объект
                # bpy.context.view_layer.objects.active = bpy.data.objects[objname[0]]  # делаем объект активным
                # bpy.ops.object.modifier_apply(modifier=mod_name)  # применяем модификаторы




                # РЕЖЕМ
                # лист линий для резки
                list_lines_for_cut_WKT = [x.ExportToWkt() for x in geom_from_wkt.Boundary()]
                list_lines_for_cut_She = [wkt.loads(h) for h in list_lines_for_cut_WKT]

                # from shapely to wkt
                list_polygons_for_cut_WKT = [h[1][1].to_wkt() for h in pol_pts.items()]
                # from ogr to shapely
                list_polygons_for_cut_She = [wkt.loads(h) for h in list_polygons_for_cut_WKT]

                # cut_polygon_by_line_shepely
                list_poly_from_cut = [My_class.cut_polygon_by_line_shepely(x, list_lines_for_cut_She[1]) for x in list_polygons_for_cut_She]

                # поднимаем на один уровень вверх все в списке списков
                list_result = [x for y in list_poly_from_cut for x in y]

                # p = gpd.GeoDataFrame(list_result)
                # gpd_gs_set_geom = p.set_geometry(list_result)
                # gpd_gs_set_geom.plot()
                # plt.show()

                # РАБОТАЕТ ВЫРЕЗАНИЕ
                #                 # создали мультиполигон, которым режем
                #                 multipolygon_shp = MultiPolygon([Polygon(x.GetPoints()) for x in geom_from_wkt.Boundary()])
                #                 gpd_cut_polygon = gpd.GeoDataFrame(geometry=[multipolygon_shp])
                #                 gpd_cut_polygon.plot()
                #                 plt.show()

                # датафрэйм создали - БАЗА полигон по внешнему контуру
                outer_boundary_polygon = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()][0])
                gpd_outer_cut_polygon = gpd.GeoDataFrame(geometry=[outer_boundary_polygon])
                # gpd_outer_cut_polygon.plot(cmap='BuPu')
                gpd_outer_cut_polygon.plot()
                plt.show()

                # датафрэйм создали - HOLES полигоны отверстий
                # aaaa = [h.GetPoints() for h in geom_from_wkt.Boundary()][1:]
                # inner_boundary_polygon = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()])
                # inner_boundary_polygon = [Polygon(h.GetPoints()) for h in geom_from_wkt.Boundary()][1:]
                inner_boundary_polygon = MultiPolygon([Polygon(h.GetPoints()) for h in geom_from_wkt.Boundary()][1:])
                gpd_inner_boundary_polygon = gpd.GeoDataFrame(geometry=[inner_boundary_polygon])
                # gpd_inner_boundary_polygon.plot(cmap='OrRd')
                # plt.show()

                # из чего вырезаем
                gpd_polygon_for = gpd.GeoDataFrame(list_polygons_for_cut_She)
                gpd_gs_set_geom = gpd_polygon_for.set_geometry(list_polygons_for_cut_She)
                # gpd_gs_set_geom.plot(cmap='GnBu')
                # plt.show()

                # удаляем из треангулированного фрэйма внешний контур
                overlay_n = gpd.overlay(gpd_gs_set_geom, gpd_outer_cut_polygon, how='intersection', keep_geom_type=False)
                # overlay_n.plot(cmap='Blues')
                # plt.show()

                # выбираем только полигоны из полученных результатов
                new_gdf = overlay_n[overlay_n['geometry'].geometry.type == 'Polygon']
                # new_gdf.plot(cmap='Blues')
                # plt.show()

                # удаляем из треангулированного фрэйма отверстия
                overlay_nn = gpd.overlay(new_gdf, gpd_inner_boundary_polygon, how='symmetric_difference', keep_geom_type=False)
                overlay_nn.plot(facecolor='#C2C2C2', linewidth=0.4, edgecolor='red')
                plt.show()



                print('stope')


                # earcut
                # triangles = ecut_tri([0,0, 100,0, 100,100, 0,100,  20,20, 80,20, 80,80, 20,80], [4])
                # unflatten
                # aaa = geom_from_wkt.ExportToJson()
                # aaj = gjs.loads(aaa)
                # aadict = dict(aaj)
                # data = flt(aadict['coordinates'][0])
                # a_body_vrts = data['vertices']
                # a_hols_vrts = data['holes']
                # a_dimen = data['dimensions']
                # triangles = ecut_tri(a_body_vrts, a_hols_vrts, a_dimen)
                # deviation = deviation(a_body_vrts, a_hols_vrts, a_dimen, triangles)
                #
                # # aaaa_vrts = [tuple(result_vrt[x]) for x in triangles]
                # result_vrt = np.array(data['vertices']).reshape(int(len(data['vertices'])/2), 2)
                # result_fcs = np.array(triangles).reshape(int(len(triangles)/3), 3)
                # result_vrt_3d = np.pad(aaaa_vrts, [(0, 0), (0, 1)])
                # mesh_ear = pv.make_tri_mesh(result_vrt_3d, result_fcs)
                # mesh_ear.plot(show_edges=True)
                #
                # aaaa_vrts = [result_vrt[x] for x in triangles]
                #
                #
                # vrts = data['vertices']
                #
                # aaaa_vrts = [vrts[x] for x in triangles]
                #
                # aaa_verts = np.array(aadict['coordinates'][0][0])
                # aaa_verts_hol = np.array(aadict['coordinates'][0][1])
                # aaa_conc_with_hole = np.concatenate((aaa_verts, aaa_verts_hol), axis=0)
                #
                # aaa_rings = np.array(list((aaa_verts.shape[0], aaa_conc_with_hole.shape[0])))
                # # result = ecut.triangulate_float32(aaa_verts, aaa_rings)
                # # result = ecut.triangulate_float64(aaa_verts, aaa_rings)
                # # result = ecut.triangulate_int32(aaa_verts, aaa_rings)
                # result = ecut.triangulate_int64(aaa_verts, aaa_rings)
                # aaaa_vrts = aaa_verts[result]
                # aaaa_fcs = np.array(result).reshape(int(len(result)/3), 3)
                # aaaa_vrts = np.pad(aaaa_vrts, [(0, 0), (0, 1)])
                # mesh_ear = pv.make_tri_mesh(aaaa_vrts, aaaa_fcs)
                # mesh_ear.plot(show_edges=True)



# РАБОТАЕТ ВЫРЕЗАНИЕ
#                 # создали мультиполигон, которым режем
#                 multipolygon_shp = MultiPolygon([Polygon(x.GetPoints()) for x in geom_from_wkt.Boundary()])
#                 gpd_cut_polygon = gpd.GeoDataFrame(geometry=[multipolygon_shp])
#                 gpd_cut_polygon.plot()
#                 plt.show()

                # # датафрэйм создали - БАЗА полигон по внешнему контуру
                # outer_boundary_polygon = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()][0])
                # gpd_outer_cut_polygon = gpd.GeoDataFrame(geometry=[outer_boundary_polygon])
                # gpd_outer_cut_polygon.plot(cmap='BuPu')
                # plt.show()
                #
                # # датафрэйм создали - HOLES полигоны отверстий
                # # aaaa = [h.GetPoints() for h in geom_from_wkt.Boundary()][1:]
                # # inner_boundary_polygon = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()])
                # # inner_boundary_polygon = [Polygon(h.GetPoints()) for h in geom_from_wkt.Boundary()][1:]
                # inner_boundary_polygon = MultiPolygon([Polygon(h.GetPoints()) for h in geom_from_wkt.Boundary()][1:])
                # gpd_inner_boundary_polygon = gpd.GeoDataFrame(geometry=[inner_boundary_polygon])
                # gpd_inner_boundary_polygon.plot(cmap='OrRd')
                # plt.show()
                #
                # # из чего вырезаем
                # gpd_polygon_for = gpd.GeoDataFrame(list_polygons_for_cut_She)
                # gpd_gs_set_geom = gpd_polygon_for.set_geometry(list_polygons_for_cut_She)
                # gpd_gs_set_geom.plot(cmap='GnBu')
                # plt.show()
                #
                # # удаляем из треангулированного фрэйма внешний контур
                # overlay_n = gpd.overlay(gpd_gs_set_geom, gpd_outer_cut_polygon, how='intersection', keep_geom_type=False)
                # overlay_n.plot(cmap='Blues')
                # plt.show()
                #
                # # выбираем только полигоны из полученных результатов
                # new_gdf = overlay_n[overlay_n['geometry'].geometry.type == 'Polygon']
                # new_gdf.plot(cmap='Blues')
                # plt.show()
                #
                # # удаляем из треангулированного фрэйма отверстия
                # overlay_nn = gpd.overlay(new_gdf, gpd_inner_boundary_polygon, how='symmetric_difference', keep_geom_type=False)
                # overlay_nn.plot(cmap='Blues')
                # plt.show()
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                # multipolygon_shp = Polygon([Polygon(x.GetPoints()) for x in geom_from_wkt.Boundary()])
                # gpd_cut_polygon = gpd.GeoDataFrame(geometry=[multipolygon_shp])
                # gpd_cut_polygon.plot(cmap='Blues')
                # plt.show()
                #
                # # из чего вырезаем
                # gpd_polygon_for = gpd.GeoDataFrame(list_polygons_for_cut_She)
                # gpd_gs_set_geom = gpd_polygon_for.set_geometry(list_polygons_for_cut_She)
                # gpd_gs_set_geom.plot(cmap='Greys')
                # plt.show()
                #
                # overlay_n = gpd.overlay(gpd_gs_set_geom, gpd_cut_polygon, how='difference', keep_geom_type=False)
                # overlay_n.plot()
                # plt.show()
                #
                #
                # overlay_n = gpd.overlay(gpd_gs_set_geom, gpd_cut_polygon, how='symmetric_difference', keep_geom_type=False)
                # overlay_n.plot()
                # plt.show()
                #
                # polygon1_shp = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()][1])
                # gpd_cut_polygon = gpd.GeoDataFrame(geometry=[polygon1_shp])
                # gpd_cut_polygon.plot()
                # plt.show()
                #
                # gpd_polygon_for = gpd.GeoDataFrame(list_polygons_for_cut_She)
                # gpd_gs_set_geom = gpd_polygon_for.set_geometry(list_polygons_for_cut_She)
                # gpd_gs_set_geom.plot()
                # plt.show()
                #
                # overlay = gpd.overlay(gpd_gs_set_geom, gpd_cut_polygon, how='difference')
                # overlay.plot()
                # plt.show()
                #
                #
                # polygon2_shp = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()][0])
                # gpd_cut_polygon2 = gpd.GeoDataFrame(geometry=[polygon2_shp])
                # gpd_cut_polygon2.plot()
                # plt.show()
                #
                # overlay_n = gpd.overlay(gpd_cut_polygon2, overlay, how='difference', keep_geom_type=False)
                # overlay_n = gpd.overlay(gpd_cut_polygon2, overlay, how='symmetric_difference', keep_geom_type=False)
                # overlay_n = gpd.overlay(overlay, gpd_cut_polygon2, how='intersection', keep_geom_type=False)
                # overlay_n = gpd.overlay(overlay, gpd_cut_polygon2, how='identity', keep_geom_type=False)
                # overlay_n = gpd.overlay(overlay, gpd_cut_polygon2, how='union', keep_geom_type=False)
                # overlay_n.plot()
                # plt.show()
                #
                # multipolygon_shp = MultiPolygon([Polygon(x.GetPoints()) for x in geom_from_wkt.Boundary()])
                # gpd_cut_polygon = gpd.GeoDataFrame(geometry=[multipolygon_shp])
                # gpd_cut_polygon.plot()
                # plt.show()
                #
                #
                #
                # polygon1_shp = Polygon([x.GetPoints() for x in geom_from_wkt.Boundary()][1])
                # gpd_cut_polygon = gpd.GeoDataFrame(geometry=[polygon1_shp])
                # gpd_cut_polygon.plot()
                # plt.show()
                # overlay_n = gpd.overlay(gpd_cut_polygon2, overlay, how='symmetric_difference', keep_geom_type=False)
                #
                #
                #
                #
                # def pplot(shapely_objects, figure_path='fig.png'):
                #     from matplotlib import pyplot as plt
                #     import geopandas as gpd
                #     boundary = gpd.GeoSeries(shapely_objects)
                #     boundary.plot(color=['red', 'green', 'blue', 'yellow', 'yellow'])
                #     plt.savefig(figure_path)
                #
                # [pplot(x) for x in list_poly_from_cut]
                # plt.show()
                #
                #
                #
                # list_united_val = []
                # for i in zip_obj:
                #     if (ogr.CreateGeometryFromWkt(i[1].to_wkt())).Within(geom_from_wkt) is True:
                #         list_united_val.append(i)
                #
                # list_polygons = [ogr.CreateGeometryFromWkt(h[1].to_wkt()) for h in list_united_val]
                #
                #
                # list_polygons_shapely = [h[1] for h in list_united_val]
                # p = gpd.GeoDataFrame(list_polygons_shapely)
                # gpd_gs_set_geom = p.set_geometry(list_polygons_shapely)
                # gpd_gs_set_geom.plot()
                # plt.show()
                # print('stop')


                # ogrLineRing = ogr.Geometry(ogr.wkbLinearRing)
                # ogrLineString = ogr.Geometry(ogr.wkbLineString)
                # ogrMultiLineString = ogr.Geometry(ogr.wkbMultiLineString)

                # ogrMultipolygon = ogr.Geometry(ogr.wkbMultiPolygon)
                # ogrCollection = ogr.Geometry(ogr.wkbGeometryCollection)
                # ogrPolygon = ogr.Geometry(ogr.wkbPolygon)
                #
                # [ogrPolygon.AddGeometry(x) for x in list_polygons]
                # [ogrCollection.AddGeometry(x) for x in list_polygons]
                # [ogrMultipolygon.AddGeometry(x) for x in list_polygons]
                #
                # ogrCollection.IsValid()
                # ogrMultipolygon.IsValid()
                #
                # gs = gpd.GeoSeries(ogrCollection)
                # gpd_gs = gpd.GeoDataFrame(gs, crs="EPSG:4326")
                # gpd_gs = gpd.GeoDataFrame(gs, crs="EPSG:4326")
                # gpd_gs_set_geom = gpd_gs.set_geometry(gs)
                # [h[1].to_wkt() for h in list_united_val]
                #
                # circle = pv.PolyData((zip(pts[:0], pts[:1], 0)))
                # x, y = list(zip(*pts))
                # multip = shapely.geometry.MultiPoint(pts)
                # triangles = shapely.ops.triangulate(multip)  # триангулировали MultiPoints
                # p = gpd.GeoDataFrame(triangles)
                # gdf_trian = p.set_geometry(triangles)  # устанавливем геомтрию
                # gdf_trian.plot()
                # plt.show()
                # list_boundary = [x.ExportToWkt() for x in geom_from_wkt.Boundary()]
                # geom_lb = ogr.CreateGeometryFromWkt(list_boundary[0])
                # geom_lb = ogr.ForceToPolygon(geom_lb)
                #
                #
                #
                # geom_mult = ogr.ForceToMultiPolygon(geom_from_wkt)
                # str_geom_mult = geom_mult.GetBoundary().ExportToWkt()
                # shap_geom_mult = shapely.geometry.MultiPolygon(str_geom_mult)
                #
                #
                # [[myPoints2D[m] for m in p] for p in my_list_faces]
                # i_p = {k: Polygon(v) for k, v in myPoints2D.items()}
                # i_p = {k: Polygon(v) for k, v in interiors.items()}
                #
                # zone = Polygon(p, [zone.exterior.coords for zone in i_p.values() if zone.within(Polygon(p)) is True])
                #
                #
                # # plot = WKTPlot(title="California", save_dir=r"C:\!_Python\_899_Blener_port\portable_work_\Stl")
                # # vvv = ogr.CreateGeometryFromWkt(list_boundary[0])
                # # vvv = ogr.ForceToPolygon(vvv)
                # # plot.add_shape(shapely.geometry.Polygon(vvv.Boundary().GetPoints()), color="green", line_width=3)
                # # plot.show()
                # # mult = geom_from_wkt.Boundary().ExportToWkt()
                # # shply_mult = shapely.geometry.MultiPolygon()
                #
                #
                # v = np.array(myPoints2D)
                # t = triangulate({'vertices': v})
                #
                # A = dict(vertices=np.array(myPoints2D))
                # # B = tr.triangulate(A, 'p')
                # B = tr.triangulate(A)
                # tr.compare(plt, A, B)
                # plt.show()
                #
                # # получаем центроид из строки WKT координат строки
                # cntr = ogr.ForceToPolygon(ogr.CreateGeometryFromWkt(mesh_dic['gpkg_wkt'][1])).Centroid().GetPoints()
                # tri = tr.delaunay(myPoints2D)
                # seg = tri.tolist()
                # # A = dict(vertices=np.array(myPoints2D), segments=seg, holes=np.array(cntr))
                # A = dict(vertices=np.array(myPoints2D))
                # # B = tr.triangulate(A, 'p')
                # B = tr.triangulate(A, 'q')
                #
                #
                #
                # def circle(N, R):
                #     i = np.arange(N)
                #     theta = i * 2 * np.pi / N
                #     pts = np.stack([np.cos(theta), np.sin(theta)], axis=1) * R
                #     seg = np.stack([i, i + 1], axis=1) % N
                #     return pts, seg
                #
                # pts0, seg0 = circle(30, 1.4)
                # pts1, seg1 = circle(16, 0.6)
                # pts = np.vstack([pts0, pts1])
                # seg = np.vstack([seg0, seg1 + seg0.shape[0]])
                # print(pts)
                # print(seg)
                # A = dict(vertices=pts, segments=seg, holes=[[0, 0]])
                # print(seg)
                # B = tr.triangulate(A)  # note that the origin uses 'qpa0.05' here
                # tr.compare(plt, A, B)
                # plt.show()
                #
                #
                # # Polygon exterior:
                # p = [[20, 767], [54, 744], [107, 707],
                #      [190, 654], [265, 609], [363, 548],
                #      [462, 484], [514, 447], [603, 389],
                #      [682, 337], [726, 310], [757, 290],
                #      [786, 277], [820, 259], [843, 249],
                #      [881, 231], [921, 215], [975, 197],
                #      [1048, 174], [1089, 163], [1141, 152],
                #      [1212, 137], [1270, 121], [1271, 64],
                #      [1207, 78], [1163, 89], [1096, 103],
                #      [1048, 115], [1001, 129], [949, 144],
                #      [905, 157], [874, 170], [830, 187],
                #      [781, 208], [730, 236], [696, 255],
                #      [652, 282], [606, 306], [561, 340],
                #      [512, 370], [478, 393], [436, 418],
                #      [385, 453], [330, 490], [285, 521],
                #      [229, 566], [183, 603], [123, 652],
                #      [70, 698], [13, 749]]
                #
                # # Define interior "holes":
                # interiors = {}
                # interiors[0] = [[290, 543], [301, 560], [393, 501], [377, 482]]
                # interiors[1] = [[507, 392], [549, 363], [553, 367], [572, 352], [588, 372], [522, 415]]
                # interiors[2] = [[599, 340], [636, 316], [648, 334], [612, 357]]
                # interiors[3] = [[714, 262], [727, 284], [821, 238], [811, 215]]
                # interiors[4] = [[850, 218], [935, 185], [937, 187], [850, 221]]
                # interiors[5] = [[959, 159], [1066, 129], [1071, 146], [966, 177]]
                # interiors[6] = [[1119, 133], [1175, 122], [1178, 123], [1119, 134]]
                # interiors[7] = [[1211, 102], [1266, 91], [1267, 97], [1212, 108], [1211, 102]]
                #
                # i_p = {k: Polygon(v) for k, v in interiors.items()}
                #
                # zone = Polygon(p, [zone.exterior.coords for zone in i_p.values() if zone.within(Polygon(p)) is True])
                # fig, ax = plt.subplots()
                # patch = PolygonPatch(zone.buffer(0))
                # ax.add_patch(patch)
                # ax.set_xlim(0, 1300)
                # ax.set_ylim(0, 777)
                # plt.show()
                #
                #
                #
                # poly_mesh = om.PolyMesh()
                # poly_mesh.add_vertices(np.array(myPoints))
                # poly_mesh.add_faces(np.array(my_list_faces))
                #
                # vertex_handle = []
                # for v in np.array(myPoints):
                #     vertex_handle.append(poly_mesh.add_vertex(v))
                # face_handle = poly_mesh.add_face(vertex_handle)
                # poly_mesh.triangulate()
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                #
                # poly_mesh = om.PolyMesh()
                # coords_array = \
                #     [
                #         np.array([-5.0, -5.0, 0.0]),
                #         np.array([5.0, -5.0, 0.0]),
                #         np.array([5.0, 10.0, 0.0]),
                #         np.array([0.0, 10.0, 0.0]),
                #         np.array([0.0, 5.0, 0.0]),
                #         np.array([-5.0, 5.0, 0.0])
                #     ]
                # vertex_handle = []
                # for v in coords_array:
                #     vertex_handle.append(poly_mesh.add_vertex(v))
                #
                # face_handle = poly_mesh.add_face(vertex_handle)
                # poly_mesh.triangulate()
                #
                # om.write_mesh("test_polymesh.stl", poly_mesh)
                #
                #
                #
                # mesh = trimesh.Trimesh(vertices=myPoints, faces=my_list_faces)
                # mesh.export('aaasf.obj', file_type="obj")
                # mesh.show()
                #
                #
                #
                #
                #
                #
                # # base_pts = list_boundary[0]
                # # geom_from_wkt = ogr.CreateGeometryFromWkt(base_pts)
                # # mesh_base = My_class.create_mesh_from_polygon_wkt(geom_from_wkt, name_t_from_con)
                # # mshbs = mesh_base.clean()
                # # for x in list_boundary[1:]:
                # #     geom_from_wkt = ogr.CreateGeometryFromWkt(x)
                # #     mesh_del = My_class.create_mesh_from_polygon_wkt(geom_from_wkt, name_t_from_con)
                # #     mshdl = mesh_del.clean()
                # # result = My_class.boolean_mesh_different(mshbs, mshdl)
                #
                #
                # circle = pv.PolyData((zip(pts[:0], pts[:1], 0)))
                # x, y = list(zip(*pts))
                # multip = shapely.geometry.MultiPoint(pts)
                # triangles = shapely.ops.triangulate(multip)  # триангулировали MultiPoints
                # p = gpd.GeoDataFrame(triangles)
                # gdf_trian = p.set_geometry(triangles)  # устанавливем геомтрию
                # gdf_trian.plot()
                # plt.show()
                # list_boundary = [x.ExportToWkt() for x in geom_from_wkt.Boundary()]
                # geom_lb = ogr.CreateGeometryFromWkt(list_boundary[0])
                # geom_lb = ogr.ForceToPolygon(geom_lb)
                #
                # trian = [x for x in triangles if x.within(geom_lb)]
                #
                # geom_polygon = ogr.ForceToPolygon(geom_from_wkt)  # переводим в полигон
                #
                # # триангулируем и берем полигоны только внутри исходного
                # trian = [triangle for triangle in triangulate(geom_polygon) if triangle.within(geom_polygon)]
                # # переносим треангулированные объекты в геодатафрэйм + назначаем поле геометрии
                # gdf_trian = gpd.GeoDataFrame(trian)
                # gdf_trian = gdf_trian.set_geometry(trian)  # устанавливем геомтрию
                # gdf_trian.rename(columns={0: 'xy'}, inplace=True)
                # gdf_trian['xy'] = [x.exterior.xy for x in gdf_trian['geometry']]
                # # gdf_trian[0] = ''
                # # it_obj = geom.Boundary().GetPoints()
                # # x, y = zip(*it_obj)
                # # # визуализируем геодатафрэйм
                # # gdf_trian.plot()
                # # plt.show()
                # # визуализируем matplotlib по x и y координатам
                # # plt.plot(x, y)
                # # plt.show()
                #
                #
                # # получили все точки полигона с отверстиями
                # pts = [y for x in geom_from_wkt.Boundary() for y in x.GetPoints()]
                #
                #
                # # # получили точки верхнего полигона
                # # base_pts = list_boundary[0]
                # # # создали геометрию из WKT координат
                # # geom_from_wkt = ogr.CreateGeometryFromWkt(base_pts)
                # # mesh_base = My_class.create_mesh_from_polygon_wkt(geom_from_wkt, name_t_from_con)
                # # for x in list_boundary[1:]:
                # #     geom_from_wkt = ogr.CreateGeometryFromWkt(x)
                # #     mesh_del = My_class.create_mesh_from_polygon_wkt(geom_from_wkt, name_t_from_con)
                # #
                # #
                # #     result = My_class.boolean_mesh_different(mesh_base, mesh_del)
                # #
                # # import pymeshfix
                # # from pymeshfix._meshfix import PyTMesh
                # #
                # #
                # # plotter = pv.Plotter()
                # # dargs = dict(show_edges=True)
                # # plotter.add_mesh(mesh_base, **dargs)
                # # plotter.add_mesh(mesh_del, **dargs)
                # # plotter.show()

#   !!! ------------------------------------------------------------------------------------------

            elif geom_from_wkt.GetGeometryCount() > 1:
                # обработка составных объектов с отверстиями
                lst_not_worked_obj[index] = (name_t_from_con, 'collection')


            else:
                pass

        return


# Главная функция
def mainFunction(path_gpkg, gr_obrezki):
    ds = My_class.open_file_by_gdal(path_gpkg)  # получаем в переменнюу GPKG

    # получаем в переменные выборки build, land, и сущ застройку с сущ дорогами
    build, land, s_build, s_road = My_class.filter_by_coordinate(gr_obrezki, ds)

    # datasourc GDAL с слоями build and lands
    tmp_ds = My_class.save_to_mem(build, land)  # сохраняем результаты в оперативку

    # datasourc GDAL с слоями существующие build и сущ road
    tmp_ds_s = My_class.save_to_mem(s_build, s_road)  # сохраняем результаты в оперативку

    # получаем словари со слоями в формате dataframe по каждому слою и инфой по полям слоя
    # т.е. перегоняем gdal -> dataframe
    data_set_first = My_class.open_by_gdal_ogr(tmp_ds)
    data_set_second = My_class.open_by_gdal_ogr(tmp_ds_s)


    # получаем объект GEODATAFRAME из DATAFRAME
    gdf_first_build_pr = gpd.GeoDataFrame(data_set_first['Build_Polygon']['FEATURE'])
    gdf_second_lands_pr = gpd.GeoDataFrame(data_set_first['Lands_Polygon']['FEATURE'])
    gdf_third_build_s = gpd.GeoDataFrame(data_set_second['Build_Polygon']['FEATURE'])
    gdf_fourth_road_s = gpd.GeoDataFrame(data_set_second['Lands_Polygon']['FEATURE'])

    # делим датафрэйм на словарь датафрэймов по уникальным значениям колонки
    dic_gdf_buil_pr = My_class.split_gdf_by_unic_val_colum('t_from_contents', gdf_first_build_pr)
    dic_gdf_land_pr = My_class.split_gdf_by_unic_val_colum('t_from_contents', gdf_second_lands_pr)




    # очищаем целевой каталог
    # pth = pathlib.Path().resolve()                          # путь к файлу где скрипт запустили
    # pth_dir = pathlib.Path(__file__).parent.resolve()       # путь к файлу где скрипт запустили
    # f_name, f_ext = os.path.splitext(os.path.basename())
    name_gpkg_with_ext = os.path.basename(path_to_GPKG)     # имя gpkg с расширением
    # path_to_dir = os.path.dirname(path_to_GPKG)             # путь к раб каталогу
    pth_dir = pathlib.Path(__file__).resolve()             # путь к файлу где скрипт запустили

    # создаем (подготавливаем) каталог для файлов
    result_path = (My_class.createNewFolder(pth_dir, r'\Stl')).replace('\\', '//')
    My_class.clear_AllIn_Folder(result_path)            # очистили каталог

    # ведем словарь не обработанных объектов
    lst_not_worked_obj = {}

    # получаем словарь для экспорта объектов в stl на основании датафрэйма
    dic_for_export_to_stl = {}
    for x in list(dic_gdf_buil_pr.keys()):
        dic_for_export_to_stl[x] = My_class.parse_by_wkt(x, dic_gdf_buil_pr[x], lst_not_worked_obj)

    dic_for_export_to_stl = {}
    for x in list(dic_gdf_land_pr.keys()):
        dic_for_export_to_stl[x] = My_class.parse_by_wkt(x, dic_gdf_land_pr[x], lst_not_worked_obj)

    pass



# ---- / ---- / ---- / ---- / MAIN / ---- / ---- / ---- / ---- / ---- / ---- / ---- /

# граница обрезки
name_granica_obrezki = '102'  # берем граничку для обрезки

# путь к GPKG
path_to_GPKG = ((r'C:\!_Python\_899_Blener_port\!!!_3d_portative_work\URBANPLANNING.gpkg').replace('"', ''))


mainFunction(path_to_GPKG, name_granica_obrezki)


# ---- / ---- / ---- / ---- / MAIN / ---- / ---- / ---- / ---- / ---- / ---- / ---- /