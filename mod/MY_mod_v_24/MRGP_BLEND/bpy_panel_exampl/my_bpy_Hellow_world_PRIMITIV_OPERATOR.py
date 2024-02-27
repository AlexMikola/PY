import bpy


class HelloWorldOperator(bpy.types.Operator):
    bl_idname = "wm.hello_world"
    bl_label = "Minimal Operator"

    def execute(self, context):
        print("Hello World")
        return {'FINISHED'}

# регистрация класса,
bpy.utils.register_class(HelloWorldOperator)

# по завершению работы нужно выгрузить класс из зарегистрированных классов
# bpy.utils.unregister_class(HelloWorldOperator)

# для вызова набрать в командной строке
bpy.ops.wm.hello_world()