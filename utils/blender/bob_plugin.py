import os
import os.path
import bpy
import bmesh
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
		name="Force Triangulation",
		description="force triangulation of .bob files",
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
	bs_dir = os.path.dirname(os.path.dirname(filepath))
	texpath = os.path.join(bs_dir, b"textures", os.path.basename(filepath).rstrip(b".bob") + b".dds")
	print(texpath)
	has_texture = os.path.isfile(texpath)
	print("has_texture", has_texture)

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
	uv_list = []

	for i in range(vertexCount):
		vertexObj = readstruct("fff HH hhh xx")
		position = (vertexObj[0], vertexObj[1], vertexObj[2])
		# FIXME: map normalized ints to float
		uv = (vertexObj[3] / 65535, vertexObj[4] / 65535)
		normal = (vertexObj[5] / 32767, vertexObj[6] / 32767, vertexObj[7] / 32767)
		verts.append(position)
		uv_list.append(uv)

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

	if has_texture:
		uv_texture = mesh.uv_textures.new("uv_map")
		uv_texture.data[0].image = bpy.data.images.load(texpath)
		bm = bmesh.new()
		bm.from_mesh(mesh)
		bm.faces.ensure_lookup_table()

		uv_layer = bm.loops.layers.uv[0]
		for i, face in enumerate(bm.faces):
			for vi, vert in enumerate(face.verts):
				uv = uv_list[vert.index]
				uv = (uv[0], 1 - uv[1])
				face.loops[vi][uv_layer].uv = uv
		bm.to_mesh(mesh)
		bm.free()

	mesh.validate()
	mesh.update()

	return mesh

def save(operator, context, filepath, triangulate, recalc_normal, global_matrix, check_existing):
	# Export the selected mesh
	scene = context.scene
	obj = scene.objects.active
	mesh = obj.to_mesh(scene, True, 'PREVIEW')

	if triangulate or any([len(face.vertices) != 3 for face in mesh.tessfaces]):
		print("triangulating...")
		bm = bmesh.new()
		bm.from_mesh(mesh)
		bmesh.ops.triangulate(bm, faces=bm.faces)
		bm.to_mesh(mesh)
		bm.free()
		del bm

	filepath = os.fsencode(filepath)

	with open(filepath, 'wb') as file:

		def writestruct(s, *args):
			file.write(pack(s, *args))

		writestruct('I', BOB_FILE_ID)
		writestruct('I', 1) # MESH_FORMAT_UV16_N8_INDEX16
		writestruct('I', len(mesh.vertices))
		writestruct('I', len(mesh.tessfaces))

		uv_by_vert = {}
		bm = bmesh.new()
		bm.from_mesh(mesh)
		uv_layer = bm.loops.layers.uv[0]
		for i, face in enumerate(bm.faces):
			for vi, vert in enumerate(face.verts):
				uv = face.loops[vi][uv_layer].uv
				uv = (int(uv[0]*65535), int((1-uv[1])*65535))
				uv_by_vert[vert.index] = uv

		bm.free()
		del bm

		for i, vert in enumerate(mesh.vertices):
			writestruct('fff', *vert.co) # position
			uv = uv_by_vert.get(vert.index, (0, 0))
			writestruct('HH', *uv)
			normal = tuple(map(lambda n: int(n*32767), vert.normal))
			normal = normal_by_vert.get(vert.index, (0, 0, 0))
			print(normal)
			writestruct('hhh', *normal)
			writestruct('xx')

		for i, face in enumerate(mesh.tessfaces):
			assert len(face.vertices) == 3
			for vertid in face.vertices:
				writestruct('H', vertid)

	return {'FINISHED'}

if __name__ == "__main__":
	register()
