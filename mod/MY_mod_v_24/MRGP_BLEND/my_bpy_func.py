# -*- coding: utf-8 -*-
from typing import Iterator, Tuple, List, Union
import numpy as np
import pathlib
import glob
from concurrent.futures import ThreadPoolExecutor
import os

from bpy import *
from bpy import context
from bpy.types import Mesh as bpyMesh
from bpy.types import Object as bpyObject
import bmesh


class FunctionsForBlender:


    @staticmethod
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

    @staticmethod
    def create_mesh(name_mesh: str, verts: np.ndarray, faces: List[List[int]]) -> bpyMesh:
        """     создаем mesh объект
        name_mesh       -  название mesha
        verts           -  numpy массив (список точек с координатами)
        faces           -  список точек для каждого face отдельно по списку
        """
        mesh = bpy.data.meshes.new(name=name_mesh)
        mesh.from_pydata(verts, [], faces)
        return mesh

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def delite_mesh_by_name(name_mesh: str) -> None:
        """     удаляем объект mesh из сцены по названию
        name_mesh       -  название объекта
        """
        [bpy.data.meshes.remove(m) for m in bpy.data.meshes if m.name == name_mesh]
        return None

    @staticmethod
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

    @staticmethod
    def delite_mesh_from_mesh(name_base_mesh: str, name_hole_mesh: str) -> bpyMesh:
        """ удаляем mesh из mesh и получаем итоговый mesh
        name_base_mesh      -  имя базового Mesh, из которго вычитаем
        name_hole_mesh      -  имя Mesh, который вычитаем из базисного Mesh
        """
        bpy.ops.object.select_all(action='DESELECT')  # снять выделение со всех объектов
        ob = bpy.context.scene.objects[name_base_mesh]  # получаем верхний, больший объект
        ob.select_set(True)  # выделяем объект
        bpy.context.view_layer.objects.active = bpy.data.objects[name_base_mesh]  # делаем объект активным

        mod_name = 'my_bool_mod'
        cur_mod = ob.modifiers.new(mod_name, 'BOOLEAN')  # добавили можификатор
        cur_mod.operation = 'DIFFERENCE'  # выбрали операцию булевую вычитание
        cur_mod.object = bpy.data.objects[name_hole_mesh]  # выбрали объект который вычетаем
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def blend_file_from_svg(path_fldr: str) -> None:
        # тост
        os.chdir(path_fldr)
        all_files_svg = [x for x in glob.glob("*.svg")]
        with ThreadPoolExecutor(int(os.cpu_count() - 2)) as executor:
            results = executor.map([FunctionsForBlender.create_obj_from_svg(x) for x in all_files_svg])

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

    @staticmethod
    def get_coord_obj(ob):
        object = bpy.data.objects.get(ob.name)
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
        v_global = bpy.context.object.location
        return v_global

    @staticmethod
    def ShowMessageBox(message="TEXT", title="Message Box", icon='INFO'):
        def draw(self, context):
            self.layout.label(text=message)

        bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

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
    def new_dimension_LD_TR(context):
        # выделяем все объекты из двух коллекций
        collection_list = ['5_tr', '6_ld']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)

        # получаем все выделенные объекты в переменную
        sel_objs = [ob for ob in bpy.context.selected_objects]

        # устанавливаем размерность 3d выделенным объектам из двух коллекций
        try:
            for x in sel_objs:
                x.data.dimensions = '3D'
        except:
            pass

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def new_style_obj_bevel_ass_mat(context):
        # выделяем все объекты коллекции 5_tr
        try:
            for obj in bpy.data.collections['5_tr'].all_objects:
                obj.select_set(True)
                obj.data.bevel_depth = 1.5  # задали толщину граничке
                mat = bpy.data.materials.get("TR_GRAN")  # взяли материал из библиотеке
                if bpy.data.materials:  # назначили материалы выбранным объектам
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
                obj.select_set(True)
                obj.data.bevel_depth = 2  # задали толщину граничке

                mat = bpy.data.materials.get("LD_GRAN")  # взяли материал из библиотеке
                if bpy.data.materials:  # назначили материалы выбранным объектам
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)
        except:
            pass

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')

    @staticmethod
    def new_style_obj_smoth_link(context):
        # выделяем все объекты из двух коллекций
        collection_list = ['5_tr', '6_ld']
        for col in collection_list:
            for obj in bpy.data.collections[col].all_objects:
                obj.select_set(True)
                bpy.ops.object.make_links_scene(scene='S_2')

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

    @staticmethod
    def new_style_cam_sun_link(context):

        # создаём ссылки на новую сцену для камер и солнца
        name_for_link = ['00_SUN', '01_North', '02_South', '03_East', '04_West']
        obj_s = [x for x in bpy.data.objects if x.name in name_for_link]
        for ob in obj_s:
            ob.select_set(True)
            bpy.ops.object.make_links_scene(scene='S_2')
            ob.select_set(False)
            # ob.make_links_scene(scene='S_2')

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
            return 0
        return len(mtl)

    @staticmethod
    def get_path_to_tmp_folder():
        # путь к временному каталогу
        path_to_tmp = (bpy.context.scene.my_tool.my_string_tmp.replace('"', ''))
        # path_to_GPKG = ((r'C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg').replace('"', ''))
        path_to_tmp = ((path_to_tmp).replace('"', ''))
        return path_to_tmp

    @staticmethod
    def create_new_collection(lst_names: list = ""):
        # Создаем новые колекции для проектируемых объектов и сущпола !!!!
        collection_list = ['1_LD_BUILD', '2_LD_LAND', '3_Build_S', '4_Road_S', '5_tr', '6_ld']
        if lst_names == "":
            lst_names = collection_list

        for i in lst_names:
            if i not in [x.name for x in bpy.context.blend_data.collections]:
                my_collection = bpy.context.blend_data.collections.new(name=i)
                bpy.context.collection.children.link(my_collection)

    @staticmethod
    def del_empty_collections():
        # удаляем ненужные пустые коллекции
        for col in bpy.context.blend_data.collections:
            if len(col.objects.keys()) == 0:
                bpy.data.collections.remove(col)  # удалили коллекции

    @staticmethod
    def add_collections_to_scene():
        # добавляем все коллекции в сцену
        try:
            for coll in bpy.context.blend_data.collections:
                bpy.context.scene.collection.children.link(coll)
        except Exception as e:
            print(f'ERR {e} Коллекция уже сущствует!  {coll.name}')

    @staticmethod
    def set_view_param():
        # устанавливаем нормльное отображение в окне blendera
        for a in bpy.context.screen.areas:
            if a.type == 'VIEW_3D':
                for s in a.spaces:
                    if s.type == 'VIEW_3D':
                        s.clip_start = 1
                        s.clip_end = 900000




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
