import bpy
import os, sys, time
# PKG, SUBPKG = __package__.split('.', maxsplit=1)
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, PropertyGroup, Panel
from bpy.props import StringProperty, PointerProperty, EnumProperty, IntProperty


class GEOSCENE_PT_georef(Panel):
    bl_category = "__MRGP__"  # "GIS"
    bl_label = "MAIN"
    bl_space_type = "VIEW_3D"
    # bl_context = "objectmode"
    bl_region_type = "UI"
    # draw = Menu.draw_preset

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        # geoscn = GeoScene(scn)
        row = layout.row(align=True)

        row.operator("importgis.shapefile_file_dialog", icon='PREFERENCES')


class VIEW3D_MT_menu_gis(bpy.types.Menu):
    bl_label = "GIS"

    # Set the menu operators and draw functions
    def draw(self, context):
        layout = self.layout
        layout.operator("bgis.pref_show", icon='PREFERENCES')
        layout.separator()
        layout.menu('VIEW3D_MT_menu_gis_import', icon='IMPORT')


class VIEW3D_MT_menu_gis_import(bpy.types.Menu):
    bl_label = "Import"

    def draw(self, context):
        layout = self.layout
        layout.operator("importgis.shapefile_file_dialog", text='Shapefile (.shp)')


class BGIS_OT_pref_show(Operator):

    bl_idname = "bgis.pref_show"
    bl_description = 'Display BlenderGIS addons preferences'
    bl_label = "Preferences"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        addon_utils.modules_refresh()
        context.preferences.active_section = 'ADDONS'
        bpy.data.window_managers["WinMan"].addon_search = bl_info['name']
        #bpy.ops.wm.addon_expand(module=PKG)
        mod = addon_utils.addons_fake_modules.get(PKG)
        mod.bl_info['show_expanded'] = True
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        return {'FINISHED'}


class IMPORTGIS_OT_shapefile_file_dialog(Operator):
    """Select shp file, loads the fields and start importgis.shapefile_props_dialog operator"""

    bl_idname = "importgis.shapefile_file_dialog"
    bl_description = 'Import ESRI shapefile (.shp)'
    bl_label = "Import SHP"
    bl_options = {'INTERNAL'}

    # Import dialog properties
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH')

    filename_ext = ".shp"

    filter_glob: StringProperty(
        default="*.shp",
        options={'HIDDEN'})

    def invoke(self, context, event):
        print("invoke")
        print(f"путь в invoke - {self.filepath}")
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def draw(self, context):
        layout = self.layout
        layout.label(text="Options will be available")
        layout.label(text="after selecting a file")

    def execute(self, context):
        print("execute")
        print(f"путь в execute - {self.filepath}")
        if os.path.exists(self.filepath):
            pass
            # bpy.ops.importgis.shapefile_props_dialog('INVOKE_DEFAULT', filepath=self.filepath)
        else:
            self.report({'ERROR'}, "Invalid filepath")
        return {'FINISHED'}


# ------------------------------------------------------------------------
#    Registration
# ------------------------------------------------------------------------
classes = (
    GEOSCENE_PT_georef,
    IMPORTGIS_OT_shapefile_file_dialog
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == '__main__':
    register()
