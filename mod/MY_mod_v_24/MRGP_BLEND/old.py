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

# ------------------------------------------------------------------------
#    MATERIALS
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
#    CAM_SUN_RENDER
# ------------------------------------------------------------------------

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
