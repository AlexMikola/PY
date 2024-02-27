# -*- coding: utf-8 -*-
import bpy
import time

class MatFunc:
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

    @staticmethod
    def del_all_svg_mat(context):
        [bpy.data.materials.remove(x) for x in bpy.data.materials if x.name.startswith('SVGMat')]

    @staticmethod
    def del_mat_from_selection_objects(context):
        for obj in bpy.context.selected_editable_objects:
            obj.active_material_index = 0
            for i in range(len(obj.material_slots)):
                bpy.ops.object.material_slot_remove({'object': obj})

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

        cl = MatFunc  # # инициируем переменную для класса

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
