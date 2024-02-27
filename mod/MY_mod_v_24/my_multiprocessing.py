import multiprocessing
from multiprocessing import Pool, Process, Queue, Pipe, Value, Array, Lock, TimeoutError
import sys

ORIG_SYS_PATH = list(sys.path)  # Make a new instance of sys.path

import bpy
# import bmesh

BPY_SYS_PATH = list(sys.path)  # Make instance of `bpy`'s modified sys.path

from typing import Iterator, Tuple, List, Union
import os
import time
import pathlib



def getPathAndNamesFilesInFolderByExtension(path_to_target_folder: str, extension: str):
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

def create_colection():
    # Создаем новые колекции для проектируемых объектов и сущпола !!!!
    collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']
    for i in collection_list:
        if i not in [x.name for x in bpy.context.blend_data.collections]:
            my_collection = bpy.context.blend_data.collections.new(name=i)
            bpy.context.collection.children.link(my_collection)

def import_svg_to_scen(f_path: str) -> List:
    # if f_name == 'TER_R_fid_1032.svg' or f_name == 'TER_R_fid_1032':
    #     print(f_name)
    sys.path = ORIG_SYS_PATH
    import os
    import bpy
    f_name = os.path.basename(f_path)[:-4]
    prefix = ("ROAD_S", "TER_R", "BUILD_S", "LD")                                   # начало у файлов (те которые не pr)
    build_list = ("ZH", "NZH", "PR", "OB")                                          # pr build
    land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

    bpy.ops.import_curve.svg(filepath=f_path)                                   # импорт svg по пути
    bpy.ops.object.select_all(action='DESELECT')                                # сняли выделение со всего

    # проверка, если добавляются сразу несколько объектов из одного svg
    objects = [x for x in bpy.data.objects if x.name.startswith("Curve")]  # выборка объектов по названию

    if len(objects) > 1:    # если объект в svg это коллекция
        print(f_name)
        [x.select_set(True) for x in objects]                       # выделяем объекты из списка объектов
        for ob in bpy.context.selected_objects:
            ob.name = f_name
        bpy.context.view_layer.objects.active = bpy.data.objects[f_name]    # активировали объект !!!!
        bpy.ops.object.join()   # объеденяем быборку объектов в один объект (В АКТИВНЫЙ ОБЪЕКТ ! с его name!!!!!)

    if len(objects) == 1:   # если это одиночный объкт (из svg)
        [x.select_set(True) for x in objects]                       # выделяем объекты из списка объектов
        for ob in bpy.context.selected_objects:
            ob.name = f_name

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
    bpy.context.view_layer.objects.active = bpy.data.objects[f_name]  # активировали объект
    print('asfd')
    obj = bpy.data.objects.get(f_name)
    return obj

def export_mesh_to_obj(rslt_path: str, msh, f_name: str) -> None:
    """     экспортируем mesh в *.obj формат
    rslt_path       -  путь, куда сохранять объект
    mesh            -  сам объект меша скидываем
    f_name          -  название объекта
    """
    if f_name == "" and rslt_path == "":
        f_name = "file_from_py.obj"
        full_path = os.path.join(pathlib.Path().resolve(), f_name)
    elif f_name != "" and rslt_path != "":
        full_path = os.path.join(rslt_path, f_name)
    elif rslt_path == "":
        full_path = os.path.join(pathlib.Path().resolve(), f_name)
    elif f_name == "":
        full_path = os.path.join(rslt_path, f_name)

    bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    ob = bpy.context.scene.objects[msh.name]
    ob.select_set(True)  # выделяем объект
    bpy.context.view_layer.objects.active = bpy.data.objects[msh.name]
    bpy.ops.export_scene.obj(
        filepath=full_path,
        check_existing=True,
        axis_forward='-Z',
        axis_up='Y',
        filter_glob="*.obj;*.mtl",
        use_selection=True,
        use_animation=False,
        use_mesh_modifiers=True,
        use_edges=True,
        use_smooth_groups=False,
        use_smooth_groups_bitflags=False,
        use_normals=True,
        use_uvs=False,
        use_materials=False,
        use_triangles=False,
        use_nurbs=False,
        use_vertex_groups=False,
        use_blen_objects=False,
        group_by_object=False,
        group_by_material=False,
        keep_vertex_order=False,
        global_scale=1,
        path_mode='AUTO')
    bpy.ops.object.select_all(action='DESELECT')


def tost_func(f_path: str):
    # if f_name == 'TER_R_fid_1032.svg' or f_name == 'TER_R_fid_1032':
    #     print(f_name)
    sys.path = ORIG_SYS_PATH
    import os
    import bpy
    from bpy import context
    import pathlib
    f_name = os.path.basename(f_path)[:-4]
    prefix = ("ROAD_S", "TER_R", "BUILD_S", "LD")                                   # начало у файлов (те которые не pr)
    build_list = ("ZH", "NZH", "PR", "OB")                                          # pr build
    land_list = ("SP", "DE", "ZE", "DO", "TR", "VP", "HP", "PP", "VD", "VS", "OV")  # pr land

    bpy.ops.import_curve.svg(filepath=f_path)                                   # импорт svg по пути
    bpy.ops.object.select_all(action='DESELECT')                                # сняли выделение со всего
    # obj = bpy.data.objects.get(f_name)

    # проверка, если добавляются сразу несколько объектов из одного svg
    objects = [x for x in bpy.data.objects if x.name.startswith("Curve")]  # выборка объектов по названию

    if len(objects) > 1:  # если объект в svg это коллекция
        print(f_name)
        [x.select_set(True) for x in objects]  # выделяем объекты из списка объектов
        for ob in bpy.context.selected_objects:
            ob.name = f_name
        bpy.context.view_layer.objects.active = bpy.data.objects[f_name]  # активировали объект !!!!
        bpy.ops.object.join()  # объеденяем быборку объектов в один объект (В АКТИВНЫЙ ОБЪЕКТ ! с его name!!!!!)

    if len(objects) == 1:  # если это одиночный объкт (из svg)
        [x.select_set(True) for x in objects]  # выделяем объекты из списка объектов
        for ob in bpy.context.selected_objects:
            ob.name = f_name

    for obj in bpy.context.selected_objects:
        bpy.context.view_layer.objects.active = bpy.data.objects[obj.name]  # активировали объект
        bpy.ops.object.convert(target='MESH')


    # блок экструд
    bpy.ops.object.select_all(action='DESELECT')
    objects = [x for x in bpy.data.objects if x.name.startswith(f_name)]
    for x in objects:
        view_layer = bpy.context.view_layer
        view_layer.active_layer_collection.collection.objects.link(x)
    [x.select_set(True) for x in objects]
    if not f_name.startswith(prefix):
        x = f_name
        r = x.split('_fid_')[0]
        h = float(r.split('_')[2])  # получаем высоту в метрах
        obj = bpy.data.objects.get(f_name)  # объект в переменную
        # obj.users_collection  # в какой коллекции объект
        obj.select_set(True)  # выделили объект
        bpy.context.view_layer.objects.active = bpy.data.objects[f_name]  # активировали объект
        bpy.ops.object.mode_set(mode='EDIT')  # Toggle edit mode
        bpy.ops.mesh.select_mode(type='FACE')  # Change to face selection
        bpy.ops.mesh.select_all(action='SELECT')  # Select all faces
        # obj = bpy.context.active_object
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


    try:
        if context.object.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
    except Exception as e:
        print(e)

    # selection_names = bpy.context.selected_objects  # выделенные объекты, список имен
    tt = bpy.context.view_layer.objects.active      # акктивный объект на видимом слое

    if bpy.context.object.type == 'MESH':
        bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
        ob = bpy.context.scene.objects[f_name]  # получаем верхний, больший объект
        ob.select_set(True)  # выделяем объект
        bpy.context.view_layer.objects.active = bpy.data.objects[ob.name]  # делаем объект активным

        o = bpy.context.active_object  # получаем активный объект в переменную
        verts = [tuple(o.matrix_world @ v.co.xyz) for v in o.data.vertices]  # получаем координаты в формате XYZ
        faces = [[vert for vert in polygon.vertices] for polygon in o.data.polygons]  # получаем списки путей полигонов
        edgs = [list(x.vertices) for x in o.data.edges]

        # СОЗДАНИЕ ОБЪЕКТА ПО КООРДИНАТАМ !!!!!!!!!!
        # mymesh = bpy.data.meshes.new('my_m')
        # mymesh.from_pydata(verts, edgs, faces)
        # myobject = bpy.data.objects.new('new_obj_new', mymesh)
        # bpy.data.collections['Collection'].objects.link(myobject)


        # bpy.context.active_object.mode  # какой режим сейчас у активного объекта
        # bpy.ops.object.mode_set(mode='EDIT')
        # bpy.ops.object.mode_set(mode='OBJECT')
        # bpy.ops.object.editmode_toggle()
        # bpy.context.tool_settings.mesh_select_mode = (False, False, True)
        #
        # dt = bpy.context.object.data  # получаем активный объект
        # bm = bmesh.from_edit_mesh(dt)
        # # dt = bpy.data.meshes.get(f_name)
        # verts = [tuple(o.matrix_world @ v.co.xyz) for v in o.data.vertices]  # получаем координаты в формате XYZ
        # faces = [[vert for vert in polygon.vertices] for polygon in o.data.polygons]  # получаем списки путей полигонов
        #
        # vrts = [list(x.co) for x in dt.vertices]
        # edgs = [list(x.vertices) for x in dt.edges]
        # # list_polygons = [x for x in dt.polygons]
        # # list_faces = [x.edge_keys.index(i) for i, x in enumerate(list_polygons)]
        # faces_out = []
        # verts_out = [vert.co[:] for vert in bm.verts]
        # _ = [faces_out.append([v.index for v in face.verts]) for face in bm.faces]
        #
        #
        #
        #
        # mymesh = bpy.data.meshes.new('my_m')
        # mymesh.from_pydata(vrts, [], faces_out)
        # myobject = bpy.data.objects.new('new_obj', mymesh)
        # bpy.data.collections['Collection'].objects.link(myobject)
        # mymesh.from_pydata(vrts, [], faces_out)
        # mymesh.update(calc_edges=True)

    print('asdf')


    # # блок экспорта в obj формат
    # rslt_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\obj"
    # if f_name == "" and rslt_path == "":
    #     f_name = "file_from_py.obj"
    #     full_path = os.path.join(pathlib.Path().resolve(), f_name)
    # elif f_name != "" and rslt_path != "":
    #     full_path = os.path.join(rslt_path, f_name+'.obj')
    # elif rslt_path == "":
    #     full_path = os.path.join(pathlib.Path().resolve(), f_name)
    # elif f_name == "":
    #     full_path = os.path.join(rslt_path, f_name)
    #
    # # try:
    # #     if context.object.mode == 'EDIT':
    # #         bpy.ops.object.mode_set(mode='OBJECT')
    # # except Exception as e:
    # #     print(e)
    #
    #
    # bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    # objects = [x for x in bpy.data.objects if x.name.startswith(f_name)]
    # # for x in objects:
    # #     view_layer = bpy.context.view_layer
    # #     view_layer.active_layer_collection.collection.objects.link(x)
    # [x.select_set(True) for x in objects]
    # # ob = bpy.data.objects.get[f_name]
    # # ob = bpy.context.scene.objects[msh.name]
    # # ob.select_set(True)  # выделяем объект
    # bpy.context.view_layer.objects.active = bpy.data.objects[f_name]
    # bpy.ops.export_scene.obj(
    #     filepath=full_path,
    #     check_existing=True,
    #     axis_forward='-Z',
    #     axis_up='Y',
    #     filter_glob="*.obj;*.mtl",
    #     use_selection=True,
    #     use_animation=False,
    #     use_mesh_modifiers=True,
    #     use_edges=True,
    #     use_smooth_groups=False,
    #     use_smooth_groups_bitflags=False,
    #     use_normals=True,
    #     use_uvs=False,
    #     use_materials=False,
    #     use_triangles=False,
    #     use_nurbs=False,
    #     use_vertex_groups=False,
    #     use_blen_objects=False,
    #     group_by_object=False,
    #     group_by_material=False,
    #     keep_vertex_order=False,
    #     global_scale=1,
    #     path_mode='AUTO')
    # bpy.ops.object.select_all(action='DESELECT')
    return {f_name: [verts, edgs, faces]}

if __name__ == '__main__':
    #  ------------------------------------------------------------------------------------------------
    start_luck = time.time()
    print("             ---  старт lucky ---")
    #  ------------------------------------------------------------------------------------------------

    # создали коллекции
    create_colection()

    # импорт svg в сцену
    p_file = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\!_bunch_svg_3t"
    # p_file = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\!_bunch_svg_13t"
    list_data = getPathAndNamesFilesInFolderByExtension(p_file, '.svg')
    # # for val_path, val_name in zip(list_data[0], list_data[1]):
    # vot = []
    # for x in list_data[0]:
    #     vot.append(tost_func(x))

    # процессов сколько веток запустим
    pr = len(list_data[0])//500
    pr = pr if pr < 30 else 30
    pr = 16 if pr < 16 else pr

    # ЭТО РАБОТАЕТ !!!!!!!!!!! НЕ УДАЛЯТЬ !!!!!!!!!!!!!
    sys.path = ORIG_SYS_PATH
    with Pool(4) as p:
        vot = (p.map(tost_func, list_data[0]))
        sys.path = BPY_SYS_PATH
        p.close()


    # sys.path = ORIG_SYS_PATH
    # vot = []
    # with Pool(4) as p:
    #     # for i in p.imap_unordered(tost_func, list_data[0], chunksize=500):
    #     # parent_conn, list_data[0] = Pipe()
    #     for i in p.imap_unordered(tost_func, list_data[0]):
    #         vot.append(i)
    #     sys.path = BPY_SYS_PATH
    #     p.close()


    # bpy.ops.wm.save_as_mainfile(filepath=r"C:\!_Python\_500_new_format\!!!!_MRGP_plugin\scen_tmp\from_python.blend")

    #  ------------------------------------------------------------------------------------------------
    print(f"  ---  все выполнение lucky заняло {(time.time() - start_luck)} seconds ---")
    #  ------------------------------------------------------------------------------------------------

    print(f'объектов в списке {len(vot)} \n {vot[5]}')
