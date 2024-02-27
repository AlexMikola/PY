# -*- coding: utf-8 -*-
import bpy
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
import sys

ORIG_SYS_PATH = list(sys.path)
mod_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\mod"
if mod_path not in ORIG_SYS_PATH:
    sys.path.insert(1, mod_path)
    MOD_SYS_PATH = list(sys.path)


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
        mytool = scene.my_tool

        layout.scale_y = 1.1
        layout.prop(mytool, "my_path")
        layout.prop(mytool, "fgm_path")
        layout.prop(mytool, "my_string_tmp")
        layout.prop(mytool, "my_string")
        row = layout.row(align=True)
        row.scale_y = 1.3
        row.operator('func.func_op', text='LUCKY!').action = 'LUCK'
        row.operator('func.func_op', text='CAMERA_SUN').action = 'CAM_SUN'
        row.operator('func.func_op', text='CLEAR_SCENE').action = 'CLEAR'

class PAN_PT_two(DAD_MT_panel, Panel):
    bl_idname = "PAN_PT_two"
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
        row.operator('func.func_op', text='IMPORT').action = 'RUN'
        row.operator('func.func_op', text='Assign_MAT').action = 'ASS_MAT'
        row.operator('func.func_op', text='Delite_MAT').action = 'DEL_MAT'

# ------------------------------------------------------------------------
#    OPERATORS
# ------------------------------------------------------------------------
class FUNC_OT_my_func(Operator):
    bl_idname = 'func.func_op'
    bl_label = 'Func'
    # bl_description = 'Test'
    bl_options = {'REGISTER', 'UNDO'}

    action: EnumProperty(
        items=[
            ('RUN', 'RUN', 'run'),
            ('ASS_MAT', 'ASS_MAT', 'ass_mat'),
            ('LUCK', 'LUCK', 'luck'),
            ('DEL_MAT', 'DEL_MAT', 'del_mat'),
            ('CAM_SUN', 'CAM_SUN', 'cam_sun'),
            ('CLEAR', 'CLEAR_SCENE', 'clear scene')
        ]
    )

    def execute(self, context):
        if self.action == 'RUN':
            print("RUN")

        elif self.action == 'ASS_MAT':
            print("ASS_MAT")

        elif self.action == 'LUCK':
            print("LUCK")

        elif self.action == 'DEL_MAT':
            print("DEL_MAT")

        elif self.action == 'CAM_SUN':
            print("CAM_SUN")

        elif self.action == 'CLEAR':
            print("CLEAR")

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
    bpy.types.Scene.my_tool = PointerProperty(type=MyProperties)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    del bpy.types.Scene.my_tool


if __name__ == '__main__':
    register()