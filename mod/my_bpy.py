import typing
from typing import Iterator, Tuple, List, Union
import numpy as np
import os
import pathlib
import glob
from concurrent.futures import ThreadPoolExecutor
import os

import bpy
from bpy import *
from bpy import context as cntx
from bpy.types import Mesh as bpyMesh
from bpy.types import Object as bpyObject
import bmesh

def flip_normal(name_mes: str) -> None:
    bm = bmesh.new()
    meshobjs = [o for o in bpy.data.meshes if o.name == name_mes]
    for ob in meshobjs:
        me = ob
        bpy.context.view_layer.objects.active = bpy.data.objects[me.name]  # активировали объект
        bpy.ops.object.mode_set(mode='EDIT')  # перевели в режим Edit
        bm = bmesh.from_edit_mesh(me)  # load bmesh
        for f in bm.faces:
            f.normal_flip()
        bm.normal_update()
        if bm.is_wrapped:
            bmesh.update_edit_mesh(me, False, False)
        else:
            bm.to_mesh(me)
            me.update()
        # bm.to_mesh(me)
        # bmesh.update_edit_mesh(me, False, False)
        # me.update()
        # bm.clear()
        bpy.ops.object.mode_set(mode='OBJECT')

def create_mesh(name_mesh: str, verts: np.ndarray, faces: List[List[int]]) -> bpyMesh:
    """     создаем mesh объект
    name_mesh       -  название mesha
    verts           -  numpy массив (список точек с координатами)
    faces           -  список точек для каждого face отдельно по списку
    """
    mesh = bpy.data.meshes.new(name=name_mesh)
    mesh.from_pydata(verts, [], faces)
    return mesh

def add_mesh_to_scene_and_get_active(mesh: bpyMesh, col: str = "Collection") -> bpyObject:
    """     добавляем mesh в сцену (коллекцию, слой) и возвращаем объект
    mesh        -  сам объект меша скидываем
    col         -  название колекции, поумолчанию "Collection"
    """
    obj = bpy.data.objects.new(mesh.name, mesh)
    col = bpy.data.collections.get(col)
    col.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    return obj

def activate_mesh_by_name(name_mesh: str) -> bool:
    """     активируем объект (mesh) по названию объекта
    name_mesh       -  название объекта
    """
    bpy.ops.object.select_all(action='DESELECT')
    ob = bpy.context.scene.objects[name_mesh]  # получаем объект
    ob.select_set(True)  # выделяем объект
    bpy.context.view_layer.objects.active = bpy.data.objects[name_mesh]  # делаем объект активным
    result = bpy.context.view_layer.objects.active.name == name_mesh
    return result

def delite_mesh_by_name(name_mesh: str) -> None:
    """     удаляем объект mesh из сцены по названию
    name_mesh       -  название объекта
    """
    [bpy.data.meshes.remove(m) for m in bpy.data.meshes if m.name == name_mesh]
    return None

def export_active_obj_to_stl(name_mesh: str, path_to_dir: str) -> None:
    """     активируем mesh по имени и экспортируем в каталог
    name_mesh       -  название mesh
    path_to_dir     -  каталог куда сохраняем объект
    """
    bpy.ops.object.select_all(action='DESELECT')
    ob = bpy.context.scene.objects[name_mesh]  # получаем объект
    ob.select_set(True)  # выделяем объект
    bpy.context.view_layer.objects.active = bpy.data.objects[name_mesh]  # делаем объект активным
    stl_path = path_to_dir + r'/' + name_mesh + '.stl'
    bpy.ops.export_mesh.stl(filepath=stl_path, use_selection=True, ascii=True)
    return None

def delite_mesh_from_mesh(name_base_mesh: str, name_hole_mesh: str) -> bpyMesh:
    """ удаляем mesh из mesh и получаем итоговый mesh
    name_base_mesh      -  имя базового Mesh, из которго вычитаем
    name_hole_mesh      -  имя Mesh, который вычитаем из базисного Mesh
    """
    bpy.ops.object.select_all(action='DESELECT')            # снять выделение со всех объектов
    ob = bpy.context.scene.objects[name_base_mesh]          # получаем верхний, больший объект
    ob.select_set(True)                                     # выделяем объект
    bpy.context.view_layer.objects.active = bpy.data.objects[name_base_mesh]  # делаем объект активным

    mod_name = 'my_bool_mod'
    cur_mod = ob.modifiers.new(mod_name, 'BOOLEAN')         # добавили можификатор
    cur_mod.operation = 'DIFFERENCE'                        # выбрали операцию булевую вычитание
    cur_mod.object = bpy.data.objects[name_hole_mesh]       # выбрали объект который вычетаем
    bpy.ops.object.modifier_apply(modifier=mod_name)
#    bpy.ops.mesh.beautify_fill()
    print('asdf')


    # ob = bpy.context.scene.objects[name_base_mesh]
    # ob.select_set(True)
    # bpy.ops.object.mode_set(mode='OBJECT')
    # vot = bpy.context.active_object   # получили активный объект в переменную
    # bpy.ops.object.modifier_apply(modifier=mod_name)        # применяем модификаторы
    #
    # bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    # ob = bpy.context.scene.objects[name_base_mesh]  # получаем верхний, больший объект
    # ob.select_set(True)  # выделяем объект
    # bpy.context.view_layer.objects.active = bpy.data.objects[name_base_mesh]  # делаем объект активным

    [bpy.data.meshes.remove(m) for m in bpy.data.meshes if m.name == name_hole_mesh]
    # вся сцена
    # sc = bpy.data.objects.items()

    # bpy.ops.object.select_all(action='DESELECT')
    # ob = bpy.context.scene.objects[name_base_mesh]  # получаем объект
    # ob_hole = bpy.context.scene.objects[name_hole_mesh]
    # ob.select_set(True)  # выделяем объект
    # bpy.context.view_layer.objects.active = bpy.data.objects[name_base_mesh]  # делаем объект активным
    #
    # cur_mod = ob.modifiers.new('my_bool_mod', 'BOOLEAN')  # добавили можификатор
    # cur_mod.operation = 'DIFFERENCE'  # выбрали операцию булевую вычитание
    # cur_mod.object = bpy.data.objects[name_hole_mesh]  # выбрали объект который вычетаем
    #
    # mod_name = 'my_bool_mod'
    # bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    # ob = bpy.context.scene.objects[name_base_mesh]  # получаем верхний, больший объект
    # ob.select_set(True)  # выделяем объект
    # bpy.context.view_layer.objects.active = bpy.data.objects[name_base_mesh]  # делаем объект активным
    # bpy.ops.object.modifier_apply(modifier=mod_name)  # применяем модификаторы

    # bpy.ops.object.modifier_add(type='BOOLEAN')  # добавляем модификатор
    # ob.modifiers[0].operation = 'DIFFERENCE'
    # ob.modifiers[0].object = ob_hole
    # bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Boolean')

    return ob

def recalculate_normals_outside(mesh: bpyMesh) -> None:
    """     пересчитывает нормали объекта
    mesh        -  сам объект меша скидываем
    """
    bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    ob = bpy.context.scene.objects[mesh.name]
    ob.select_set(True)  # выделяем объект
    bpy.context.view_layer.objects.active = bpy.data.objects[mesh.name]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    return None

def export_mesh_to_obj(rslt_path: str, msh: bpyMesh, f_name: str) -> None:
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

def export_mesh_to_stl(rslt_path: str, msh: bpyMesh, f_name: str) -> None:
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
    bpy.ops.export_mesh.stl(
        filepath=full_path,
        use_selection=True)
    bpy.ops.object.select_all(action='DESELECT')

def load_all_svg_from_folder(fldr_path: str) -> None:
    os.chdir(fldr_path)
    for files in glob.glob("*.svg"):
        print(files, "... imported!")
        bpy.ops.import_curve.svg(filepath=files)

        # deselect nothing, select all curves, join
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_by_type(type='CURVE')
        # bpy.context.scene.objects.active = bpy.data.objects["Curve"]
        bpy.context.view_layer.objects.active = bpy.data.objects["Curve"]
        for obj in bpy.context.scene.objects:
            if obj.name == "Curve":
                obj.name = files[:-4]
        bpy.ops.object.join()
        bpy.ops.object.convert(target='MESH')
        bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=f'{fldr_path}\scen_from_python.blend')
    # bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
    # tt = bpy.context.view_layer.objects.active  # получить активных объект

def create_obj_from_svg(f_name: str) -> bpyObject:
    bpy.ops.import_curve.svg(filepath=f_name)
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_by_type(type='CURVE')
    # bpy.context.scene.objects.active = bpy.data.objects["Curve"]
    bpy.context.view_layer.objects.active = bpy.data.objects["Curve"]
    for obj in bpy.context.scene.objects:
        if obj.name == "Curve":
            obj.name = f_name[:-4]
    bpy.ops.object.join()
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.select_all(action='DESELECT')

    # extrude code block
    x = f_name[:-4]
    r = x.split('_fid_')[0]
    h = float(r.split('_')[2])  # получаем высоту в метрах
    etazh = r.split('_')[1]  # получаем кол-во этажей
    mat = r.split('_')[0]  # получаем тип здания
    bpy.context.view_layer.objects.active = bpy.data.objects[x]  # активировали объект
    bpy.ops.object.mode_set(mode='EDIT')  # Toggle edit mode
    bpy.ops.mesh.select_mode(type='FACE')  # Change to face selection
    bpy.ops.mesh.select_all(action='SELECT')  # Select all faces
    obj = bpy.context.active_object
    bpy.ops.mesh.extrude_faces_move(
        MESH_OT_extrude_faces_indiv={"mirror": True},
        TRANSFORM_OT_shrink_fatten={"value": -h,
                                    "mirror": True,
                                    "proportional_edit_falloff": 'SMOOTH',
                                    "proportional_size": 1,
                                    "snap": False,
                                    "snap_target": 'CLOSEST',
                                    "snap_point": (0, 0, 0),
                                    "snap_align": False,
                                    "snap_normal": (0, 0, 0),
                                    "release_confirm": False})

    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
    print(f_name, "... imported!")
    return obj

def blend_file_from_svg(path_fldr: str) -> None:
    # тост
    os.chdir(path_fldr)
    all_files_svg = [x for x in glob.glob("*.svg")]
    with ThreadPoolExecutor(int(os.cpu_count()-2)) as executor:
        results = executor.map([create_obj_from_svg(x) for x in all_files_svg])

    # всю сцену сохраняем предварительно избавившись от лишней треангуляции
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.dissolve_limited()
    bpy.ops.object.editmode_toggle()
    bpy.ops.object.select_all(action='DESELECT')

    # # Создаем новые колекции для проектируемых объектов и сущпола !!!!
    # collection_list = ['LD_BUILD', 'LD_LAND', 'PODOSNOVA_BUILD', 'PODOSNOVA_LAND']
    # for i in collection_list:
    #     if i not in [x.name for x in bpy.context.blend_data.collections]:
    #         my_collection = bpy.context.blend_data.collections.new(name=i)
    #         bpy.context.collection.children.link(my_collection)
    #
    # # удаляем ненужные коллекции и все объекты из них
    # for collection in bpy.context.blend_data.collections:
    #     if collection.name not in collection_list:
    #         bpy.data.collections.remove(collection)  # удалили коллекции

    # устанавливаем нормльное отображение в окне blendera
    for a in bpy.context.screen.areas:
        if a.type == 'VIEW_3D':
            for s in a.spaces:
                if s.type == 'VIEW_3D':
                    s.clip_start = 1
                    s.clip_end = 900000

    bpy.ops.wm.save_as_mainfile(filepath=f'{path_fldr}\scen_from_python.blend')



# bpy.ops.wm.open_mainfile(filepath=bpy.data.filepath)
# tt = bpy.context.view_layer.objects.active  # получить активных объект


# bpy.ops.object.editmode_toggle()

# bpy.ops.export_scene.obj(
#     filepath=str(os.path.join(
#         scene.auto_obj_dir_out, files.replace(".svg", ".obj"))))
# bpy.ops.object.delete()



# for files in glob.glob("*.svg"):
#     print(files, "... imported!")
#     bpy.ops.import_curve.svg(filepath=files)
#
#     # deselect nothing, select all curves, join
#     bpy.ops.object.select_all(action='DESELECT')
#     bpy.ops.object.select_by_type(type='CURVE')
#     bpy.context.scene.objects.active = bpy.data.objects["Curve"]
#     for obj in bpy.context.scene.objects:
#         if obj.select: obj.name = "snail.000"
#     bpy.ops.object.join()
#     bpy.ops.object.convert(target='MESH')
#     bpy.ops.object.select_all(action='DESELECT')





# import bpy
# import os
#
# svg_files = [f for f in os.listdir('svgtest') if f.endswith('.svg')]
#
# for f in svg_files:
#     start_objs = bpy.data.objects[:]
#     bpy.ops.import_curve.svg(filepath=os.path.join('svgtest',f))
#     new_curves = [o for o in bpy.data.objects if o not in start_objs]
#
#     n = f[:-8] # the start of the filename
#     s = float(f[-6:-4]) # the scale factor as in the 99 from name_S99.svg
#     for obj in new_curves:
#         obj.name = n
#         obj.scale = (s,s,s)