crvs_name = [r.name for r in bpy.data.curves]
objcts_name = [r.name for r in bpy.data.objects]
meshs_name = [r.name for r in bpy.data.meshes]
colls_name = [r.name for r in bpy.data.collections]
selected_name = [x.name for x in bpy.context.selected_objects]
view_objcts = [x.name for x in bpy.context.view_layer.objects]

[print(r.name) for r in bpy.data.curves if r.name != "None"]
[print(r.name) for r in bpy.data.objects]
[print(r.name) for r in bpy.data.meshes]
[print(r.name) for r in bpy.data.collections]
[print(x.name) for x in bpy.context.selected_objects]
[print(x.name) for x in bpy.context.view_layer.objects]


print(len([r.name for r in bpy.data.curves]))
print(len([r.name for r in bpy.data.objects]))
print(len([r.name for r in bpy.data.meshes]))
print(len([r.name for r in bpy.data.collections]))
print(len([x.name for x in bpy.context.selected_objects]))
print(len([x.name for x in bpy.context.view_layer.objects]))



import bpy
import os

# "//" prefix is a Blender specific identifier for the current blend file
#filepath = "//link_library.blend"
#abs_filepath = bpy.path.abspath(filepath) # returns the absolute path

# os.path.abspath(__file__) returns path to the script
filepath = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\default.blend"


# link all objects starting with 'Cube'
with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
    # data_to.objects = [name for name in data_from.objects if name.startswith("Cube")]
    data_to.materials = data_from.materials

for mat in data_to.materials:
    if mat is not None:
        mt = bpy.data.materials.new(mat.name)
        mt = mat
        # bpy.context.collection.materials.link(mat)
        # bpy.context.materials.link(mat)
        # bpy.data.materials.link(mat)
        # bpy.context.collection.materials.link(mat)

bpy.ops.wm.save_as_mainfile(
    filepath=r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\scen_tmp\tester999.blend")


bpy.ops.wm.append(filename="object_2", directory="D:/blend_folder/external_blender_file.blend\\Object\\")
with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
    data_to.materials = data_from.materials




# link object to scene collection
for obj in data_to.objects:
    if obj is not None:
       bpy.context.collection.objects.link(obj)



def append_mat_from_file():
    sc_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\default.blend"
    dir_path = r"C:\!_Python\_899_Blener_port\!!!!_MRGP_plugin\default\\"
    with bpy.data.libraries.load(filepath=sc_path, directory=dir_path, link=False) as (data_from, data_to):
        # data_to.materials = [m for m in data_from.materials if m.startswith("MATLIB_")]
        data_to.materials = [m for m in data_from.materials]