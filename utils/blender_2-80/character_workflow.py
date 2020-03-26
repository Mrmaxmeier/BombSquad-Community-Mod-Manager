bl_info = {
    "name": "BombSquad Character-making Workflow",
    "description": "provides batch import-exports and character assembly",
    "author": "Aryan",
    "blender": (2, 80, 0),
    "version": (2, 0),
    "category": "BombSquad",
    "location": "3D View > UI > Create",
    "warning": "bob_plugin must be installed and enabled",
}

import bpy

allparts = ["Head", "Torso", "Pelvis", "UpperArm", "ForeArm", "Hand", "UpperLeg", "LowerLeg", "Toes"]
mirrorparts = ["UpperArm", "ForeArm", "Hand", "UpperLeg", "LowerLeg", "Toes"]
locrot = [[0,0,0.942794,1.5708,0,0],[0,0,0.496232,1.5708,0,0],[0,-0.03582,0.361509,1.35976,0,0],[-0.207339,0.016968,0.516395,3.32611,0.185005,0],[-0.199252,-0.013197,0.372489,2.67074,0,0],[-0.195932,-0.0641,0.321099,2.39285,0,0],[-0.09192,-0.031631,0.266533,2.94554,0,0],[-0.088037,-0.063052,0.113304,3.14159,0,0],[-0.086935,-0.11274,0.069577,3.14159,0,0]]


class AddonProperties(bpy.types.PropertyGroup):
    importfrom: bpy.props.StringProperty(name="import from", description="path to the bombsquad models folder", maxlen=1024, default="neoSpaz")
    importmodelname: bpy.props.StringProperty(name="import model name", description="name of character to import", maxlen=1024, default="neoSpaz")
    exportto: bpy.props.StringProperty(name="export to", description="path to folder to put new files", maxlen=1024, default="neoSpaz")
    exportmodelname: bpy.props.StringProperty(name="export model name", description="name of new character", maxlen=1024, default="untitled")


class BatchImportBOB(bpy.types.Operator):
    """Import all models for character"""
    bl_idname = "bs.batchimportbob"
    bl_label = "Import all models for character"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        importmodelname = bpy.context.scene.bombsquad.importmodelname
        importfrom = bpy.context.scene.bombsquad.importfrom
        for index in range(len(allparts)):
            bpy.ops.import_mesh.bob(filepath=importfrom+"\\"+importmodelname+allparts[index]+".bob")
            bpy.data.objects[importmodelname+allparts[index]].name = allparts[index]
        bpy.ops.bs.assemble()
        return {'FINISHED'}

    
class BatchExportBOB(bpy.types.Operator):
    """Export all models for character"""
    bl_idname = "bs.batchexportbob"
    bl_label = "Export all models for character"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        bpy.ops.bs.disassemble()
        exportmodelname = bpy.context.scene.bombsquad.exportmodelname
        exportto = bpy.context.scene.bombsquad.exportto
        for part in allparts:    
            bpy.ops.export_mesh.bob(filepath=exportto+"\\"+exportmodelname+part+".bob")
        return {'FINISHED'}


class Assemble(bpy.types.Operator):
    """Assembles the bombsquad mesh"""
    bl_idname = "bs.assemble"
    bl_label = "Assemble the bombsquad mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for index in range(len(allparts)):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[allparts[index]].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[allparts[index]]
            bpy.context.object.location = (locrot[index][0], locrot[index][1], locrot[index][2])
            bpy.context.object.rotation_euler = (locrot[index][3], locrot[index][4], locrot[index][5])
            #bpy.ops.object.shade_smooth()
            #bpy.context.object.data.use_auto_smooth = True
            #bpy.context.object.data.auto_smooth_angle = 0.523599

        bpy.ops.object.select_all(action='DESELECT')

        for index in range(len(mirrorparts)):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[mirrorparts[index]].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[mirrorparts[index]]
            bpy.ops.object.modifier_add(type='MIRROR')
            bpy.context.object.modifiers["Mirror"].mirror_object = bpy.data.objects[allparts[2]]
            
        bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}
    
    
class Disassemble(bpy.types.Operator):
    """Disassembles the bombsquad mesh"""
    bl_idname = "bs.disassemble"
    bl_label = "Disassemble the bombsquad mesh"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        for index in range(len(allparts)):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[allparts[index]].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[allparts[index]]
            bpy.context.scene.cursor.location = (locrot[index][0], locrot[index][1], locrot[index][2])
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
            bpy.context.object.location = (0, 0, 0)
            bpy.context.object.rotation_euler = (1.5708, 0, 0)
            
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.scene.cursor.location = (0, 0, 0)

        for index in range(len(mirrorparts)):
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[mirrorparts[index]].select_set(True)
            bpy.context.view_layer.objects.active = bpy.data.objects[mirrorparts[index]] 
            bpy.ops.object.modifier_remove(modifier="Mirror")

        bpy.ops.object.select_all(action='DESELECT')
    
        return {'FINISHED'}


class OBJECT_PT_bombsquad(bpy.types.Panel):
    bl_idname = "object_PT_bombsquad"
    bl_label = "Bombsquad"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create"
    bl_context = "objectmode"


    def draw(self, context):
        self.layout.use_property_split = True
        
        box1 = self.layout.box()
        box1.label(text="Import")
        box1.prop(context.scene.bombsquad, "importfrom")
        box1.prop(context.scene.bombsquad, "importmodelname")
        box1.operator('bs.batchimportbob',icon="IMPORT")
        
        box2 = self.layout.box()
        box2.label(text="Export")
        box2.prop(context.scene.bombsquad, "exportto")
        box2.prop(context.scene.bombsquad, "exportmodelname")
        box2.operator('bs.batchexportbob',icon="EXPORT")
        box2.operator('bs.assemble',icon="ARMATURE_DATA")



classes = (
    AddonProperties,
    Assemble,
    Disassemble,
    BatchImportBOB,
    BatchExportBOB,
    OBJECT_PT_bombsquad,
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.bombsquad = bpy.props.PointerProperty(type=AddonProperties)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.bombsquad


if __name__ == "__main__":
    register()