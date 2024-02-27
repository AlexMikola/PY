bl_info = {
    # required
    'name': 'My Example Addon',
    'blender': (2, 93, 0),
    'category': 'Object',
    # optional
    'version': (1, 0, 0),
    'author': 'Mina Pêcheux',
    'description': 'An example addon',
}

import bpy

class ExamplePanel(bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_example_panel'
    bl_label = 'Example Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        self.layout.label(text='Hello there')


if __name__ == '__main__':
    bpy.utils.register_class(ExamplePanel)