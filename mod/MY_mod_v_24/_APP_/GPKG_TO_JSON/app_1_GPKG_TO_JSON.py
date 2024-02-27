from mod.my_gdal import GdalFunc as GF
from mod.my_pd_gpd import Func_GeoPandas_Pandas as GpdF
from mod.my_text import TextFunc as TF
import os

# главная функция
def main_function(path, fltr_lr, filtr_column, fltr_val, column_name_for_file, path_to_result):

    # открываем и перепроецируем GPKG
    gdf = GpdF.reprojection_apu_wgs(path, fltr_lr)

    # отфильтровали GeoDataFrame
    fltr_gdf = GpdF.gdf_filter_by_column_val(gdf, filtr_column, fltr_val)

    # добавляем новую уникальную колонку в gdf и получаем ее название
    fltr_gdf, add_col_name = GpdF.add_new_unic_column(fltr_gdf, "indx_col")

    # заполняем созданную колонку значениями из колонки индексации
    fltr_gdf = GpdF.add_val_to_col_from_col_with_index(fltr_gdf, add_col_name)

    # получаем список из gdf по каждому индексу из общего фрэйма
    dict_gdf = GpdF.split_gdf_by_unic_val_colum(fltr_gdf, add_col_name)

    # получаем словарь названий для файлов
    # list_names_to_check_unic = fltr_gdf[column_name_for_file].to_list()
    # dict_names = fltr_gdf[column_name_for_file].to_dict()
    dict_names = {x: y for x, y in fltr_gdf[column_name_for_file].to_dict().items()}
    unic_names = set([x for y, x in fltr_gdf[column_name_for_file].to_dict().items()])

    # получаем транслитеризованные названия для файлов
    dict_trans_names = TF.translitezator(unic_names)

    # # сохраняем все файлы в geojson
    for y, x in dict_trans_names.items():
        gdf_exp = fltr_gdf.loc[fltr_gdf[column_name_for_file] == y]
        gdf_exp.iloc[:, :-1].to_file(f"{os.path.join(path_to_result, x)}.geojson", driver="GeoJSON")

        # dict_gdf[y].iloc[:, :-1].to_file(f"{dict_trans_names[y]}.geojson", driver="GeoJSON")



if __name__ == '__main__':
    #  !!!!!!!!!  МЕНЯЕМ ПУТЬ К GPKG
    path_to_folder = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\GP.gpkg"

    #  - путь к папке для результатов
    path_to_result = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\__APP\geoj"

    #  - название слоя
    ftr_layer = r"GP_2021_line"

    #  - колонка для фильтра
    filtr_column = r"PRIM"

    #  - значение в колонке для фильтрации
    filtr_val = r"json"

    #  - откуда брать названия для названий файлов
    column_name_for_file = r"name"

    main_function(path_to_folder, ftr_layer, filtr_column, filtr_val, column_name_for_file, path_to_result)

    print("done")

