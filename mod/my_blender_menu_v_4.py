import time
import os
import tempfile
import pathlib
import textwrap
import shutil

import math
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame

import osgeo
from osgeo import ogr
from osgeo.ogr import DataSource

from shapely import wkt

import bpy
from bpy import context
from bpy.types import Object as bpyObject
from bpy.types import Mesh as bpyMesh
from bpy.types import Operator, Menu, PropertyGroup, Panel
from bpy.utils import register_class, unregister_class
from bpy.props import StringProperty, PointerProperty, EnumProperty

# ------------------------------------------------------------------------
#    Scene Properties
# ------------------------------------------------------------------------
class MyProperties(PropertyGroup):
    # для всплывающих подсказок
    str_1 = "введите название гранички обрезки"
    str_2 = "вставьте путь к каталогу где расположен GPKG"
    str_3 = "вставьте путь к каталогу где расположены FGM"
    str_4 = "вставьте путь где распологать временные файлы"
    str_ = "выберите объект по центру сцены и нажмите кнопку, камеры центрируются по выборке"
    # свойство строки для выбора границы из слоя
    my_string: StringProperty(
        name="Название гранички",
        description=str_1.upper(),
        default="граничка название",
        maxlen=512,
    )

    # свойство строки для выбора пути к объекту
    my_path: StringProperty(
        name="Путь к GPKG",
        description=str_2.upper(),
        default="путь к GPKG",
        maxlen=1024,
        subtype='FILE_PATH'  # раскоментируй если нужен значёк
    )
    # свойство строки для выбора пути к ФГМ
    fgm_path: StringProperty(
        name="Путь к FGM",
        description=str_3.upper(),
        default="путь к ФГМ",
        maxlen=1024,
        subtype='DIR_PATH'  # раскоментируй если нужен значёк
    )
    # свойство строки для выбора пути к ТЕКСТУРАМ
    texture_path: StringProperty(
        name="Texture",
        description="Вставьте путь к текстурам!",
        default="путь к Текстурам",
        maxlen=1024,
        # subtype='DIR_PATH'  # раскоментируй если нужен значёк
    )
    # ------------------------------------------  NEW  ------------------------------------------
    # выбор слоёв для импорта из QGIS
    my_enum: EnumProperty(
        name="",
        description="выбор слоёв для импорта из QGIS",
        items=[('OP1', "1-2 Project (Build_PR, Land_PR)", ""),
               ('OP2', "3-4 Susch   (Build_S, Road_S)", ""),
               ('OP3', "5-6 TR, LD", ""),
               ('OP4', "Build_PR", ""),
               ('OP5', "Land_PR", ""),
               ('OP6', "Build_S", ""),
               ('OP7', "Road_S", ""),
               ('OP8', "TR", ""),
               ('OP9', "LD", ""),
               ]
    )
    # свойство строки для выбора границы из слоя - дополнительный импорт
    my_string_add: StringProperty(
        name="Название гранички",
        description=str_1.upper(),
        default="граничка название",
        maxlen=512,
    )
    # свойство строки для выбора границы из слоя - дополнительный импорт
    my_string_tmp: StringProperty(
        name="Временный каталог",
        description=str_4.upper(),
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )


# ------------------------------------------------------------------------
#    Panels
# ------------------------------------------------------------------------
class Main_panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "__MRGP__"
    bl_options = {"DEFAULT_CLOSED"}


class Panel_one(Main_panel, Panel):
    bl_idname = "MY_PT_pan_one"
    bl_label = "MAIN"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool

        layout.scale_y = 1.1
        layout.prop(mytool, "my_path")
        layout.prop(mytool, "fgm_path")
        layout.prop(mytool, "my_string_tmp")
        layout.prop(mytool, "my_string")
        # layout.separator(factor=0.2)
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('test.test_op', text='LUCKY!').action = 'LUCK'
        # row.operator('test.test_op', text='ASSIGN_MATERIALS').action = 'MAT_ASSING'
        row.operator('test.test_op', text='CAMERA_SUN').action = 'CAM_SUN'
        row.operator('test.test_op', text='CLEAR_SCENE').action = 'CLEAR'
        # layout.separator(factor=1)
        # row = layout.row(align=True)
        # row.operator('test.test_op', text='IMPORT').action = 'RUN'
        #separ = " * * * * * * * * * * * * * * * * * * * * * * * * * * "
        # layout.operator('test.test_op', text='LUCKY!').action = 'LUCK'
        # layout.operator('test.test_op', text='IMPORT').action = 'RUN'
        # layout.operator('test.test_op', text='inf scene').action = 'INF'
        # layout.label(text=separ)


class Panel_two(Main_panel, Panel):
    bl_idname = "MY_PT_pan_two"
    bl_label = "Работа с выборками"

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.1
        scene = context.scene
        mytool = scene.my_tool
        layout.prop(mytool, "my_enum", text="")
        layout.prop(mytool, "my_string_add")
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('test.test_op', text='IMPORT').action = 'RUN'
        row.operator('test.test_op', text='Assign_MAT').action = 'MAT_ASSING'
        row.operator('test.test_op', text='Delite_MAT').action = 'DEL_MAT'


class Panel_three(Main_panel, Panel):
    bl_parent_id = "MY_PT_pan_two"
    bl_label = "GPKG LAYER"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Second Sub Panel of Panel 1.")


class Panel_four(Main_panel, Panel):
    bl_parent_id = "MY_PT_pan_two"
    bl_label = "Delite"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Second Sub Panel of Panel 1.")

# ------------------------------------------------------------------------
#    SHAPELY, GEOPANDAS, GDAL
# ------------------------------------------------------------------------
class My_class(Operator):
    bl_label = 'GIS_Function'
    bl_idname = 'gis.gis_op'

    @staticmethod
    def open_file_by_gdal(path_to_file):
        """открываем file GDAL - ом по пути """
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
            My_func.ShowMessageBox(u'Неверное название границы обрезки')
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

    @staticmethod
    def save_Dict_With_Ds_To_Mem(dict_ds: dict) -> osgeo.ogr.DataSource:
        """ сливаем в память в один DataSource словарь с DataSources
        dict_ds             -  dict - словарь с DataSources
        """
        if len(dict_ds.keys()) == 0:
            print(f"Нет данных в данном словаре")
            My_func.ShowMessageBox(u'Нет данных в данном словаре :err func "save_Dict_With_Ds_To_Mem"')
            return None

        driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
        ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
        driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

        # скопировали слои в память и разрешили перезаписать если потребутеся
        for key, val in dict_ds.items():
            ds_mem.CopyLayer(val, val.GetName(), ['OVERWRITE=YES'])
        return ds_mem

    @staticmethod
    def lr_to_dataframe(lr: osgeo.ogr.Layer) -> pd.core.frame.DataFrame:
        '''
        перегоняем слой в pandas dataframes с инфой по семантике
        '''
        if isinstance(lr, osgeo.ogr.Layer) != True:
            print(f" ERROR - !!!!Полученные данные не являются слоем gdal.ogr")
            My_func.ShowMessageBox(u' ERROR - !!!!Полученные данные не являются слоем gdal.ogr')
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
    def save_lr_to_mem(lr: osgeo.ogr.Layer = "", name_layer: str = "") -> osgeo.ogr.DataSource:
        """ перегоняем слой в память
        lr                  -  слой ogr
        name_layer          -  имя создаваемого слоя в памяти
        """
        if name_layer == "":
            print(f"Укажите название слоя для сохранения, текущее значение не указано!")
            My_func.ShowMessageBox(u'Укажите название слоя для сохранения, текущее значение не указано!')
            return None

        driver_mem = ogr.GetDriverByName('MEMORY')  # создали драйвер Memory (копия объекта ogr driver memory)
        ds_mem = driver_mem.CreateDataSource('memData')  # создали сурс драйвером
        driver_mem.Open('memData', 1)  # открыли на редактирование созданный сурс

        # скопировали слои в память и разрешили перезаписать если потребутеся
        ds_mem.CopyLayer(lr, name_layer, ['OVERWRITE=YES'])
        return ds_mem

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

    @staticmethod
    def export_gdf_to_svg(gdf_src: GeoDataFrame, name_t_from_con: str, path_rslt: str, filter_par: str = ""):
        """export каждого объекта из gdf в отдельный файл stl
        gdf_src                 -   источник объектов, GeoDataFrame
        name_t_from_con         -   колонка "t_from_contents"
        fltr_clmn               -   значение колонки "t_from_contents" для данного объекта
        path_rslt               -   куда сохраняем результаты (сам stl file)
        """
        geom_clmn = gdf_src._geometry_column_name  # получаем название колонки геометрии
        cur_gdf = gdf_src.loc[:, (name_t_from_con, geom_clmn)]  # срез по геодатафрэйму только нужных столбиков
        cur_gdf['index'] = cur_gdf.index  # присваиваем значения индексов новой колонке
        cur_gdf = cur_gdf.loc[:, ('index', name_t_from_con, geom_clmn)]  # упорядочили колонки по списку

        # цикл по каждой строке геодатафрэйма
        for index, val in cur_gdf.iterrows():

            # # создали геометрию из WKT координат
            # geom_from_wkt = ogr.CreateGeometryFromWkt(val[geom_clmn])

            # экспорт в svg
            fltr_clmn = val[name_t_from_con]
            if filter_par == "":
                name_for_file_svg = f'{fltr_clmn}_fid_{index}.svg'
            else:
                name_for_file_svg = f'{filter_par}_fid_{index}.svg'
            My_class.export_wkt_to_svg(val[geom_clmn], path_rslt, name_for_file_svg)

    @staticmethod
    def getPathAndNamesFilesInFolderByExtension(path_to_target_folder: str = '', extension: str = '.shp'):
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

    @staticmethod
    def import_svg_to_scen(f_path: str, f_name: str) -> bpyObject:
        # if f_name == 'TER_R_fid_1032.svg' or f_name == 'TER_R_fid_1032':
        #     print(f_name)
        prefix = ("ROAD_S", "TER_R", "BUILD_S", "LD")  # начало у файлов (те которые не pr)
        build_list = ("ZH", "NZH", "PR", "OB")  # pr build
        land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

        bpy.ops.import_curve.svg(filepath=f_path)  # импорт svg по пути
        bpy.ops.object.select_all(action='DESELECT')  # сняли выделение со всего

        # проверка, если добавляются сразу несколько объектов из одного svg
        objects = [x for x in bpy.data.objects if x.name.startswith("Curve")]  # выборка объектов по названию

        if len(objects) > 1:  # если объект в svg это коллекция
            print(f_name)
            # bpy.context.view_layer.objects.active = bpy.data.objects["Curve"]  # активировали объект
            # obj = bpy.context.scene.objects.get("Curve")
            # obj.select_set(True)                                                        # выделили объект
            # obj.name = f_name
            # selection_names = bpy.context.selected_objects            # все выбранные объекты
            [x.select_set(True) for x in objects]  # выделяем объекты из списка объектов
            for ob in bpy.context.selected_objects:
                ob.name = f_name
            bpy.context.view_layer.objects.active = bpy.data.objects[f_name]  # активировали объект !!!!
            bpy.ops.object.join()  # объеденяем быборку объектов в один объект (В АКТИВНЫЙ ОБЪЕКТ ! с его name!!!!!)

        if len(objects) == 1:  # если это одиночный объкт (из svg)
            # # bpy.ops.object.select_by_type(type='CURVE')
            # # bpy.context.scene.objects.active = bpy.data.objects["Curve"]
            # bpy.context.view_layer.objects.active = bpy.data.objects["Curve"]           # активировали объект
            # obj = bpy.context.scene.objects.get("Curve")                                # объект в переменную
            # # obj = bpy.data.objects.get("Curve")                                       # или так попробовать получить obj
            # obj.select_set(True)                                                        # выделили объект
            # obj.name = f_name                                                           # переименовали
            # # obj = [obj for obj in bpy.context.scene.objects if obj.name == "Curve"]
            # # tt = bpy.context.view_layer.objects.active            # получить активных объект
            # # selection_names = bpy.context.selected_objects        # получить выделенные объекты
            # # len(selection_names)                                  # количество выделенных объктов
            # bpy.ops.object.join()
            [x.select_set(True) for x in objects]  # выделяем объекты из списка объектов
            for ob in bpy.context.selected_objects:
                ob.name = f_name

        # collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']

        for obj in bpy.context.selected_objects:
            bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]  # активировали объект
            if f_name.startswith(prefix):
                bpy.ops.object.convert(target='CURVE')  # конвертировали в curve
                bpy.ops.collection.objects_remove_all()  # удаляем объект со всех коллекций
                if f_name.startswith('ROAD_S'):
                    bpy.data.collections['4_Road_S'].objects.link(obj)
                if f_name.startswith("TER_R"):
                    bpy.data.collections['5_tr'].objects.link(obj)
                if f_name.startswith("BUILD_S"):
                    bpy.data.collections['3_Build_S'].objects.link(obj)
                if f_name.startswith("LD"):
                    bpy.data.collections['6_ld'].objects.link(obj)
                # [x for x in bpy.data.collections]                      # список всех коллекций
                # len(bpy.data.collections['BUILD_S_fid_104720.svg'].objects.keys())  # кол-во объектов в коллекции
                coll_del = bpy.data.collections.get(f'{f_name}.svg')  # объект коллекции для удаления
                if len(coll_del.objects.keys()) == 0:  # если в коллекции нет объектов - удаляем
                    bpy.data.collections.remove(coll_del)  # удаляем коллекцию по названию
            else:
                bpy.ops.object.convert(target='MESH')
                bpy.ops.collection.objects_remove_all()
                if f_name.startswith(build_list):
                    bpy.data.collections['1_LD_BUILD'].objects.link(obj)
                if f_name.startswith(land_list):
                    bpy.data.collections['2_LD_LAND'].objects.link(obj)
                # [x for x in bpy.data.collections]                      # список всех коллекций
                coll_del = bpy.data.collections.get(f'{f_name}.svg')  # объект коллекции для удаления
                if len(coll_del.objects.keys()) == 0:  # если в коллекции нет объектов - удаляем
                    bpy.data.collections.remove(coll_del)  # удаляем коллекцию по названию

        bpy.ops.object.select_all(action='DESELECT')

        if not f_name.startswith(prefix):
            x = f_name
            r = x.split('_fid_')[0]
            h = float(r.split('_')[2])  # получаем высоту в метрах
            obj = bpy.data.objects.get(f_name)  # объект в переменную
            obj.users_collection  # в какой коллекции объект
            obj.select_set(True)  # выделили объект
            bpy.context.view_layer.objects.active = bpy.data.objects[f_name]  # активировали объект
            bpy.ops.object.mode_set(mode='EDIT')  # Toggle edit mode
            bpy.ops.mesh.select_mode(type='FACE')  # Change to face selection
            bpy.ops.mesh.select_all(action='SELECT')  # Select all faces
            obj = bpy.context.active_object
            bpy.ops.mesh.extrude_faces_move(
                MESH_OT_extrude_faces_indiv={"mirror": True},
                TRANSFORM_OT_shrink_fatten={"value": h,
                                            "mirror": True,
                                            "proportional_edit_falloff": 'SMOOTH',
                                            "proportional_size": 1,
                                            "snap": False,
                                            "snap_target": 'CLOSEST',
                                            "snap_point": (0, 0, 0),
                                            "snap_align": False,
                                            "snap_normal": (0, 0, 0),
                                            "release_confirm": False})

        for x in bpy.context.selected_objects:
            if context.object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
        print(f_name, "... imported!")
        return

    @staticmethod
    def move_by_z(context):
        collection_list = ['1_LD_BUILD']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)

        selection_objects = bpy.context.selected_objects
        for x in selection_objects:
            r = x.name.split('_fid_')[0]
            try:
                z_val = r.split('_')[3]
                if z_val:
                    z_val = float(z_val)
                    bpy.context.view_layer.objects.active = bpy.data.objects[x.name]  # активировали объект
                    bpy.data.objects[x.name].location.z += z_val
            except:
                pass

# ------------------------------------------------------------------------
#    MATERIALS
# ------------------------------------------------------------------------
class Work_mat_v_2(Operator):
    bl_label = 'SGN_Function'
    bl_idname = 'sgn.sgn_op'

    @staticmethod
    def clear_slots_mat_obj(ob):
        # delete all slot from obj
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        for x in ob.material_slots:  # For all of the materials in the selected object:
            bpy.context.object.active_material_index = 0  # select the top material
            bpy.ops.object.material_slot_remove()  # delete it

    @staticmethod
    def create_materials():
        # get all exist scen material list
        exist_scen_mat_list = [x[0] for x in bpy.data.materials.items()]

        # create list of names
        mat_names_list = [
            "DF",  # default mat
        ]

        # create slots of materials by list names
        [bpy.data.materials.new(name=x) for x in mat_names_list if x not in exist_scen_mat_list]

    @staticmethod
    def asign_default_to_obj(ob):
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        ob.data.materials.append(bpy.data.materials["DF"])

    @staticmethod
    def asign_mat_to_obj(ob):
        # bpy.ops.object.select_all(action='DESELECT')
        # bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        name_mat_gis = ((ob.name).split('_fid_')[0]).split('_')[0]
        mat = bpy.data.materials.get(name_mat_gis)
        # ob.data.materials.append(mat)
        if ob.data.materials:
            # assign to 1st material slot
            ob.data.materials[0] = mat
        else:
            # no slots
            ob.data.materials.append(mat)
        # build_list = ["ZH", "NZH", "PR", "OB"]
        # if name_mat_gis in build_list:
        #     top_mat = name_mat_gis + "_DF"
        #     ob.data.materials.append(bpy.data.materials[top_mat])

    @staticmethod
    def delete_all_uv_layer_from_obj(ob):
        # удаляем все uv слои с объекта
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        for uv_layer in bpy.context.object.data.uv_layers:
            bpy.context.object.data.uv_layers.remove(uv_layer)

    @staticmethod
    def create_uv_layer_for_obj(ob):
        # создаем новую сетку UV
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]
        name_uv_layer = ((bpy.context.active_object.name).split('_fid_')[1]).split('_')[0]
        bpy.context.active_object.data.uv_layers.new(name=name_uv_layer)

    @staticmethod
    def get_indx_polygon(ob):
        # получаем 2 списка индексов полигонов объекта (список паралелльных z полигонов и полигонов под текстуры)
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
    def assign_mat_to_face(ob, list_indx_face, mat_name):
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

    @staticmethod
    def assign_mat_to_face_2(ob, list_indx_face, list_indx_face_Z, mat_name):
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

# ------------------------------------------------------------------------
#    CAM_SUN_RENDER
# ------------------------------------------------------------------------
class work_cam_lights(Operator):
    bl_label = 'CAM_Function'
    bl_idname = 'cam.cam_op'

    @staticmethod
    def get_coord_obj(ob):
        object = bpy.data.objects.get(ob.name)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
        v_global = bpy.context.object.location
        return v_global

    @staticmethod
    def del_cam(ob):
        bpy.data.cameras.remove(ob)

    @staticmethod
    def get_cam(ob):
        cam = bpy.data.cameras.get(ob.name)
        return cam

    @staticmethod
    def custom_camera_clip_end(ob):
        # clip_end
        name_cam = ob.name
        bpy.data.cameras[name_cam].clip_start = 1       # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!УДАЛИТЬ ЕСЛИ
        bpy.data.cameras[name_cam].clip_end = 900000

    @staticmethod
    def custom_camera_background():
        path_to_FGM = ((bpy.context.scene.my_tool.fgm_path).replace('\\', '//').replace('"', ''))

        filepath = [
            (path_to_FGM + r"\N.png"),
            (path_to_FGM + r"\S.png"),
            (path_to_FGM + r"\E.png"),
            (path_to_FGM + r"\W.png")
        ]
        imgN = bpy.data.images.load(filepath[0])
        imgS = bpy.data.images.load(filepath[1])
        imgE = bpy.data.images.load(filepath[2])
        imgW = bpy.data.images.load(filepath[3])

        cam_obj_list = [x for x in bpy.data.objects if x.type == 'CAMERA']
        for cam in cam_obj_list:
            name_cam = cam.name
            active_cam = bpy.data.cameras.get(name_cam)  # активировали объект
            # active_cam.data.show_background_images = True
            bg = active_cam.background_images.new()
            if cam.name == '01_North':
                bg.image = imgN
            if cam.name == '02_South':
                bg.image = imgS
            if cam.name == '03_East':
                bg.image = imgE
            if cam.name == '04_West':
                bg.image = imgW
            active_cam.show_background_images = True

            # bpy.ops.view3d.background_image_add()

        # bpy.data.cameras[name_cam].

    @staticmethod
    def creat_cam(new_cam_name, coord):
        cam_list = ['01_North', '02_South', '03_East', '04_West']
        camera_data = bpy.data.cameras.new(name=new_cam_name)
        camera_object = bpy.data.objects.new(new_cam_name, camera_data)
        bpy.context.scene.collection.objects.link(camera_object)
        bpy.context.view_layer.objects.active = camera_object
        # camera_object.data.alpha = 1
        # tt = bpy.context.view_layer.objects.active
        # tt.data.alpha = 1.0
        camera_object.scale[0] = 70
        camera_object.scale[1] = 70
        camera_object.scale[2] = 70
        if new_cam_name == '01_North':
            camera_object.location = (coord[0], coord[1] - 600, 300)
            camera_object.rotation_euler[0] = 1.22522
        if new_cam_name == '02_South':
            camera_object.location = (coord[0], coord[1] + 600, 300)
            camera_object.rotation_euler[0] = -2.1
            camera_object.rotation_euler[1] = 3.14159
        if new_cam_name == '03_East':
            camera_object.location = (coord[0] - 600, coord[1], 300)
            camera_object.rotation_euler[0] = 4.3
            camera_object.rotation_euler[2] = 1.71
            camera_object.rotation_euler[1] = 3.14159
        if new_cam_name == '04_West':
            camera_object.location = (coord[0] + 600, coord[1], 300)
            camera_object.rotation_euler[0] = 4.3
            camera_object.rotation_euler[2] = -1.71
            camera_object.rotation_euler[1] = -3.14159


    @staticmethod
    def add_sun_light(x, y, z):
        light_data = bpy.data.lights.new(name="00_SUN", type='SUN')
        light_object = bpy.data.objects.new(name="00_SUN", object_data=light_data)
        bpy.context.collection.objects.link(light_object)
        bpy.context.view_layer.objects.active = light_object
        light_object.location = (x, y, z + 100)
        bpy.data.lights["00_SUN"].energy = 11
        bpy.data.lights["00_SUN"].angle = math.pi * 50.0 / 180.0

    @staticmethod
    def del_sun(ob):
        bpy.data.lights.remove(ob)

    @staticmethod
    def get_sun(ob):
        sun = bpy.data.lights.get(ob.name)
        return sun

# ------------------------------------------------------------------------
#    OPERATORS
# ------------------------------------------------------------------------
class My_func(Operator):
    bl_idname = 'test.test_op'
    bl_label = 'Test'
    # bl_description = 'Test'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(
        items=[
            ('RUN', 'RUN', 'run'),
            ('MAT_ASSING', 'MAT_ASSING', 'mat_assing'),
            ('ASS_MAT', 'ASS_MAT', 'ass_mat'),
            ('LUCK', 'LUCK', 'luck'),
            ('DEL_MAT', 'DEL_MAT', 'del_mat'),
            ('CAM_SUN', 'CAM_SUN', 'cam_sun'),
            ('CLEAR', 'clear scene', 'clear scene'),
            ('ADD_CUBE', 'add cube', 'add cube'),
            ('INF', 'ShowMessageBox', 'inf scene')
        ]
    )

    def execute(self, context):
        if self.action == 'RUN':
            self.show_vwport(context=context)
            self.import_by_select_layer(context=context)
            self.hide_vwport(context=context)
        elif self.action == 'LUCK':
            #  ------------------------------------------------------------------------------------------------
            start_luck = time.time()
            print(f"             ---  старт lucky ---")
            #  ------------------------------------------------------------------------------------------------
            self.run(context=context)
            self.select_obj_from_two_collection(context=context)
            self.del_all_svg_mat(context=context)

            if My_func.check_mtl_in_scene(context=context) > 0:
                self.ass_mat(context=context)
            self.hide_vwport(context=context)
            #  ------------------------------------------------------------------------------------------------
            print(f"--- LUCKy все выполнение  заняло {(time.time() - start_luck)} seconds ---")
            #  ------------------------------------------------------------------------------------------------

        elif self.action == 'MAT_ASSING':
            self.ass_mat(context=context)
            # self.del_all_svg_mat(context=context)
        elif self.action == 'ASS_MAT':
            self.ass_mat(context=context)
        elif self.action == 'CAM_SUN':
            self.cam_sun(context=context)
        elif self.action == 'CLEAR':
            self.clear_scene(context=context)
        elif self.action == 'ADD_CUBE':
            self.ShowMessageBox('ADD_CUBE')
            # self.add_cube(context=context)
        elif self.action == 'INF':
            self.ShowMessageBox('INF')
            # self.ShowMessageBox()
        elif self.action == 'DEL_MAT':
            self.del_mat_from_selection_objects(context=context)
        return {'FINISHED'}

    @staticmethod
    def import_by_select_layer(context):
        #  ------------------------------------------------------------------------------------------------
        start_time = time.time()
        print(f"--- START IMPORT ---")
        #  ------------------------------------------------------------------------------------------------

        # путь к GPKG
        path_to_GPKG = (bpy.context.scene.my_tool.my_path.replace('"', ''))
        # path_to_GPKG = ((r'C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg').replace('"', ''))
        path_to_GPKG = ((path_to_GPKG).replace('"', ''))

        # проверка, по этому пути есть ли файл
        if not os.path.isfile(path_to_GPKG):
            My_func.ShowMessageBox(u'По указанному пути нет gpkg!')
            return None
            # raise Exception(u"Not file gpkg by this path!")

        # проверка, по этому пути есть ли файл с нужным расширением
        file_name, file_extension = os.path.splitext(path_to_GPKG)
        if file_extension != '.gpkg':
            My_func.ShowMessageBox(u'Неверное расширение файла! Нужен *.gpkg')
            return None
            # raise Exception(u"File is not *.gpkg!")

        # граница обрезки
        name_granica = bpy.context.scene.my_tool.my_string_add
        if name_granica =="граничка название" or name_granica == "":  # если не ввели граничку то присвоить по умлочанию
            My_func.ShowMessageBox(u'Неверное название границы обрезки!')
            return None

        My_func.ShowMessageBox(f'границf обрезки {name_granica}')

        # получаем ссылку на DataSource Gdal
        ds = My_class.open_file_by_gdal(path_to_GPKG)

        # словарь слоёв с которыми работаем
        lst_src_layer = {
            "bld_pr": 'total_building_pr',
            "lnd_pr": 'total_a_landscaping_pr',
            "road_s": 'ROAD_POLY',
            "bld_s": 'BUILDING',
            "tr": 'total_terr_razvitie',
            "ld": 'ld_region'}

        # слой в котором граничка лежит
        str_layer_grn = 'GRANICA_OBREZKI'

        # название колонки для фильтрации в слое где граничка обрезки
        col_filtr_name = "GR_OBREZKI"

        # название колонки для фильтрации по слоям
        col_split_name = "t_from_contents"

        # получаем словарь отфильтрованых datasource по каждому слою/.
        dct_ds = {}
        for i in lst_src_layer.keys():
            dct_ds[i] = My_class.filter_by_coordinate(
                name_granica=name_granica,
                name_column=col_filtr_name,
                name_f_layer=str_layer_grn,
                nm_lr_for_flt=lst_src_layer[i],
                ds=ds
            )

        # сохраняем datasource gdal в оперативке (в словаре DataSources
        dct_ds_mem = {}  # словарь DataSource в памяти пк
        for i in dct_ds.keys():
            dct_ds_mem[i] = My_class.save_lr_to_mem(dct_ds[i], i)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        ds_mem = My_class.save_Dict_With_Ds_To_Mem(dct_ds)

        # перегоняем DataSource в DataFrame
        df_ds_buil = My_class.lr_to_dataframe(ds_mem[0])  # bld_pr
        df_ds_land = My_class.lr_to_dataframe(ds_mem[1])  # lnd_pr
        df_ds_road = My_class.lr_to_dataframe(ds_mem[2])  # road_s
        df_ds_blds = My_class.lr_to_dataframe(ds_mem[3])  # bld_s
        df_ds_tr = My_class.lr_to_dataframe(ds_mem[4])  # tr
        df_ds_ld = My_class.lr_to_dataframe(ds_mem[5])  # ld

        # pandas Dataframe -> GeoPandas GeoDataFrame
        gdf_ds_buil = My_class.pandas_to_geopandas(df_ds_buil)
        gdf_ds_land = My_class.pandas_to_geopandas(df_ds_land)
        gdf_ds_road_s = My_class.pandas_to_geopandas(df_ds_road)
        gdf_ds_bld_s = My_class.pandas_to_geopandas(df_ds_blds)
        gdf_ds_tr = My_class.pandas_to_geopandas(df_ds_tr)
        gdf_ds_ld = My_class.pandas_to_geopandas(df_ds_ld)


        [print(x) for x in dct_ds.keys()]


        # получаем значение какого набора слоёв нужно получить в выборку
        sel_layer = bpy.context.scene.my_tool.my_enum

        # словарь слоёв
        dic_pul_layers = {
             'OP1': {"bld_pr": 'total_building_pr', "lnd_pr": 'total_a_landscaping_pr'},
             'OP2': {"road_s": 'ROAD_POLY', "bld_s": 'BUILDING'},
             'OP3': {"tr": 'total_terr_razvitie', "ld": 'ld_region'},
             'OP4': {"bld_pr": 'total_building_pr'},
             'OP5': {"lnd_pr": 'total_a_landscaping_pr'},
             'OP6': {"bld_s": 'BUILDING'},
             'OP7': {"road_s": 'ROAD_POLY'},
             'OP8': {"tr": 'total_terr_razvitie'},
             'OP9': {"ld": 'ld_region'}
        }

        # определяем какие слои выбрал пользователь для импорта
        sel_lrs = dic_pul_layers[sel_layer]

        print(sel_lrs)

        # создали временный каталог для сохранения результатов svg файлов
        path_to_script_folder = bpy.context.scene.my_tool.my_string_tmp  # тут путь к месту где скрипт запустили
        tmpdirpath = tempfile.mkdtemp(dir=path_to_script_folder)
        print(f'Временный каталог создан по пути - {tmpdirpath}')

        print(sel_layer)
        # перегоняем в svg только те geodataframe которые попадают по выбор пользователя

        if sel_layer == 'OP1':
            # перегоняем build_pr в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_buil) != 0:
                val_build_p = My_class.export_gdf_to_svg(gdf_ds_buil, name_obj_from_col, tmpdirpath)
            # перегоняем land_pr в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_land) != 0:
                val_land_p = My_class.export_gdf_to_svg(gdf_ds_land, name_obj_from_col, tmpdirpath)

        if sel_layer == 'OP2':
            # перегоняем ROAD SUSCH в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_road_s) != 0:
                val_road_s = My_class.export_gdf_to_svg(gdf_ds_road_s, name_obj_from_col, tmpdirpath, "ROAD_S")
            # перегоняем BUILD SUSCH в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_bld_s) != 0:
                val_bld_s = My_class.export_gdf_to_svg(gdf_ds_bld_s, name_obj_from_col, tmpdirpath, "BUILD_S")

        if sel_layer == 'OP3':
            # перегоняем TR в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_tr) != 0:
                val_ds_tr = My_class.export_gdf_to_svg(gdf_ds_tr, name_obj_from_col, tmpdirpath, "TER_R")
            # перегоняем LD в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_ld) != 0:
                val_ds_ld = My_class.export_gdf_to_svg(gdf_ds_ld, name_obj_from_col, tmpdirpath, "LD")

        if sel_layer == 'OP4':
            # перегоняем build_pr в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_buil) != 0:
                val_build_p = My_class.export_gdf_to_svg(gdf_ds_buil, name_obj_from_col, tmpdirpath)

        if sel_layer == 'OP5':
            # перегоняем land_pr в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_land) != 0:
                val_land_p = My_class.export_gdf_to_svg(gdf_ds_land, name_obj_from_col, tmpdirpath)

        if sel_layer == 'OP6':
            # перегоняем BUILD SUSCH в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_bld_s) != 0:
                val_bld_s = My_class.export_gdf_to_svg(gdf_ds_bld_s, name_obj_from_col, tmpdirpath, "BUILD_S")

        if sel_layer == 'OP7':
            # перегоняем ROAD SUSCH в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_road_s) != 0:
                val_road_s = My_class.export_gdf_to_svg(gdf_ds_road_s, name_obj_from_col, tmpdirpath, "ROAD_S")

        if sel_layer == 'OP8':
            # перегоняем TR в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_tr) != 0:
                val_ds_tr = My_class.export_gdf_to_svg(gdf_ds_tr, name_obj_from_col, tmpdirpath, "TER_R")

        if sel_layer == 'OP9':
            # перегоняем LD в svg каждый geodadaframe
            name_obj_from_col = col_split_name
            if len(gdf_ds_ld) != 0:
                val_ds_ld = My_class.export_gdf_to_svg(gdf_ds_ld, name_obj_from_col, tmpdirpath, "LD")


        # Создаем новые колекции для проектируемых объектов и сущпола !!!!
        collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']
        for i in collection_list:
            if i not in [x.name for x in bpy.context.blend_data.collections]:
                my_collection = bpy.context.blend_data.collections.new(name=i)
                bpy.context.collection.children.link(my_collection)


        # импортируем svg в сцену
        list_path_all_svg = My_class.getPathAndNamesFilesInFolderByExtension(tmpdirpath,
                                                                             '.svg')  # список всех svg с путями
        for val_path, val_name in zip(list_path_all_svg[0], list_path_all_svg[1]):
            My_class.import_svg_to_scen(val_path, val_name)

        # поднимаем z
        My_class.move_by_z(context=context)

        # удаляем ненужные пустые коллекции
        for col in bpy.context.blend_data.collections:
            if len(col.objects.keys()) == 0:
                bpy.data.collections.remove(col)  # удалили коллекции

        # # Скроем сущпольные коллекции в сцене
        # for i, x in enumerate(bpy.data.collections.items()):
        #     if x[0] in ['1_LD_BUILD']:
        #         bpy.data.collections[i].hide_viewport = True
        #     if x[0] in ['2_LD_LAND']:
        #         bpy.data.collections[i].hide_viewport = True
        #     if x[0] in ['5_tr']:
        #         bpy.data.collections[i].hide_viewport = True
        #     if x[0] in ['6_ld']:
        #         bpy.data.collections[i].hide_viewport = True

        # удаляем все svg материалы из сцены
        bpy.ops.object.select_all(action='DESELECT')  # снимаем выделение со всех объектов
        [bpy.data.materials.remove(x) for x in bpy.data.materials if x.name.startswith('SVGMat')]

        # выделяем все новые объекты в сцене
        [x.select_set(True) for x in bpy.data.objects if x.name in list_path_all_svg[1]]  # выделяем объекты из списка объектов

        # назначаем материалы новым объектам
        My_func.ass_mat(context)


        # добавляем все коллекцию в сцену
        try:
            for coll in bpy.context.blend_data.collections:
                bpy.context.scene.collection.children.link(coll)
        except Exception as e:
            print(f'ERR {e} Коллекция уже сущствует!  {coll.name}')

        # устанавливаем нормльное отображение в окне blendera
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        s.clip_start = 1
                        s.clip_end = 900000

        # НЕ ЗАБЫВАЕМ УДАЛЯТЬ ВРЕМЕННЫЙ КАТАЛОГ С SVG ФАЙЛАМИ !!!!!!!!!!!!!!!!!!
        shutil.rmtree(tmpdirpath)  # функция удаляет каталог и все содержимое рекурсивно
        print(f"Удалили временный каталог - {tmpdirpath}")

        #  ------------------------------------------------------------------------------------------------
        print(f" --- END IMPORT  выполнено за {(time.time() - start_time)} seconds ---")
        #  ------------------------------------------------------------------------------------------------

    @staticmethod
    def run(context):
        #  ------------------------------------------------------------------------------------------------
        start_time = time.time()
        print(f"--- START IMPORT ---")
        #  ------------------------------------------------------------------------------------------------

        # путь к GPKG
        path_to_GPKG = (bpy.context.scene.my_tool.my_path.replace('"', ''))
        # path_to_GPKG = ((r'C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg').replace('"', ''))
        path_to_GPKG = ((path_to_GPKG).replace('"', ''))

        # проверка, по этому пути есть ли файл
        if not os.path.isfile(path_to_GPKG):
            My_func.ShowMessageBox(u'По указанному пути нет gpkg!')
            return None
            # raise Exception(u"Not file gpkg by this path!")

        # проверка, по этому пути есть ли файл с нужным расширением
        file_name, file_extension = os.path.splitext(path_to_GPKG)
        if file_extension != '.gpkg':
            My_func.ShowMessageBox(u'Неверное расширение файла! Нужен *.gpkg')
            return None
            # raise Exception(u"File is not *.gpkg!")

        # граница обрезки
        name_granica = bpy.context.scene.my_tool.my_string
        if name_granica =="граничка название" or name_granica == "":  # если не ввели граничку то присвоить по умлочанию
            My_func.ShowMessageBox(u'Неверное название границы обрезки!')
            return None

        # получаем ссылку на DataSource Gdal
        ds = My_class.open_file_by_gdal(path_to_GPKG)

        # словарь слоёв с которыми работаем
        lst_src_layer = {
            "bld_pr": 'total_building_pr',
            "lnd_pr": 'total_a_landscaping_pr',
            "road_s": 'ROAD_POLY',
            "bld_s": 'BUILDING',
            "tr": 'total_terr_razvitie',
            "ld": 'ld_region'}

        # слой в котором граничка лежит
        str_layer_grn = 'GRANICA_OBREZKI'

        # название колонки для фильтрации в слое где граничка обрезки
        col_filtr_name = "GR_OBREZKI"

        # название колонки для фильтрации по слоям
        col_split_name = "t_from_contents"

        # получаем словарь отфильтрованых datasource по каждому слою/.
        dct_ds = {}
        for i in lst_src_layer.keys():
            dct_ds[i] = My_class.filter_by_coordinate(
                name_granica=name_granica,
                name_column=col_filtr_name,
                name_f_layer=str_layer_grn,
                nm_lr_for_flt=lst_src_layer[i],
                ds=ds
            )

        # сохраняем datasource gdal в оперативке (в словаре DataSources
        dct_ds_mem = {}  # словарь DataSource в памяти пк
        for i in dct_ds.keys():
            dct_ds_mem[i] = My_class.save_lr_to_mem(dct_ds[i], i)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        ds_mem = My_class.save_Dict_With_Ds_To_Mem(dct_ds)

        # перегоняем DataSource в DataFrame
        df_ds_buil = My_class.lr_to_dataframe(ds_mem[0])  # bld_pr
        df_ds_land = My_class.lr_to_dataframe(ds_mem[1])  # lnd_pr
        df_ds_road = My_class.lr_to_dataframe(ds_mem[2])  # road_s
        df_ds_blds = My_class.lr_to_dataframe(ds_mem[3])  # bld_s
        df_ds_tr = My_class.lr_to_dataframe(ds_mem[4])  # tr
        df_ds_ld = My_class.lr_to_dataframe(ds_mem[5])  # ld

        # pandas Dataframe -> GeoPandas GeoDataFrame
        gdf_ds_buil = My_class.pandas_to_geopandas(df_ds_buil)
        gdf_ds_land = My_class.pandas_to_geopandas(df_ds_land)
        gdf_ds_road_s = My_class.pandas_to_geopandas(df_ds_road)
        gdf_ds_bld_s = My_class.pandas_to_geopandas(df_ds_blds)
        gdf_ds_tr = My_class.pandas_to_geopandas(df_ds_tr)
        gdf_ds_ld = My_class.pandas_to_geopandas(df_ds_ld)

        # путь к временному каталогу
        path_to_tmp = (bpy.context.scene.my_tool.my_string_tmp.replace('"', ''))
        # path_to_GPKG = ((r'C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg').replace('"', ''))
        path_to_tmp = ((path_to_tmp).replace('"', ''))

        if path_to_tmp == "":
            My_func.ShowMessageBox(u'Неверное название каталога для временных файлов!')
            print(f'Pick correctly path to save tmp files!')
            return None

        # создали временный каталог для сохранения результатов svg файлов
        path_to_script_folder = os.path.dirname(path_to_tmp)
        tmpdirpath = tempfile.mkdtemp(dir=path_to_script_folder)
        print(f'Временный каталог создан по пути - {tmpdirpath}')

        # перегоняем build_pr в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_buil) != 0:
            val_build_p = My_class.export_gdf_to_svg(gdf_ds_buil, name_obj_from_col, tmpdirpath)


        # перегоняем land_pr в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_land) != 0:
            val_land_p = My_class.export_gdf_to_svg(gdf_ds_land, name_obj_from_col, tmpdirpath)


        # перегоняем ROAD SUSCH в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_road_s) != 0:
            val_road_s = My_class.export_gdf_to_svg(gdf_ds_road_s, name_obj_from_col, tmpdirpath, "ROAD_S")

        # перегоняем BUILD SUSCH в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_bld_s) != 0:
            val_bld_s = My_class.export_gdf_to_svg(gdf_ds_bld_s, name_obj_from_col, tmpdirpath, "BUILD_S")

        # перегоняем TR в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_tr) != 0:
            val_ds_tr = My_class.export_gdf_to_svg(gdf_ds_tr, name_obj_from_col, tmpdirpath, "TER_R")

        # перегоняем LD в svg каждый geodadaframe
        name_obj_from_col = col_split_name
        if len(gdf_ds_ld) != 0:
            val_ds_ld = My_class.export_gdf_to_svg(gdf_ds_ld, name_obj_from_col, tmpdirpath, "LD")

        # Создаем новые колекции для проектируемых объектов и сущпола !!!!
        collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']
        for i in collection_list:
            if i not in [x.name for x in bpy.context.blend_data.collections]:
                my_collection = bpy.context.blend_data.collections.new(name=i)
                bpy.context.collection.children.link(my_collection)


        # импортируем svg в сцену
        list_path_all_svg = My_class.getPathAndNamesFilesInFolderByExtension(tmpdirpath,
                                                                             '.svg')  # список всех svg с путями
        for val_path, val_name in zip(list_path_all_svg[0], list_path_all_svg[1]):
            My_class.import_svg_to_scen(val_path, val_name)

        # поднимаем z
        My_class.move_by_z(context=context)

        # удаляем ненужные пустые коллекции
        for col in bpy.context.blend_data.collections:
            if len(col.objects.keys()) == 0:
                bpy.data.collections.remove(col)  # удалили коллекции



        # добавляем все коллекцию в сцену
        try:
            for coll in bpy.context.blend_data.collections:
                bpy.context.scene.collection.children.link(coll)
        except Exception as e:
            print(f'ERR {e} Коллекция уже сущствует!  {coll.name}')

        # устанавливаем нормльное отображение в окне blendera
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        s.clip_start = 1
                        s.clip_end = 900000

        # НЕ ЗАБЫВАЕМ УДАЛЯТЬ ВРЕМЕННЫЙ КАТАЛОГ С SVG ФАЙЛАМИ !!!!!!!!!!!!!!!!!!
        shutil.rmtree(tmpdirpath)  # функция удаляет каталог и все содержимое рекурсивно
        print(f"Удалили временный каталог - {tmpdirpath}")

    @staticmethod
    def hide_vwport(context):
        # Скроем сущпольные коллекции в сцене
        for i, x in enumerate(bpy.data.collections.items()):
            if x[0] in ['1_LD_BUILD']:
                bpy.data.collections[i].hide_viewport = True
            if x[0] in ['2_LD_LAND']:
                bpy.data.collections[i].hide_viewport = True
            if x[0] in ['3_Build_S']:
                bpy.data.collections[i].hide_render = True
            if x[0] in ['4_Road_S']:
                bpy.data.collections[i].hide_render = True
            if x[0] in ['5_tr']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True
            if x[0] in ['6_ld']:
                bpy.data.collections[i].hide_viewport = True
                bpy.data.collections[i].hide_render = True

    @staticmethod
    def show_vwport(context):
        # откроем все коллекции в сцене
        for i, x in enumerate(bpy.data.collections.items()):
            bpy.data.collections[i].hide_viewport = False
            bpy.data.collections[i].hide_render = False


    @staticmethod
    def cam_sun(context):
        cl = work_cam_lights  # назначаем класс переменной (объекту)

        # удаляем все камеры
        [cl.del_cam(cl.get_cam(x)) for x in bpy.data.objects if x.type == 'CAMERA']

        # удаляем все SUN из сцены
        [cl.del_sun(cl.get_sun(x)) for x in bpy.data.lights if x.type == 'SUN']

        # получаем координаты выбранного пользователем объекта (активного)
        ob = bpy.context.active_object  # получили в переменную активный объект
        coord_cur_obj = cl.get_coord_obj(ob)  # получили координаты активного объекта

        # добавляем камены по списку
        cam_list = ['01_North', '02_South', '03_East', '04_West']
        [cl.creat_cam(x, coord_cur_obj) for x in cam_list]

        # customize cameras
        [cl.custom_camera_clip_end(x) for x in bpy.data.objects if x.type == 'CAMERA']  # clip_end
        cl.custom_camera_background()  # add background image to cameras
        for x in bpy.data.cameras:
            x.background_images[0].alpha = 1

        # добавляем SUN
        cl.add_sun_light(coord_cur_obj[0] + 300, coord_cur_obj[1], coord_cur_obj[2] + 800)

        # bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'
        bpy.data.scenes["Scene"].render.film_transparent = True
        bpy.data.scenes["Scene"].cycles.progressive = 'PATH'
        bpy.data.scenes["Scene"].cycles.samples = 256
        bpy.data.scenes["Scene"].cycles.preview_samples = 128
        bpy.context.scene.render.resolution_x = 3680
        bpy.context.scene.render.resolution_y = 2600


    @staticmethod
    def select_obj_from_two_collection(context):
        collection_list = ['1_LD_BUILD', '2_LD_LAND']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)

    @staticmethod
    def check_mtl_in_scene(context):
        l_mtl = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV", "ZH", "NZH", "PR", "OB")
        mtl = [x for x in bpy.data.materials if x.name.startswith(l_mtl)]
        if len(mtl) == 0:
            My_func.ShowMessageBox(f'В СЦЕНУ НЕ ДОБАВЛЕНЫ МАТЕРИАЛЫ!!!!')
            return 0
        return len(mtl)

    @staticmethod
    def ass_mat(context):
        #  ------------------------------------------------------------------------------------------------
        start_time = time.time()
        print("--- START ASSIGN MATERIALS ---")
        #  ------------------------------------------------------------------------------------------------

        scene = context.scene
        mytool = scene.my_tool

        build_list = ["ZH", "NZH", "PR", "OB"]
        land_list = ["SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV"]
        build_top_list = ["ZH_DF", "NZH_DF", "PR_DF", "OB_DF"]

        cl = Work_mat_v_2  # # инициируем переменную для класса

        sel_objs = [ob for ob in bpy.context.selected_objects]
        if len(sel_objs) > 0:
            # назначаем материалы на каждый face (polygon)
            for x in sel_objs:
                if x.name not in ['Camera', 'Cube', 'Light'] and x.type == 'MESH':

                    # name_mat_default = 'DF'  # получили назв default material
                    mat_name = ((x.name).split('_fid_')[0]).split('_')[
                        0]  # получили назв основного материала из имени объекта

                    if mat_name in build_list:
                        lz, lt = cl.get_indx_polygon(x)  # получаем листы с индексами полигонов паралельных z и нет
                        cl.assign_mat_to_face_2(x, lt, lz,
                                                mat_name)  # назначили основной материал каждому полигону из списка
                    if mat_name in land_list:
                        cl.asign_mat_to_obj(x)  # назначили на весь объект материал для landscaping

        else:
            # назначаем материалы на каждый face (polygon)
            for x in bpy.data.objects:
                if x.name not in ['Camera', 'Cube', 'Light'] and x.type == 'MESH':

                    # name_mat_default = 'DF'  # получили назв default material
                    mat_name = ((x.name).split('_fid_')[0]).split('_')[
                        0]  # получили назв основного материала из имени объекта

                    if mat_name in build_list:
                        lz, lt = cl.get_indx_polygon(x)  # получаем листы с индексами полигонов паралельных z и нет
                        cl.assign_mat_to_face_2(x, lt, lz,
                                                mat_name)  # назначили основной материал каждому полигону из списка
                    if mat_name in land_list:
                        cl.asign_mat_to_obj(x)  # назначили на весь объект материал для landscaping`

        #  ------------------------------------------------------------------------------------------------
        print("---  %s seconds ASSIGN MATERIALS ---" % (time.time() - start_time))
        #  ------------------------------------------------------------------------------------------------

    @staticmethod
    def clear_scene(context):
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

    @staticmethod
    def del_mat_from_selection_objects(context):
        for obj in bpy.context.selected_editable_objects:
            obj.active_material_index = 0
            for i in range(len(obj.material_slots)):
                bpy.ops.object.material_slot_remove({'object': obj})

    @staticmethod
    def del_all_svg_mat(context):
        [bpy.data.materials.remove(x) for x in bpy.data.materials if x.name.startswith('SVGMat')]

    @staticmethod
    def ShowMessageBox(message="TEXT", title="Message Box", icon='INFO'):
        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)



# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------

classes = (
    MyProperties,
    Panel_one,
    Panel_two,
    My_class,
    Work_mat_v_2,
    work_cam_lights,
    # Panel_three,
    # Panel_four
    My_func
)

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == '__main__':
    register()
