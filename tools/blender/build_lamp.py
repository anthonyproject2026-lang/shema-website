"""Build the SHEMA "Light the lamp" scene in Blender 4.4 (bpy, primitives and modifiers only).

Scene plan by Fable 5.2 (see PR description). Run from the repo root:

  blender -b --factory-startup -P tools/blender/build_lamp.py -- --export --render

Outputs
  assets/3d/lamp.glb                  web model (no textures, no Draco: CSP stays wasm-free)
  tools/blender/out/lamp-lit.png      1600x1200 RGBA lit still (no-JS / no-WebGL image)
  tools/blender/out/lamp-og.png       1200x630 RGBA plate for the social image
  tools/blender/out/lamp-draco.glb    Draco comparison only (not shipped)
Blender: Z-up, front = -Y. glTF export: Y-up, front = +Z.
"""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "tools" / "blender" / "out"
LAMP_SCALE = 1.5  # lamp enlarged 1.5x after the first render so it reads as the hero object
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


# ---------------------------------------------------------------- helpers
def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    return tuple(srgb_to_linear(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (a,)


MATS = {}


def mat(name, hexcol, metallic=0.0, roughness=0.8, emission=None, strength=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgba(hexcol)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(emission)
        bsdf.inputs["Emission Strength"].default_value = strength
    m.diffuse_color = hex_rgba(hexcol)
    MATS[name] = m
    return m


def assign(obj, m):
    obj.data.materials.clear()
    obj.data.materials.append(m)


def apply_all(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)


def shade(obj, smooth=True, angle=35):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    if smooth:
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(angle))
    else:
        bpy.ops.object.shade_flat()


def join(objs, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = name
    o.data.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def cyl(r, depth, verts, loc, m, cap="NGON", rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc,
                                        rotation=rot, end_fill_type=cap)
    o = bpy.context.active_object
    assign(o, m)
    return o


def cyl_between(p0, p1, r, verts, m):
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length,
                                        location=(p0 + p1) / 2, end_fill_type="NOTHING")
    o = bpy.context.active_object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    assign(o, m)
    apply_all(o)
    return o


def ico(r, sub, loc, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    assign(o, m)
    apply_all(o)
    return o


# ---------------------------------------------------------------- scene
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"

    mat("Brass", "#c8962a", metallic=1.0, roughness=0.35)
    mat("Oil", "#8a5a00", roughness=0.15)
    mat("Wick", "#f6f0e3", roughness=0.9)
    mat("Flame", "#f3d58a", roughness=0.5, emission="#f0a830", strength=1.6)
    mat("Plinth", "#2a1d14", roughness=0.8)
    for n, h in (("PetalRed", "#a3301f"), ("PetalGold", "#c8962a"), ("PetalCream", "#f6f0e3"),
                 ("PetalGreen", "#1b5e43"), ("PetalOchre", "#C6822B")):
        mat(n, h, roughness=0.9)
    mat("Wood", "#5c4a3c", roughness=0.7)
    mat("Skin", "#ece4d4", roughness=0.8)
    mat("Hoop", "#B23A2B", roughness=0.6)
    mat("Stick", "#C6822B", roughness=0.6)
    mat("Leaf", "#1b5e43", roughness=0.6)
    mat("LeafRib", "#0f3d2e", roughness=0.6)
    mat("Rice", "#f6f0e3", roughness=0.9)
    mat("Pappadam", "#f3d58a", roughness=0.8)
    mat("Sindoor", "#B23A2B", roughness=0.8)
    M = MATS

    # 1. Plinth
    p = cyl(1.10, 0.04, 64, (0, 0, -0.02), M["Plinth"])
    bev = p.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.008
    bev.segments = 1
    apply_all(p)
    shade(p, True)
    p.name = "Plinth"

    # 2. Pookalam
    parts = []
    for r, top, m in ((0.62, 0.006, "PetalRed"), (0.52, 0.009, "PetalGold"), (0.42, 0.012, "PetalCream"),
                      (0.32, 0.015, "PetalGreen"), (0.22, 0.018, "PetalOchre")):
        d = cyl(r, top, 48, (0, 0, top / 2), M[m], cap="NGON")
        # drop the bottom cap: it sits on the plinth and is never seen
        bm = bmesh.new()
        bm.from_mesh(d.data)
        bottom = [f for f in bm.faces if f.normal.z < -0.9]
        bmesh.ops.delete(bm, geom=bottom, context="FACES_ONLY")
        bm.to_mesh(d.data)
        bm.free()
        shade(d, False)
        parts.append(d)
    for i in range(16):
        a = math.radians(22.5 * i)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.035, radius2=0, depth=0.008,
                                        location=(0.57 * math.cos(a), 0.57 * math.sin(a), 0.010))
        c = bpy.context.active_object
        c.scale = (1.6, 0.8, 1)
        c.rotation_euler = (0, 0, a)
        assign(c, M["PetalCream"])
        apply_all(c)
        shade(c, False)
        parts.append(c)
    for i in range(8):
        a = math.radians(45 * i)
        s = ico(0.03, 1, (0.47 * math.cos(a), 0.47 * math.sin(a), 0.018), M["PetalGold"], (1, 1, 0.5))
        shade(s, False)
        parts.append(s)
    join(parts, "Pookalam")

    # 3. Lamp body (lathe profile + Screw modifier), oil, wicks
    prof = [(0.000, 0.000), (0.110, 0.000), (0.110, 0.012), (0.095, 0.022), (0.085, 0.040), (0.050, 0.060),
            (0.030, 0.085), (0.022, 0.130), (0.034, 0.150), (0.022, 0.170), (0.018, 0.230), (0.036, 0.255),
            (0.018, 0.280), (0.016, 0.340),
            (0.030, 0.355), (0.060, 0.375), (0.105, 0.392), (0.125, 0.405), (0.125, 0.412), (0.112, 0.412),
            (0.100, 0.398), (0.030, 0.396),
            (0.026, 0.420), (0.020, 0.470), (0.030, 0.490), (0.014, 0.510), (0.012, 0.560), (0.022, 0.575),
            (0.010, 0.595), (0.000, 0.610)]
    me = bpy.data.meshes.new("LampProfile")
    me.from_pydata([(r, 0, z) for r, z in prof], [(i, i + 1) for i in range(len(prof) - 1)], [])
    body = bpy.data.objects.new("LampBody", me)
    sc.collection.objects.link(body)
    scr = body.modifiers.new("Screw", "SCREW")
    scr.axis = "Z"
    scr.angle = math.radians(360)
    scr.steps = 24
    scr.render_steps = 24
    scr.use_merge_vertices = True
    scr.merge_threshold = 0.0005
    scr.use_smooth_shade = True
    scr.use_normal_calculate = True
    apply_all(body)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    assign(body, M["Brass"])
    shade(body, True)
    lamp_parts = [body]
    oil = cyl(0.108, 0.002, 24, (0, 0, 0.404), M["Oil"])
    shade(oil, False)
    lamp_parts.append(oil)
    angles = [math.radians(270 + 72 * i) for i in range(5)]
    for a in angles:
        w = cyl(0.004, 0.05, 8, (0.118 * math.cos(a), 0.118 * math.sin(a), 0.416), M["Wick"],
                rot=(0, math.radians(75), a))
        apply_all(w)
        shade(w, True)
        lamp_parts.append(w)
    lamp = join(lamp_parts, "Lamp")
    lamp.scale = (LAMP_SCALE,) * 3
    apply_all(lamp)

    # 4. Flames (separate objects, origin at the flame base)
    flames = []
    for i, a in enumerate(angles):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.012)
        for v in bm.verts:
            v.co.z *= 2.2
        top = max(bm.verts, key=lambda v: v.co.z)
        top.co.z += 0.010
        zmin = min(v.co.z for v in bm.verts)
        for v in bm.verts:
            v.co.z -= zmin
            v.co *= LAMP_SCALE
        fm = bpy.data.meshes.new(f"Flame_{i}")
        bm.to_mesh(fm)
        bm.free()
        f = bpy.data.objects.new(f"Flame_{i}", fm)
        sc.collection.objects.link(f)
        f.location = Vector((0.146 * math.cos(a), 0.146 * math.sin(a), 0.426)) * LAMP_SCALE
        assign(f, M["Flame"])
        shade(f, True, 60)
        flames.append(f)

    # 5. Chenda, back right
    cx, cy = 0.66, 0.55
    ch = [cyl(0.15, 0.50, 20, (cx, cy, 0.28), M["Wood"])]
    shade(ch[0], True)
    for z in (0.015, 0.545):
        h = cyl(0.165, 0.03, 20, (cx, cy, z), M["Skin"])
        shade(h, True)
        ch.append(h)
    for z in (0.03, 0.53):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.165, minor_radius=0.008, major_segments=20,
                                         minor_segments=6, location=(cx, cy, z))
        t = bpy.context.active_object
        assign(t, M["Hoop"])
        shade(t, True)
        ch.append(t)
    for k in range(10):
        a0, a1 = math.radians(36 * k), math.radians(36 * k + 18)
        a2 = math.radians(36 * (k + 1))
        p0 = (cx + 0.158 * math.cos(a0), cy + 0.158 * math.sin(a0), 0.03)
        p1 = (cx + 0.158 * math.cos(a1), cy + 0.158 * math.sin(a1), 0.53)
        p2 = (cx + 0.158 * math.cos(a2), cy + 0.158 * math.sin(a2), 0.03)
        for q0, q1 in ((p0, p1), (p1, p2)):
            r = cyl_between(q0, q1, 0.004, 3, M["Skin"])
            shade(r, False)
            ch.append(r)
    for ang in (20, -20):
        s = cyl(0.008, 0.32, 6, (cx, cy, 0.568), M["Stick"], rot=(0, math.radians(90), math.radians(ang)))
        apply_all(s)
        shade(s, True)
        ch.append(s)
    join(ch, "Chenda")

    # 6. Sadhya on a banana leaf, front left (built at origin, then placed)
    sd = []
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=7, y_subdivisions=3, size=1, location=(0, 0, 0))
    leaf = bpy.context.active_object
    leaf.scale = (0.70, 0.30, 1)
    apply_all(leaf)
    xs = sorted({round(v.co.x, 5) for v in leaf.data.vertices})
    for v in leaf.data.vertices:
        x = round(v.co.x, 5)
        if x in (xs[0], xs[-1]):
            v.co.y *= 0.35
        elif x in (xs[1], xs[-2]):
            v.co.y *= 0.80
        if abs(v.co.y) < 1e-4:
            v.co.z -= 0.006
    sol = leaf.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.004
    assign(leaf, M["Leaf"])
    apply_all(leaf)
    leaf.location.z = 0.004
    shade(leaf, False)
    sd.append(leaf)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.006))
    rib = bpy.context.active_object
    rib.scale = (0.70, 0.012, 0.004)
    assign(rib, M["LeafRib"])
    apply_all(rib)
    sd.append(rib)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.07, location=(0.05, -0.04, 0.012))
    rice = bpy.context.active_object
    rice.scale = (1, 1, 0.45)
    assign(rice, M["Rice"])
    apply_all(rice)
    shade(rice, True)
    sd.append(rice)
    for x, m in zip((-0.18, -0.08, 0.02, 0.12, 0.22), ("PetalRed", "PetalGold", "PetalOchre", "Skin", "Sindoor")):
        d = ico(0.028, 1, (x, 0.07, 0.012), M[m], (1, 1, 0.5))
        shade(d, False)
        sd.append(d)
    pap = cyl(0.05, 0.004, 12, (-0.20, -0.05, 0.014), M["Pappadam"], rot=(math.radians(8), 0, 0))
    apply_all(pap)
    shade(pap, False)
    sd.append(pap)
    sad = join(sd, "Sadhya")
    sad.matrix_world = Matrix.Translation((-0.704, -0.493, 0)) @ Matrix.Rotation(math.radians(305), 4, "Z")
    bpy.ops.object.select_all(action="DESELECT")
    sad.select_set(True)
    bpy.context.view_layer.objects.active = sad
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Flicker animation (one NLA track per flame, all named "Flicker")
    base = [(0, (1, 1, 1)), (12, (0.95, 0.95, 1.12)), (24, (1.04, 1.04, 0.94)), (36, (0.98, 0.98, 1.06)),
            (48, (1, 1, 1))]

    def at(phase):
        for (f0, v0), (f1, v1) in zip(base, base[1:]):
            if f0 <= phase <= f1:
                t = (phase - f0) / (f1 - f0)
                return tuple(a + (b - a) * t for a, b in zip(v0, v1))
        return base[0][1]

    sc.render.fps = 24
    sc.frame_start, sc.frame_end = 0, 48
    for f, off in zip(flames, (0, 9, 19, 28, 38)):
        f.animation_data_create()
        for t in range(0, 49, 3):
            f.scale = at((t - off) % 48)
            f.keyframe_insert("scale", frame=t)
        act = f.animation_data.action
        act.name = f"Flicker_{f.name}"
        for fc in act.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
        track = f.animation_data.nla_tracks.new()
        track.name = "Flicker"
        track.strips.new("Flicker", 0, act)
        f.animation_data.action = None
        f.scale = (1, 1, 1)
    sc.frame_set(0)
    return flames


def tri_count():
    dg = bpy.context.evaluated_depsgraph_get()
    total = 0
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            total += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
    return total


def export(path, draco=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(path), export_format="GLB", use_selection=True, export_yup=True, export_apply=True,
        export_texcoords=False, export_normals=True, export_tangents=False, export_materials="EXPORT",
        export_animations=True, export_animation_mode="NLA_TRACKS", export_cameras=False,
        export_lights=False, export_draco_mesh_compression_enable=draco, export_extras=False)


def look_at(obj, target):
    c = obj.constraints.new("TRACK_TO")
    empty = bpy.data.objects.new(f"{obj.name}_target", None)
    bpy.context.scene.collection.objects.link(empty)
    empty.location = target
    c.target = empty
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"


def area(name, loc, size, watts, hexcol):
    ld = bpy.data.lights.new(name, "AREA")
    ld.size = size
    ld.energy = watts
    ld.color = hex_rgba(hexcol)[:3]
    o = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    look_at(o, (0, 0, 0))
    return o


def render_setup():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 64
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = hex_rgba("#2a1d14")
    world.node_tree.nodes["Background"].inputs[1].default_value = 0.3
    sc.world = world
    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 42
    cam_d.sensor_width = 36
    cam = bpy.data.objects.new("Cam", cam_d)
    sc.collection.objects.link(cam)
    cam.location = (1.350, -2.896, 1.423)
    look_at(cam, (0, 0, 0.30))
    sc.camera = cam
    area("Key", (-2.0, -2.5, 3.0), 2.0, 400, "#fff1d6")
    area("Fill", (2.5, -1.0, 1.5), 1.5, 120, "#f3d58a")
    area("Rim", (0, 3.0, 2.0), 1.5, 200, "#ffffff")
    pd = bpy.data.lights.new("FlameGlow", "POINT")
    pd.energy = 15
    pd.color = hex_rgba("#f3d58a")[:3]
    pd.shadow_soft_size = 0.05
    po = bpy.data.objects.new("FlameGlow", pd)
    sc.collection.objects.link(po)
    po.location = (0, 0, 0.72)
    # soft bloom on the flames (Eevee Next has no bloom; use the compositor)
    try:
        sc.use_nodes = True
        nt = sc.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        rl = nt.nodes.new("CompositorNodeRLayers")
        gl = nt.nodes.new("CompositorNodeGlare")
        gl.glare_type = "FOG_GLOW"
        gl.threshold = 1.0
        gl.size = 6
        comp = nt.nodes.new("CompositorNodeComposite")
        nt.links.new(rl.outputs["Image"], gl.inputs["Image"])
        nt.links.new(gl.outputs["Image"], comp.inputs["Image"])
        nt.links.new(rl.outputs["Alpha"], comp.inputs["Alpha"])
    except Exception as exc:  # compositor API differences are cosmetic only
        print("compositor glare skipped:", exc)
    return cam


def render(path, w, h, shift_x=0.0):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.camera.data.shift_x = shift_x
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    build()
    print("TRIANGLES", tri_count())
    if "--export" in ARGS:
        glb = ROOT / "assets" / "3d" / "lamp.glb"
        glb.parent.mkdir(parents=True, exist_ok=True)
        export(glb)
        print("GLB", glb, glb.stat().st_size)
        export(OUT / "lamp-draco.glb", draco=True)
        print("GLB_DRACO", (OUT / "lamp-draco.glb").stat().st_size)
    if "--render" in ARGS:
        render_setup()
        render(OUT / "lamp-lit.png", 1600, 1200)
        render(OUT / "lamp-og.png", 1200, 630, shift_x=-0.18)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "lamp.blend"))


main()
