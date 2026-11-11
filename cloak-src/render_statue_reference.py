# render_statue_reference.py - renders the game's Ysgramor statue (meshes\clutter\statues\statueysgramor.nif, unpacked
# into _reference\ - a Bethesda file, git-ignored, never shipped) from six angles in a clay look with cavity shading,
# as the reference for our own cloak (the owner, 2026-11-11: "you can find the Isgrimor statue in the game files and
# load it into Blender to use as a reference for the cloak").
# Run: blender --background --factory-startup --python render_statue_reference.py
import bpy, os, addon_utils
from math import radians
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
NIF = os.path.join(HERE, "_reference", "meshes", "clutter", "statues", "statueysgramor.nif")
OUT = os.path.join(HERE, "_reference", "renders"); os.makedirs(OUT, exist_ok=True)
addon_utils.enable("io_scene_nifly", default_set=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
bpy.ops.import_scene.pynifly(filepath=NIF, blender_xf=False, import_collisions=False)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
lo = Vector((min(min((o.matrix_world @ Vector(c)).x for c in o.bound_box) for o in meshes),
             min(min((o.matrix_world @ Vector(c)).y for c in o.bound_box) for o in meshes),
             min(min((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in meshes)))
hi = Vector((max(max((o.matrix_world @ Vector(c)).x for c in o.bound_box) for o in meshes),
             max(max((o.matrix_world @ Vector(c)).y for c in o.bound_box) for o in meshes),
             max(max((o.matrix_world @ Vector(c)).z for c in o.bound_box) for o in meshes)))
mid = (lo + hi) / 2; size = hi - lo
print("STATUE bounds", tuple(round(v, 1) for v in lo), tuple(round(v, 1) for v in hi), "meshes", [o.name for o in meshes])
sc = bpy.context.scene; sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.72, 0.70, 0.66)
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.curvature_ridge_factor = 1.5; sh.curvature_valley_factor = 1.5
sh.show_shadows = True; sh.background_type = 'VIEWPORT'; sh.background_color = (0.32, 0.33, 0.35)
sc.render.resolution_x, sc.render.resolution_y = 1100, 1400; sc.render.image_settings.file_format = 'PNG'
cd = bpy.data.cameras.new("Ref"); cd.type = 'ORTHO'; cd.ortho_scale = max(size.z, size.x, size.y) * 1.08
cam = bpy.data.objects.new("Ref", cd); sc.collection.objects.link(cam); sc.camera = cam
dist = max(size) * 3
views = {"front": (0, -1), "back": (0, 1), "left": (-1, 0), "right": (1, 0), "front_left": (-0.7071, -0.7071), "back_right": (0.7071, 0.7071)}
for name, (dx, dy) in views.items():
    cam.location = mid + Vector((dx * dist, dy * dist, 0))
    cam.rotation_euler = (mid - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f"statue_{name}.png"); bpy.ops.render.render(write_still=True)
print("STATUE renders ->", OUT)
