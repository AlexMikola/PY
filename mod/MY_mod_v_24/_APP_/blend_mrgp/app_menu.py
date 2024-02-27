# -*- coding: utf-8 -*-
bl_info = {
    "name": "MRGP",
    "description": "Various tools",
    "author": "AD",
    'license': 'GPL',
    'deps': '',
    "version": (8, 0, 1),
    "blender": (2, 80, 0),
    "location": "3D View > Tools",
    'warning': 'development version',
    "wiki_url": "",
    'tracker_url': "",
    'link': '',
    'support': 'COMMUNITY',
    "category": "3D View"
}
# ------------------------------------------------------------------------
#    IMPORTS
# ------------------------------------------------------------------------
import bpy
import sys
from pathlib import Path

# импортируем пути к своим модулям
ORIG_SYS_PATH = list(sys.path)
MOD_PATH = r"C:\blender_3_alpha_25_10_21\default_mrgp"            # путь к функциям данного модуля
if MOD_PATH not in ORIG_SYS_PATH:
    sys.path.insert(1, MOD_PATH)
    MOD_SYS_PATH = list(sys.path)

# from app_0_mains import Luck as MF
# import app_0_mains as MF
from app_0_mains import LUCK as LF
from app_0_mains import AssMaterials as AF
from app_0_mains import CamSun as CF
from app_0_mains import ClearScene as CS
from app_0_mains import Settings_scen as SC
from app_0_mains import Border_Scene as BS

# from .app_0_mains import LUCK as LF

from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, PropertyGroup, Panel
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
    # DEFAULT ЗНАЧЕНИЯ
    gr = "граничка название"
    # gr = "2"
    pth_gpgk = "путь к GPKG"
    # pth_gpgk = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\gpkg\URBANPLANNING.gpkg"
    pth_fgm = r"путь к ФГМ"
    # pth_fgm = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\03_FGM\\"
    path_descktop = Path.home() / "Desktop"
    tmp_dir = f"{path_descktop}"
    # tmp_dir = r"C:\Users\dolgushin_an\Desktop\\"

    # свойство строки для выбора границы из слоя
    my_string: StringProperty(
        name="Название гранички",
        description=str_1.upper(),
        default=gr,
        maxlen=512,
    )

    # свойство строки для выбора пути к объекту
    my_path: StringProperty(
        name="Путь к GPKG",
        description=str_2.upper(),
        default=pth_gpgk,
        maxlen=1024,
        subtype='FILE_PATH'  # раскоментируй если нужен значёк
    )
    # свойство строки для выбора пути к ФГМ
    fgm_path: StringProperty(
        name="Путь к FGM",
        description=str_3.upper(),
        default=pth_fgm,
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
    # свойство строки для выбора временной папки
    my_string_tmp: StringProperty(
        name="Временный каталог",
        description=str_4.upper(),
        default=tmp_dir,
        maxlen=1024,
        subtype='DIR_PATH'
    )


# ------------------------------------------------------------------------
#    Panels
# ------------------------------------------------------------------------
class DAD_MT_panel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "__MRGP__"
    bl_options = {"DEFAULT_CLOSED"}


class PAN_PT_one(DAD_MT_panel, Panel):
    bl_idname = "PAN_PT_one"
    bl_label = "MAIN"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.mrgp

        layout.scale_y = 1.1
        layout.prop(mytool, "my_path")
        layout.prop(mytool, "fgm_path")
        layout.prop(mytool, "my_string_tmp")
        layout.prop(mytool, "my_string")

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('func.func_op', text='LUCKY!', icon='PLAY').action = 'LUCK'
        row.operator('func.func_op', text='CAMERA_SUN', icon='VIEW_CAMERA').action = 'CAM_SUN'
        row.operator('func.func_op', text='CLEAR_SCENE', icon='X').action = 'CLEAR'
        # layout.separator(factor=1)
        # layout.row().separator()
        row2 = layout.row(align=True)
        row2.scale_y = 1.3
        row2.operator('func.func_op', text='Aply render settings', icon='MODIFIER').action = 'RENDSET'
        row2.operator('func.func_op', text='Scene for border', icon='DUPLICATE').action = 'BORDERSCENE'

class PAN_PT_two(DAD_MT_panel, Panel):
    bl_idname = "PAN_PT_two"
    bl_label = "Работа с выборками"

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 1.1
        scene = context.scene
        mytool = scene.mrgp
        layout.prop(mytool, "my_enum", text="")
        layout.prop(mytool, "my_string_add")
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('func.func_op', text='IMPORT', icon='PLAY').action = 'RUN'
        row.operator('func.func_op', text='Assign_MAT', icon='BRUSH_DATA').action = 'ASS_MAT'
        row.operator('func.func_op', text='Delite_MAT', icon='X').action = 'DEL_MAT'


# ------------------------------------------------------------------------
#    OPERATORS
# ------------------------------------------------------------------------
class FUNC_OT_my_func(Operator):
    bl_idname = 'func.func_op'
    bl_label = 'Func'
    # bl_description = 'Test'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(
        items=(
            ('RUN', 'RUN', 'run'),
            ('ASS_MAT', 'ASS_MAT', 'ass_mat'),
            ('LUCK', 'LUCK', 'luck'),
            ('DEL_MAT', 'DEL_MAT', 'del_mat'),
            ('CAM_SUN', 'CAM_SUN', 'cam_sun'),
            ('CLEAR', 'CLEAR_SCENE', 'clear scene'),
            ('RENDSET', 'RENDSET', 'RendSet'),
            ('BORDERSCENE', 'BORDERSCENE', 'BorderScene')
        )
    )

    def execute(self, context):

        if self.action == 'LUCK':
            self.LF = LF()                  # инициализируем класс
            self.LF.run_import()            # запускаем скрипт из другого класса

            self.AF = AF()                  # инициируем класс
            self.AF.run_ass_materials()     # запускаем скрипт из другог класса

        elif self.action == 'CAM_SUN':
            self.CF = CF()                  # инициируем класс
            self.CF.run_camsun()            # запускаем скрипт из другог класса

        elif self.action == 'CLEAR':
            self.CS = CS()                  # инициируем класс
            self.CS.run_clear_scene()       # запускаем скрипт из другог класса

        elif self.action == 'RUN':
            self.LF = LF()                  # инициализируем класс
            self.LF.run_selection_import()  # запускаем скрипт из другого класса

            self.AF = AF()                  # инициируем класс
            self.AF.run_ass_materials()     # запускаем скрипт из другог класса

        elif self.action == 'ASS_MAT':
            self.LF = LF()                  # инициализируем класс
            self.LF.vwport_show_all()       # вызываем функцию

            self.AF = AF()                  # инициируем класс
            self.AF.run_ass_materials()     # запускаем скрипт из другог класса

            self.LF.vwport_hide()           # вызываем функцию


        elif self.action == 'DEL_MAT':
            self.AF = AF()                  # инициируем класс
            self.AF.delite_mat_from_obj()   # запускаем скрипт из другог класса

        elif self.action == 'RENDSET':
            self.SC = SC()                  # инициируем класс
            self.SC.run_scene_settings()    # запускаем скрипт из другог класса
            print("rendset")

        elif self.action == 'BORDERSCENE':
            self.BS = BS()                  # инициируем класс
            self.BS.run_border_set()        # запускаем скрипт из другого класса
            print("BorderScene")


        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------
classes = (
    MyProperties,
    PAN_PT_one,
    PAN_PT_two,
    FUNC_OT_my_func
)


def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.mrgp = PointerProperty(type=MyProperties)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.mrgp
    # PointerProperty(type=MyProperties)


if __name__ == '__main__':
    register()