# -*- coding: utf-8 -*-
import math

import bpy

from my_bpy_func import FunctionsForBlender as fb


class CamSun:
    bl_label = 'CAM_Function'
    bl_idname = 'cam.cam_op'

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
        bpy.data.cameras[name_cam].clip_start = 1
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

    @staticmethod
    def cam_sun(context):
        cl = CamSun  # назначаем класс переменной (объекту)

        # удаляем все камеры
        [cl.del_cam(cl.get_cam(x)) for x in bpy.data.objects if x.type == 'CAMERA']

        # удаляем все SUN из сцены
        [cl.del_sun(cl.get_sun(x)) for x in bpy.data.lights if x.type == 'SUN']

        # получаем координаты выбранного пользователем объекта (активного)
        ob = bpy.context.active_object  # получили в переменную активный объект
        coord_cur_obj = fb.get_coord_obj(ob)  # получили координаты активного объекта

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
        bpy.data.scenes["S_1"].render.film_transparent = True
        bpy.data.scenes["S_1"].cycles.progressive = 'PATH'
        bpy.data.scenes["S_1"].cycles.samples = 256
        bpy.data.scenes["S_1"].cycles.preview_samples = 128
        bpy.context.scene.render.resolution_x = 3680
        bpy.context.scene.render.resolution_y = 2600

        # снимаем выделение со всех объектов сцены
        bpy.ops.object.select_all(action='DESELECT')