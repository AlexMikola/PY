# -*- coding: utf-8 -*-
import bpy
import sys
import os
import tempfile
import time

# импортируем пути к своим модулям
ORIG_SYS_PATH = list(sys.path)
MOD_PATH = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\mod\MRGP_BLEND"
if MOD_PATH not in ORIG_SYS_PATH:
    sys.path.insert(1, MOD_PATH)
    MOD_SYS_PATH = list(sys.path)

# from app_0_mains import Luck as MF
# import app_0_mains as MF
from app_1_mains import LUCK as LF
from app_1_mains import AssMaterials as AF
from app_1_mains import CamSun as CF

class Toster:
    def __init__(self):
        #  ------------------------------------------------------------------------------------------------
        start_time = time.time()
        print(f"--- START ALL ---")
        #  ------------------------------------------------------------------------------------------------

        self.LF = LF()                                                      # инициализируем класс

        LF.run_import(self.LF)









        # берем путь из панели bpy
        self.LF.path_to_GPKG = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg"

        # открываем gdal-ом gpkg по пути
        self.LF.ds = LF.open_file_by_gdal(self.LF)

        # берем название значения объекта для фильта wkt, значение из семантики
        self.LF.name_granica = "2"

        # получаем словарь datasource отфильтрованный по граничке обрезки (wkt)
        self.LF.dict_ds = LF.get_dict_from_ds(self.LF)

        # переросим словарь с отдельными ds по слоям - в память пк
        self.LF.dict_ds_mem = LF.save_dict_of_lrs_to_mem(self.LF)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        self.LF.ds_mem = LF.save_Dict_With_Ds_To_Mem(self.LF)

        # перегоняем DataSource в DataFrame
        self.LF.dict_df = LF.lr_to_dataframe(self.LF)

        # словарь pandas Dataframe -> словарь GeoPandas GeoDataFrame
        self.LF.dict_gdf = LF.pandas_to_geopandas(self.LF)

        # путь к временному каталогу - берем из панели bpy
        self.LF.tmp_path_fldr = r"C:\Users\dolgushin_an\Desktop\\"

        # создали временный каталог для сохранения результатов svg файлов
        self.LF.tmp_path_fldr = LF.create_tmp_folder_by_path(self.LF)

        # експорт каждого gdf из словаря в *.svg
        LF.export_gdf_to_svg(self.LF)

        # получаем список всех путей и названий файлов во временном каталоге по расширению '*.svg'
        self.LF.svg_path_names = LF.get_path_names_files_by_exten(self.LF.tmp_path_fldr, extension=".svg")

        # # импортируем svg в сцену
        # LF.import_svg_to_scen(self.LF)

        # импортируем svg в сцену
        LF.iter_import_svg_to_scen(self.LF)

        # удаляем временный каталог
        LF.del_tmp_folder(self.LF)

        # # extrude всех curve
        # LF.extrude_curves_in_data(self.LF)

        # extrude всех curve
        LF.iter_extrude_curves_in_data(self.LF)

        # # конвертируем объекты в mesh
        # LF.convert_curve_to_mesh(self.LF)

        # конвертируем объекты в mesh iter
        LF.iter_convert_curve_to_mesh(self.LF)

        # создаём коллекции в blender scene
        LF.create_collection_in_blend_scene(self.LF)

        # рассортировать объекты по сценам в зависимости от названия объекта
        LF.sort_all_obj_by_collections(self.LF)

        # удаляем пустые коллекции из сцены
        LF.del_empty_collections(self.LF)

        # перемещаем объекты по Z если есть необходимость
        LF.move_by_z(self.LF)

        # убираем сглаживание углов
        LF.make_shade_flat(self.LF)

        # устанавливаем нормальное отображение в сцене
        LF.set_normal_view_in_scene(self.LF)

        # Скроем сущпольные коллекции в сцене
        LF.vwport_hide(self.LF)

        # удаляем объекты mesh чьи имена начинаются с Collect
        LF.del_cub_mesh_coll(self.LF)

        # # откроем все коллекции в сцене
        # LF.vwport_show_all(self.LF)

        ######################################  MATERIALS   ########################################
        self.AF = AF()                                                      # инициализируем класс

        # добавляем материалы из файла blend
        AF.append_mat_from_file()

        # назначаем материалы объектам
        AF.ass_mat(self.AF)

        ######################################  CAMERASUN   ########################################
        self.CF = CF()                                                      # инициализируем класс

        self.CF = CF.run_camsun(self.CF)                                    # запустили основную процедуру

        ############################################################################################
        bpy.ops.wm.save_as_mainfile(
            filepath=r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\scen_tmp\tester999.blend")

        ############################################################################################
        ###########################  ПОВТОРНЫЙ ЗАПУСК ПО НОВОЙ ГРАНИЦЕ   ###########################
        print(len([r.name for r in bpy.data.curves]))
        print(len([r.name for r in bpy.data.objects]))
        print(len([r.name for r in bpy.data.meshes]))
        print(len([r.name for r in bpy.data.collections]))
        print(len([x.name for x in bpy.context.selected_objects]))
        print(len([x.name for x in bpy.context.view_layer.objects]))


        # УДАЛИЛИ 5 curve и 5 objects
        i = 0
        for x in bpy.data.collections['1_LD_BUILD'].objects:
            if i < 5:
                crv = bpy.data.curves.get(x.name[:-4])
                bpy.data.curves.remove(crv)
                bpy.data.objects.remove(x)
                i += 1
        print("#" * 50)
        print(len([r.name for r in bpy.data.curves]))
        print(len([r.name for r in bpy.data.objects]))
        print(len([r.name for r in bpy.data.meshes]))
        print(len([r.name for r in bpy.data.collections]))
        print(len([x.name for x in bpy.context.selected_objects]))
        print(len([x.name for x in bpy.context.view_layer.objects]))


        self.LF = LF()  # инициализируем класс

        # берем путь из панели bpy
        self.LF.path_to_GPKG = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg"

        # открываем gdal-ом gpkg по пути
        self.LF.ds = LF.open_file_by_gdal(self.LF)

        # берем название значения объекта для фильта wkt, значение из семантики
        self.LF.name_granica = "2"

        # получаем словарь datasource отфильтрованный по граничке обрезки (wkt)
        self.LF.dict_ds = LF.get_dict_from_ds(self.LF)

        # переросим словарь с отдельными ds по слоям - в память пк
        self.LF.dict_ds_mem = LF.save_dict_of_lrs_to_mem(self.LF)

        # объединяем словарь с несколькими DataSources в один DataSource в памяти ПК
        self.LF.ds_mem = LF.save_Dict_With_Ds_To_Mem(self.LF)

        # перегоняем DataSource в DataFrame
        self.LF.dict_df = LF.lr_to_dataframe(self.LF)

        # словарь pandas Dataframe -> словарь GeoPandas GeoDataFrame
        self.LF.dict_gdf = LF.pandas_to_geopandas(self.LF)

        # путь к временному каталогу - берем из панели bpy
        self.LF.tmp_path_fldr = r"C:\Users\dolgushin_an\Desktop\\"

        # создали временный каталог для сохранения результатов svg файлов
        self.LF.tmp_path_fldr = LF.create_tmp_folder_by_path(self.LF)

        # експорт каждого gdf из словаря в *.svg
        LF.export_gdf_to_svg(self.LF)

        # получаем список всех путей и названий файлов во временном каталоге по расширению '*.svg'
        self.LF.svg_path_names = LF.get_path_names_files_by_exten(self.LF.tmp_path_fldr, extension=".svg")

        # # импортируем svg в сцену
        # LF.import_svg_to_scen(self.LF)

        # импортируем svg в сцену
        LF.iter_import_svg_to_scen(self.LF)

        # удаляем временный каталог
        LF.del_tmp_folder(self.LF)

        # # extrude всех curve
        # LF.extrude_curves_in_data(self.LF)

        # extrude всех curve
        LF.iter_extrude_curves_in_data(self.LF)

        # # конвертируем объекты в mesh
        # LF.convert_curve_to_mesh(self.LF)

        # конвертируем объекты в mesh iter
        LF.iter_convert_curve_to_mesh(self.LF)

        # создаём коллекции в blender scene
        LF.create_collection_in_blend_scene(self.LF)

        # рассортировать объекты по сценам в зависимости от названия объекта
        LF.sort_all_obj_by_collections(self.LF)

        # удаляем пустые коллекции из сцены
        LF.del_empty_collections(self.LF)

        # перемещаем объекты по Z если есть необходимость
        LF.move_by_z(self.LF)

        # убираем сглаживание углов
        LF.make_shade_flat(self.LF)

        # устанавливаем нормальное отображение в сцене
        LF.set_normal_view_in_scene(self.LF)

        # Скроем сущпольные коллекции в сцене
        LF.vwport_hide(self.LF)

        # удаляем объекты mesh чьи имена начинаются с Collect
        LF.del_cub_mesh_coll(self.LF)

        # # откроем все коллекции в сцене
        # LF.vwport_show_all(self.LF)

        ######################################  MATERIALS   ########################################
        self.AF = AF()                                                      # инициализируем класс

        # добавляем материалы из файла blend
        AF.append_mat_from_file()

        # назначаем материалы объектам
        AF.ass_mat(self.AF)


        bpy.ops.wm.save_as_mainfile(
            filepath=r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\scen_tmp\tester777.blend")

        #  ------------------------------------------------------------------------------------------------
        print("---  %s END ALL ---" % (time.time() - start_time))
        #  ------------------------------------------------------------------------------------------------



        self.LF.run_lucky()

    # # УДОБНАЯ ИНФОРМАЦИЯ ЧЕРЕЗ ГЕНЕРАТОРЫ
    # crvs_name = [r.name for r in bpy.data.curves]
    # objcts_name = [r.name for r in bpy.data.objects]
    # meshs_name = [r.name for r in bpy.data.meshes]
    # colls_name = [r.name for r in bpy.data.collections]
    # selected_name = [x.name for x in bpy.context.selected_objects]
    # view_objcts = [x.name for x in bpy.context.view_layer.objects]
    #
    # print(len([r.name for r in bpy.data.curves]))
    # print(len([r.name for r in bpy.data.objects]))
    # print(len([r.name for r in bpy.data.meshes]))
    # print(len([r.name for r in bpy.data.collections]))
    # print(len([x.name for x in bpy.context.selected_objects]))
    # print(len([x.name for x in bpy.context.view_layer.objects]))





if __name__ == "__main__":
    tst = Toster()
    print("stop")
