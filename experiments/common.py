"""Blender 4.0/4.2 compatible helpers for Flyxion headless experiments."""

import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

INK = (0.012, 0.018, 0.028, 1)
CYAN = (0.03, 0.75, 1.0, 1)
AMBER = (1.0, 0.32, 0.04, 1)
GREEN = (0.12, 0.9, 0.42, 1)
VIOLET = (0.62, 0.22, 1.0, 1)
RED = (1.0, 0.06, 0.1, 1)
PAPER = (0.74, 0.78, 0.76, 1)


def args(name):
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="output")
    p.add_argument("--name", default=name)
    p.add_argument("--resolution", default="1280x1280")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--seed", type=int, default=23)
    p.add_argument("--engine", choices=("AUTO", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"), default="AUTO")
    p.add_argument("--no-render", action="store_true")
    return p.parse_args(argv)


def begin(a):
    random.seed(a.seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    engines = {e.identifier for e in scene.render.bl_rna.properties["engine"].enum_items}
    engine = a.engine
    if engine == "AUTO":
        engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    if engine not in engines:
        raise RuntimeError(f"Engine {engine} unavailable; found {sorted(engines)}")
    scene.render.engine = engine
    scene.render.resolution_x, scene.render.resolution_y = (int(v) for v in a.resolution.lower().split("x", 1))
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    if engine == "CYCLES":
        scene.cycles.samples = a.samples
        scene.cycles.use_denoising = True
    scene.world = bpy.data.worlds.new("World")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = INK
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except Exception:
        pass
    return scene


def mat(name, color, emission=0.0, metallic=0.0, roughness=0.42, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    rgba = (*color[:3], alpha)
    p.inputs["Base Color"].default_value = rgba
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    p.inputs["Alpha"].default_value = alpha
    key = "Emission Color" if "Emission Color" in p.inputs else "Emission"
    p.inputs[key].default_value = rgba
    p.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        if hasattr(m, "surface_render_method"):
            m.surface_render_method = "DITHERED"
        else:
            m.blend_method = "BLEND"
    return m


def use(obj, material):
    obj.data.materials.append(material)
    return obj


def sphere(name, radius, location, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    return use(obj, material)


def cube(name, scale, location, material):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    return use(obj, material)


def cylinder(name, radius, depth, location, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return use(obj, material)


def torus(name, major, minor, location, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=72,
                                    minor_segments=10, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return use(obj, material)


def curve(name, points, material, radius=0.035, cyclic=False):
    data = bpy.data.curves.new(name, "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("NURBS" if len(points) > 3 else "POLY")
    spline.points.add(len(points) - 1)
    for p, co in zip(spline.points, points):
        p.co = (*co, 1)
    if len(points) > 3:
        spline.order_u = min(4, len(points))
        spline.use_endpoint_u = not cyclic
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    data.materials.append(material)
    return obj


def segment(name, a, b, material, radius=0.055):
    a, b = Vector(a), Vector(b)
    d = b - a
    obj = cylinder(name, radius, d.length, (a + b) / 2, material)
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def text(label, location, size=0.32, material=None, rotation=(math.pi / 2, 0, 0), align="CENTER"):
    data = bpy.data.curves.new(f"Text {label}", "FONT")
    data.body, data.size, data.align_x, data.extrude = label, size, align, 0.008
    obj = bpy.data.objects.new(f"Text {label}", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location, obj.rotation_euler = location, rotation
    data.materials.append(material or mat(f"Text {label}", PAPER, emission=0.35))
    return obj


def floor(size=30):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, -0.05))
    return use(bpy.context.object, mat("Floor", (0.018, 0.028, 0.04, 1), metallic=0.12, roughness=0.3))


def camera(location, target=(0, 0, 2), lens=52):
    data = bpy.data.cameras.new("Camera")
    obj = bpy.data.objects.new("Camera", data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location, data.lens = location, lens
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = obj
    return obj


def lights(target=(0, 0, 2), energy=1400):
    for name, loc, power, color in (("Key", (5, -8, 12), energy, (0.72, 0.88, 1.0)),
                                    ("Rim", (-7, 3, 8), energy * 0.65, (1.0, 0.22, 0.05))):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.size, data.color = power, 5.0, color
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def finish(a):
    out = Path(bpy.path.abspath(a.output)).resolve()
    out.mkdir(parents=True, exist_ok=True)
    blend, image = out / f"{a.name}.blend", out / f"{a.name}.png"
    bpy.context.scene.render.filepath = str(image)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    if not a.no_render:
        bpy.ops.render.render(write_still=True)
    print(f"EXPERIMENT_BLEND={blend}")
    if not a.no_render:
        print(f"EXPERIMENT_RENDER={image}")

