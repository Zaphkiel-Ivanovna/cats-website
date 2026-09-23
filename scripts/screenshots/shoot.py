import inspect
import json
import math
import os
import shutil

import bpy
from mathutils import Euler, Vector

PKG = "bl_ext.user_default.cats_blender_plugin"
WORK = os.environ["CATS_WORK"]
ONLY = [s for s in os.environ.get("CATS_ONLY", "").split(",") if s]
CROPS = {}

MAIN_BEFORE = [
    "J_Bip_C_Hips", "J_Bip_C_Spine", "J_Bip_C_Chest", "J_Bip_C_UpperChest", "J_Bip_C_Neck", "J_Bip_C_Head",
    "J_Bip_L_UpperArm", "J_Bip_L_Hand",
    "J_Bip_L_UpperLeg", "J_Bip_L_LowerLeg", "J_Bip_L_Foot",
]
MAIN_AFTER = [
    "Hips", "Spine", "Chest", "Upper Chest", "Neck", "Head",
    "Left arm", "Left wrist",
    "Left leg", "Left knee", "Left ankle",
]


def log(*args):
    print("[shot]", *args, flush=True)


def win():
    return bpy.context.window_manager.windows[0]


def view_area():
    return max((a for a in win().screen.areas if a.type == "VIEW_3D"), key=lambda a: a.width * a.height)


def region(area, kind):
    return next(r for r in area.regions if r.type == kind)


def override(**extra):
    w = win()
    area = view_area()
    return bpy.context.temp_override(window=w, screen=w.screen, area=area,
                                     region=region(area, "WINDOW"), **extra)


def armature():
    return next(o for o in bpy.data.objects if o.type == "ARMATURE")


def meshes():
    return [o for o in bpy.data.objects if o.type == "MESH" and o.parent and o.parent.type == "ARMATURE"]


def _panel_classes():
    found, stack = [], list(bpy.types.Panel.__subclasses__())
    while stack:
        cls = stack.pop()
        found.append(cls)
        stack.extend(cls.__subclasses__())
    return found


def _is_sidebar(cls):
    return getattr(cls, "bl_space_type", "") == "VIEW_3D" and getattr(cls, "bl_region_type", "") == "UI"


CATS_PANELS = {}


def hide_builtin_sidebar():
    others = [c for c in _panel_classes()
              if _is_sidebar(c) and not c.__module__.startswith(PKG) and c.is_registered]
    for cls in sorted(others, key=lambda c: 0 if getattr(c, "bl_parent_id", "") else 1):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    for name in dir(bpy.types):
        cls = getattr(bpy.types, name)
        if name.startswith("VIEW3D_PT_") and isinstance(cls, type) and _is_sidebar(cls) \
                and not getattr(cls, "__module__", "").startswith(PKG):
            try:
                bpy.utils.unregister_class(cls)
            except (RuntimeError, ValueError):
                pass
    for cls in _panel_classes():
        if _is_sidebar(cls) and cls.__module__.startswith(PKG):
            CATS_PANELS[cls.bl_idname] = cls


SHOWN = []
_round = [0]


def show_panels(*idnames, only=None):
    for cls in reversed(SHOWN):
        bpy.utils.unregister_class(cls)
    SHOWN.clear()
    for cls in sorted(CATS_PANELS.values(), key=lambda c: 0 if getattr(c, "bl_parent_id", "") else 1):
        if cls.is_registered:
            bpy.utils.unregister_class(cls)
    _round[0] += 1
    suffix = f"_shot{_round[0]}"
    for idname in idnames:
        children = sorted((c for c in CATS_PANELS.values() if getattr(c, "bl_parent_id", "") == idname
                           and (only is None or c.bl_idname in only)),
                          key=lambda c: inspect.getsourcelines(c)[1])
        for cls in [CATS_PANELS[idname]] + children:
            attrs = {"bl_idname": cls.bl_idname + suffix,
                     "bl_options": set(getattr(cls, "bl_options", set())) - {"DEFAULT_CLOSED"}}
            if getattr(cls, "bl_parent_id", ""):
                attrs["bl_parent_id"] = cls.bl_parent_id + suffix
            shot = type(cls.__name__ + suffix, (cls,), attrs)
            bpy.utils.register_class(shot)
            SHOWN.append(shot)


def style_viewport(shading="MATERIAL", sidebar=True):
    area = view_area()
    space = area.spaces[0]
    space.shading.type = shading
    if shading == "SOLID":
        space.shading.light = "STUDIO"
        space.shading.color_type = "MATERIAL"
    space.show_region_ui = sidebar
    space.show_region_toolbar = False
    space.show_gizmo_navigate = False
    space.overlay.show_text = shading == "SOLID"
    space.overlay.show_stats = False
    space.overlay.show_cursor = False
    space.overlay.show_extras = shading == "SOLID"
    space.overlay.show_outline_selected = False
    space.overlay.show_axis_x = False
    space.overlay.show_axis_y = False
    space.overlay.show_floor = True


def frame(focus=(0.0, 0.0, 0.8), distance=2.6, yaw=24.0, pitch=84.0, ortho=False):
    r3d = view_area().spaces[0].region_3d
    r3d.view_perspective = "ORTHO" if ortho else "PERSP"
    r3d.view_location = Vector(focus)
    r3d.view_distance = distance
    r3d.view_rotation = Euler((math.radians(pitch), 0.0, math.radians(yaw))).to_quaternion()


def body_bounds():
    pts = [ob.matrix_world @ Vector(c) for ob in meshes() for c in ob.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    return lo, hi


def deselect_all():
    for ob in bpy.data.objects:
        ob.select_set(False)
    bpy.context.view_layer.objects.active = None


def show_bones(names):
    arm = armature()
    arm.show_in_front = True
    arm.data.display_type = "OCTAHEDRAL"
    arm.data.show_names = True
    arm.hide_set(False)
    keep = set(names)
    for bone in arm.data.bones:
        bone.hide = bone.name not in keep
    for pbone in arm.pose.bones:
        if hasattr(pbone, "hide"):
            pbone.hide = pbone.name not in keep
    missing = keep - {b.name for b in arm.data.bones}
    if missing:
        log("missing bones", sorted(missing))


def rect_of(obj):
    return {"x": obj.x, "y": obj.y, "w": obj.width, "h": obj.height}


def grab(name, target="area", trim=False, frac=None, right_inset=0):
    path = os.path.join(WORK, f"{name}.png")
    with override():
        bpy.ops.screen.screenshot(filepath=path, check_existing=False)
    area = view_area()
    rect = rect_of(region(area, "UI")) if target == "sidebar" else rect_of(area)
    if target == "viewport":
        rect = rect_of(region(area, "WINDOW"))
    if frac:
        x0, y0, x1, y1 = frac
        rect = {"x": rect["x"] + int(rect["w"] * x0), "y": rect["y"] + int(rect["h"] * y0),
                "w": int(rect["w"] * (x1 - x0)), "h": int(rect["h"] * (y1 - y0))}
    rect["w"] -= right_inset
    CROPS[name] = {"raw": path, "rect": rect, "trim": trim}
    log("grabbed", name, rect)


def wanted(name):
    return not ONLY or any(o in name for o in ONLY)


def restore_shape_key_names(glb):
    import struct
    with open(glb, "rb") as fh:
        data = fh.read()
    length = struct.unpack("<I", data[12:16])[0]
    gltf = json.loads(data[20:20 + length])
    by_node = {n["name"]: gltf["meshes"][n["mesh"]] for n in gltf["nodes"] if "mesh" in n}
    for ob in meshes():
        mesh = by_node.get(ob.name)
        keys = ob.data.shape_keys
        if not mesh or not keys:
            continue
        names = (mesh["primitives"][0].get("extras") or {}).get("targetNames") or []
        for i, name in enumerate(names):
            block = keys.key_blocks.get(f"target_{i}")
            if block:
                block.name = name[name.find("Fcl_"):] if "Fcl_" in name else name
        log("restored", len(names), "shape key names on", ob.name)


def step_import():
    bpy.ops.preferences.addon_enable(module=PKG)
    glb = os.path.join(WORK, "model.glb")
    shutil.copy(os.environ["CATS_MODEL"], glb)
    bpy.ops.import_scene.gltf(filepath=glb, disable_bone_shape=True)
    log("objects", [(o.name, o.type, o.parent.name if o.parent else None) for o in bpy.data.objects])
    restore_shape_key_names(glb)
    deselect_all()
    stray = [o for o in bpy.data.objects if o.type == "MESH" and not o.parent]
    for ob in stray:
        ob.select_set(True)
    if stray:
        with override():
            bpy.ops.object.delete()
    bpy.context.scene.armature = armature().name
    with override():
        bpy.ops.screen.screen_full_area()
    hide_builtin_sidebar()
    view_area().spaces[0].show_region_ui = True
    log("imported", armature().name, [m.name for m in meshes()])


def set_sidebar_width(units):
    import ctypes
    area = view_area()
    ui = region(area, "UI")
    field = ctypes.c_short.from_address(ui.as_pointer() + 198)
    expected = round(ui.width / bpy.context.preferences.system.pixel_size)
    if abs(field.value - expected) > 1:
        log("sidebar width field not found, keeping default width")
        return
    field.value = units
    area.spaces[0].show_region_ui = False


def show_sidebar():
    view_area().spaces[0].show_region_ui = True


def step_bones(names):
    def run():
        bpy.context.preferences.view.ui_scale = 1.6
        style_viewport("SOLID", sidebar=False)
        deselect_all()
        show_bones(names)
        lo, hi = body_bounds()
        height = hi.z - lo.z
        frame(focus=(-(hi.x - lo.x) * 0.2, 0.0, lo.z + height * 0.5), distance=height * 1.4, yaw=180, pitch=90,
              ortho=True)
    return run


def reset_scale():
    bpy.context.preferences.view.ui_scale = 1.0


def step_fix():
    reset_scale()
    arm = armature()
    for bone in arm.data.bones:
        bone.hide = False
    for pbone in arm.pose.bones:
        if hasattr(pbone, "hide"):
            pbone.hide = False
    with override():
        result = bpy.ops.cats_armature.fix()
    log("fix", result, [m.name for m in meshes()])


def step_hero():
    reset_scale()
    style_viewport("MATERIAL", sidebar=True)
    deselect_all()
    armature().hide_set(True)
    show_panels("VIEW3D_PT_quickaccess_v3", "VIEW3D_PT_mmdoptions_stuff")
    lo, hi = body_bounds()
    height = hi.z - lo.z
    frame(focus=(-0.12, 0.0, lo.z + height * 0.5), distance=height * 1.15, yaw=180 + 28, pitch=86)


STEPS = [
    (step_import, 2.0),
    (lambda: set_sidebar_width(360), 0.3),
    (show_sidebar, 0.5),
]
if wanted("bones"):
    STEPS += [
        (step_bones(MAIN_BEFORE), 1.5),
        (lambda: grab("bones-before", "viewport", frac=(0.3, 0.4, 0.74, 0.95)), 0.5),
    ]
STEPS += [(step_fix, 2.0)]
if wanted("bones"):
    STEPS += [
        (step_bones(MAIN_AFTER), 1.5),
        (lambda: grab("bones-after", "viewport", frac=(0.3, 0.4, 0.74, 0.95)), 0.5),
    ]
if wanted("hero"):
    STEPS += [
        (step_hero, 6.0),
        (lambda: grab("hero", "area"), 0.5),
    ]


def enum_pick(prop, *candidates):
    scene = bpy.context.scene
    for cand in candidates:
        try:
            setattr(scene, prop, cand)
            return cand
        except TypeError:
            continue
    log("no candidate for", prop, candidates)
    return None


def shape_key(*needles):
    body = next(m for m in meshes() if m.data.shape_keys)
    for needle in needles:
        for key in body.data.shape_keys.key_blocks:
            if needle.lower() == key.name.lower() or key.name.lower().endswith(needle.lower()):
                return key.name
    return None


def panel_setup(*idnames, before=None, only=None):
    def run():
        reset_scale()
        style_viewport("MATERIAL", sidebar=True)
        deselect_all()
        armature().hide_set(True)
        if before:
            before()
        show_panels(*idnames, only=only)
    return run


def prep_visemes():
    body = next(m for m in meshes() if m.data.shape_keys)
    log("shape keys", [k.name for k in body.data.shape_keys.key_blocks][:60])
    enum_pick("mesh_name_viseme", body.name)
    enum_pick("mouth_a", shape_key("MTH A", "Fcl_MTH_A"))
    enum_pick("mouth_o", shape_key("MTH O", "Fcl_MTH_O"))
    enum_pick("mouth_ch", shape_key("MTH I", "Fcl_MTH_I"))


def prep_eyes():
    arm = armature()
    arm.hide_set(False)
    bpy.context.view_layer.objects.active = arm
    enum_pick("head", "Head")
    enum_pick("eye_left", "Eye_L")
    enum_pick("eye_right", "Eye_R")


def prep_settings():
    bpy.context.scene.custom_translate_csv_export_dir = "~/Documents/Cats"


def prep_more():
    bpy.context.scene.show_more_options = True


OPT, EYE = "VIEW3D_PT_optimize_v3", "VIEW3D_PT_eye_tracking_v3"
PANELS = [
    ("panel-quick-access", ["VIEW3D_PT_quickaccess_v3"], None, None),
    ("panel-optimization-atlas", [OPT], None, ["VIEW3D_PT_optimize_atlas_v3"]),
    ("panel-optimization-materials", [OPT], None, ["VIEW3D_PT_optimize_material_v3"]),
    ("panel-optimization-bones", [OPT], None, ["VIEW3D_PT_optimize_bonemerging_v3"]),
    ("panel-mmd-options", ["VIEW3D_PT_mmdoptions_stuff"], None, None),
    ("panel-other-options", ["VIEW3D_PT_OtherOptionsPanel_v3"], prep_more, None),
    ("panel-visemes", ["VIEW3D_PT_viseme_v3"], prep_visemes, None),
    ("panel-bone-parenting", ["VIEW3D_PT_boneroot_v3"], None, None),
    ("panel-model-scaling", ["VIEW3D_PT_scale_v2"], None, None),
    ("panel-eye-sdk3", [EYE], prep_eyes, ["VIEW3D_PT_eye_tracking_sdk3_v3"]),
    ("panel-eye-legacy", [EYE], prep_eyes, ["VIEW3D_PT_eye_tracking_legacy_v3"]),
    ("panel-settings", ["VIEW3D_PT_updater_v3"], prep_settings, None),
]
for name, ids, before, only in PANELS:
    if wanted(name):
        inset = 44 if before is prep_eyes else 0
        STEPS += [
            (panel_setup(*ids, before=before, only=only), 1.0),
            ((lambda n=name, i=inset: grab(n, "sidebar", trim=True, right_inset=i)), 0.3),
        ]


def step_visemes_create():
    prep_visemes()
    with override():
        result = bpy.ops.cats_viseme.create()
    log("visemes", result)


def face_shot(key_name):
    def run():
        style_viewport("MATERIAL", sidebar=False)
        deselect_all()
        armature().hide_set(True)
        body = next(m for m in meshes() if m.data.shape_keys)
        for key in body.data.shape_keys.key_blocks:
            key.value = 1.0 if key.name == key_name else 0.0
        arm = armature()
        head = arm.matrix_world @ arm.pose.bones["Head"].head
        frame(focus=(head.x, head.y, head.z + 0.07), distance=0.42, yaw=180, pitch=90)
    return run


if wanted("viseme-faces"):
    STEPS += [(step_visemes_create, 2.0)]
    for key in ("vrc.v_aa", "vrc.v_oh", "vrc.v_ch"):
        STEPS += [
            (face_shot(key), 3.0),
            ((lambda k=key: grab("face-" + k.split("_")[-1], "viewport", frac=(0.3, 0.05, 0.7, 0.95))), 0.3),
        ]


def finish():
    with open(os.path.join(WORK, "crops.json"), "w") as fh:
        json.dump(CROPS, fh, indent=1)
    log("done", len(CROPS))
    bpy.ops.wm.quit_blender()


def runner():
    if not STEPS:
        finish()
        return None
    fn, delay = STEPS.pop(0)
    try:
        fn()
    except Exception:
        import traceback
        log("ERROR in", getattr(fn, "__name__", fn))
        traceback.print_exc()
    return delay


bpy.app.timers.register(runner, first_interval=1.0)
