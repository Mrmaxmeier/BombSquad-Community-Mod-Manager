import os
import bpy
import mathutils
from struct import *
from bpy.props import (
	BoolProperty,
	FloatProperty,
	StringProperty,
	EnumProperty,
)
from bpy_extras.io_utils import (
	ImportHelper,
	ExportHelper,
	unpack_list,
	unpack_face_list,
	axis_conversion,
)

bl_info = {
	"name": "BOB format",
	"description": "Import-Export bombsquad .bob files.",
	"author": "Mrmaxmeier",
	"version": (0, 0),
	"blender": (2, 76, 0),
	"location": "File > Import-Export",
	"warning": "", # used for warning icon and text in addons panel
	"wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
				"Scripts/My_Script",
	"category": "Import-Export"}

BOB_FILE_ID = 45623

"""
 File Structure:

 MAGIC 45623 (I)
 meshFormat  (I)
 vertexCount (I)
 faceCount   (I)
 VertexObject x vertexCount (fff HH hhh xx)
 index x faceCount*3 (b / H)

 struct VertexObjectFull{
   float position[3];
   bs_uint16 uv[2]; // normalized to 16 bit unsigned ints 0 - 65535
   bs_sint16  normal[3]; // normalized to 16 bit signed ints -32768 - 32767
   bs_uint8 _padding[2];
 };
"""


class ImportBOB(bpy.types.Operator, ImportHelper):
	"""Load an Bombsquad Mesh file"""
	bl_idname = "import_mesh.bob"
	bl_label = "Import Bombsquad Mesh"
	filename_ext = ".bob"
	filter_glob = StringProperty(
		default="*.bob",
		options={'HIDDEN'},
	)
	def execute(self, context):
		keywords = self.as_keywords(ignore=('filter_glob',))
		mesh = load(self, context, **keywords)
		if not mesh:
			return {'CANCELLED'}

		scene = bpy.context.scene
		obj = bpy.data.objects.new(mesh.name, mesh)
		scene.objects.link(obj)
		scene.objects.active = obj
		obj.select = True
		obj.matrix_world = axis_conversion(from_forward='-Z', from_up='Y').to_4x4()
		scene.update()
		return {'FINISHED'}

class ExportBOB(bpy.types.Operator, ExportHelper):
	"""Save an Bombsquad Mesh file"""
	bl_idname = "export_mesh.bob"
	bl_label = "Export Bombsquad Mesh"
	filter_glob = StringProperty(
		default="*.bob",
		options={'HIDDEN'},
	)
	check_extension = True
	filename_ext = ".bob"

	triangulate = BoolProperty(
		name="Triangulate Mesh",
		description="automatic triangulation for .bob files",
		default=False,
	)

	recalc_normal = BoolProperty(
		name="Recalculate Normals",
		description="recalculate vertex normals while exporting to .bob",
		default=False,
	)

	def execute(self, context):
		keywords = self.as_keywords(ignore=('filter_glob',))
		global_matrix = axis_conversion(from_forward='-Z', from_up='Y').to_4x4()
		return save(self, context, global_matrix=global_matrix, **keywords)

def menu_func_import(self, context):
	self.layout.operator(ImportBOB.bl_idname, text="Bombsquad Mesh (.bob)")

def menu_func_export(self, context):
	self.layout.operator(ExportBOB.bl_idname, text="Bombsquad Mesh (.bob)")

def register():
	bpy.utils.register_module(__name__)
	bpy.types.INFO_MT_file_import.append(menu_func_import)
	bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
	bpy.utils.unregister_module(__name__)
	bpy.types.INFO_MT_file_import.remove(menu_func_import)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)

def load(operator, context, filepath):
	filepath = os.fsencode(filepath)
	file = open(filepath, 'rb')
	def readstruct(s):
		tup = unpack(s, file.read(calcsize(s)))
		return tup[0] if len(tup) == 1 else tup
	assert readstruct("I") == BOB_FILE_ID
	meshFormat = readstruct("I")
	assert meshFormat in [0, 1]

	vertexCount = readstruct("I")
	faceCount = readstruct("I")

	verts = []
	faces = []
	edges = []
	indices = []

	for i in range(vertexCount):
		vertexObj = readstruct("fff HH hhh xx")
		position = (vertexObj[0], vertexObj[1], vertexObj[2])
		# FIXME: map normalized ints to float
		uv = (vertexObj[3], vertexObj[4])
		normal = (vertexObj[5], vertexObj[6], vertexObj[7])
		verts.append(position)

	for i in range(faceCount*3):
		if meshFormat == 0:
			# MESH_FORMAT_UV16_N8_INDEX8
			indices.append(readstruct("b"))
		elif meshFormat == 1:
			# MESH_FORMAT_UV16_N8_INDEX16
			indices.append(readstruct("H"))

	for i in range(faceCount):
		faces.append((indices[i*3], indices[i*3+1], indices[i*3+2]))

	bob_name = bpy.path.display_name_from_filepath(filepath)
	mesh = bpy.data.meshes.new(name=bob_name)
	mesh.from_pydata(verts,edges,faces)

	print(mesh.uv_textures)

	mesh.validate()
	mesh.update()

	return mesh

def save(operator, context, filepath, triangulate, recalc_normal, global_matrix, check_existing):
	# Export the selected mesh
	scene = context.scene
	obj = scene.objects.active
	mesh = obj.to_mesh(scene, True, 'PREVIEW')

	filepath = os.fsencode(filepath)
	with open(filepath, 'wb') as file:

		def writestruct(s, *args):
			file.write(pack(s, *args))

		writestruct('I', BOB_FILE_ID)
		writestruct('I', 1) # MESH_FORMAT_UV16_N8_INDEX16
		writestruct('I', len(mesh.vertices))
		writestruct('I', len(mesh.tessfaces))

		for i, vert in enumerate(mesh.vertices):
			print(i, vert, *vert.co)
			writestruct('fff', *vert.co) # position
			writestruct('HH', 0, 0) # uv FIXME
			writestruct('hhh', 0, 0, 0) # normals FIXME
			writestruct('xx')

		for i, face in enumerate(mesh.tessfaces):
			print(i, face)
			assert len(face.vertices) == 3 # TODO: triangulate
			for vertid in face.vertices:
				writestruct('H', vertid)
	return {'FINISHED'}

if __name__ == "__main__":
	register()
