"""# -*- coding: utf-8 -*-"""
import pyvista as pv
import os
from pyvista.core.pointset import PolyData as pvPolyData
import osgeo
from osgeo import ogr
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import triangulate as shp_tri
import geopandas as gpd

def tri_from_2d_point(pts: np.ndarray) -> gpd.GeoDataFrame:
    '''
    получаем геодатафрэйм из триангулированных полигонов отфильтрованных по граничке
    !!! если последовательнос соединить точки pts - будет граница полигона
    pts     -  точки numpy массив последовательных точек (граница полигона)
    '''
    poly_from_wkt = Polygon(pts)  # создаем shapely полигон

    # # можно посмотреть созданный полигон
    # x, y = poly_from_wkt.exterior.xy
    # plt.plot(x, y)
    # plt.show()

    # триангулируем и берем полигоны только внутри исходного
    trian = [triangle for triangle in shp_tri(poly_from_wkt) if triangle.within(poly_from_wkt)]
    # переносим треангулированные объекты в геодатафрэйм + назначаем поле геометрии
    gdf_trian = gpd.GeoDataFrame(trian)   # trian - это лист shapely полигонов !!!
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

def create_mesh_by_extrude_list_pts(var: list, h_extrude: float) -> pvPolyData:
    """
    функция возвращае mesh по точкам и значению extrude, Т.е. функция выдавливает точки линии на высоту
    var        -   последовательный список картежей точек линии (внешняя граница к примеру)
    h_extrude  -   высота на которую нужно экструдить данную линию
    """
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

def create_top_button_meshes_by_pts_fcs(pts: list, fcs: list, h_obj: float) -> [pvPolyData, pvPolyData]:
    ''' получаем два mesha по точкам, граням, высоте объекта + добавляем z = 0
    pts     -  лист картежей x, y пример - [(16339.56001, 14490.695), (16315.11, 14490.695), ....
    fcs     -  лист листов int значений номеров faces, пример - [[1, 2, 3], [1, 3, 0]]...
    h_obj   -  высота на которую выдавливать объект
    '''
    points_3d_z_zero = np.pad(pts[:-1], [(0, 0), (0, 1)])   # добавляем нулевую колонку z
    points_3d_z_hm = points_3d_z_zero.copy()                # копирум обязательно
    points_3d_z_hm[:, 2] = h_obj                            # в копию создаем второй массив точек с z = h_obj

    # создаем tri-mesh стандартными средствами pyvista
    but = pv.make_tri_mesh(points_3d_z_zero, np.array(fcs))
    top = pv.make_tri_mesh(points_3d_z_hm, np.array(fcs))
    # but.plot(show_edges=True)
    # top.plot(show_edges=True)

    return but, top

def merge_meshes_by_list_meshes(list_meshes: list) -> pvPolyData:
    """    объединяем каждый mesh из списка через merge
    list_meshes  -  лист из мешей pyvista, pv.core.pointset.PolyData
    """
    mesh_un = pv.PolyData()
    obj = mesh_un.merge(list_meshes)
    full_geom = obj.extract_geometry()
    return full_geom

def save_mesh_as_stl_to_folder(file_mesh: pvPolyData, path: str, name_file: str) -> None:
    '''      сохраняет mesh как stl file в папку
    file_mesh       -  сохраняемый меш
    path            -  путь к папке в которую сохраняем
    name_file       -  имя файла для сохранения
    '''
    file_mesh.save(f'{path}/{name_file}', binary=False)

def get_vrts_from_gdf(gdf_tri_polygons: gpd.GeoDataFrame) -> list:
    """     получаем вертексы треангулированного полигона
    gdf_tri_polygons    -  geopandas с полигонами из которых нужно извлеч vrts
    """
    vrts = []
    for ii in range(len(gdf_tri_polygons['geometry'])):
        # fnd_pts.append(list(zip(*tri['geometry'][ii].exterior.xy)))
        vrts.append(list(zip(*gdf_tri_polygons['geometry'][ii].exterior.xy))[:-1])
    return vrts

def get_fcs_from_pts(vrts_boundary_line: list, vrts_after_tri: list) -> list:
    """     получаем лист индексов faces (сравниваем полученные координаты точек каждого треугольника после
            треангуляции всего полигона, с координатами исходных точек гранички всего многоугольного полигана)
    vrts_boundary_line      -  лист картежей с координатами точек границ многоугольного полигона (исходный объект)
    vrts_after_tri          -  полученные точки из полигонов после треангуляции объекта (каждого треугольника отдельно)
    """
    fcs = []
    for ii in range(len(vrts_after_tri)):
        fcs.append([vrts_boundary_line.index(x) for x in vrts_after_tri[ii]])
    return fcs

def create_mesh_from_polygon_wkt(obj_from_wkt_ogr: osgeo.ogr.Geometry, name_t_from_con: str = "") -> pvPolyData:
    """     создаем mesh из простого полигона
    obj_from_wkt_ogr        -  геометрия ogr (Polygon, MultiPolygon)
    name_t_from_con         -  полученное значение из колонки "t_from_contents", пример - NZH_6_18
    """
    geom_polygon = ogr.ForceToPolygon(obj_from_wkt_ogr)     # переводим в полигон
    it_obj = geom_polygon.Boundary().GetPoints()            # получаем картежи точек
    tri = tri_from_2d_point(np.array(it_obj))               # триангулируем точки одиночного полигона

    # получаем вертексы треангулированного полигона из geodataframe
    vrts = get_vrts_from_gdf(tri)

    # получаем список faces текущего объекта по индексам списка точек границы объекта и треангулированного полигона
    fcs = get_fcs_from_pts(it_obj, vrts)

    # получаем экструдированный mesh по точкам полигона
    h_obj = float(name_t_from_con.split('_')[2])  # высота экструдии
    mesh_extr = create_mesh_by_extrude_list_pts(it_obj, h_obj)

    # получаем крышку и дно в виде мешей
    but_mesh, top_mesh = create_top_button_meshes_by_pts_fcs(it_obj, fcs, h_obj)

    # объединяем meshes
    full_mesh = merge_meshes_by_list_meshes([mesh_extr, but_mesh, top_mesh])

    return full_mesh

def pyvista_load_obj_file(path_to_file: str) -> pvPolyData:
    """     загрузка файла obj при помощи pyvista
    path_to_file        -  путь к файлу
    """
    mesh = pv.read(path_to_file)
    # mesh.plot(show_edges=True)
    return mesh

def delit_mesh_from_mesh_boolean_different(base_mesh: pvPolyData, hole_mesh: pvPolyData) -> pvPolyData:
    """     возвращает результат удаления из базового меша меша отверстия
    base_mesh       -  базовый мешь, объект pyvista
    hole_mesh       -  мешь отверстия, удаляемые объект pyvista
    """
    result = base_mesh.boolean_difference(hole_mesh)
    return result