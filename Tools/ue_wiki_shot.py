"""UE-side helper for capturing wiki images (driven by Tools/capture_wiki_images.py).

Reads Saved/wiki_shot.json:
  {"action": "setup"}                         temp MI + temp bear 'Jelly_Bear_Sweep' (alone, off to the side)
  {"action": "set", "base": "MI_Jelly_Raspberry", "params": {...}, "stencil": false}
                                              temp MI = base preset's values + params, applied to the temp bear
  {"action": "assign", "mi": "MI_Jelly_RedPainted", "stencil": true}
                                              put an existing instance on the temp bear (gallery)
  {"action": "teardown"}                      remove temp bear and temp assets
Nothing here saves the level; existing instances are only read.
"""
import json
import os
import unreal as u

P = json.load(open(os.path.join(u.Paths.project_dir(), 'Saved', 'wiki_shot.json'), encoding='utf-8'))
lib = u.MaterialEditingLibrary
eal = u.EditorAssetLibrary
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
INST = '/Game/JellyGame/Art/Materials/Jelly/Instances/'
JELLY = '/Game/JellyGame/Art/Materials/Jelly/'


def mi_path(n):
    return JELLY + n if '/' in n else INST + n
MASTER = '/Game/JellyGame/Art/Materials/Jelly/M_Jelly_Gummy'
TMP = '/Game/__WikiTemp'
TMP_MI = f'{TMP}/MI_Wiki_Sweep'
LABEL = 'Jelly_Bear_Sweep'
STUDIO = (0.0, 3000.0)   # far from the look-dev floor


def build_studio():
    # floor + back wall + two side walls (no shadows), neutral matte grey
    cube = u.load_asset('/Engine/BasicShapes/Cube')
    mat = u.load_asset('/Game/JellyGame/Art/Materials/LookDev/M_LookDev_Floor')
    x0, y0 = STUDIO
    parts = {  # name: (center, scale in metres since the cube is 100cm)
        'Floor': ((x0, y0, -5), (10, 10, 0.1)),
        'Back': ((x0 - 220, y0, 220), (0.1, 10, 4.6)),
        'Left': ((x0 + 100, y0 - 380, 220), (8, 0.1, 4.6)),
        'Right': ((x0 + 100, y0 + 380, 220), (8, 0.1, 4.6)),
    }
    for n, (c, sc) in parts.items():
        w = acts.spawn_actor_from_object(cube, u.Vector(*c), u.Rotator(0, 0, 0))
        w.set_actor_label('Wiki_Studio_' + n)
        w.set_actor_scale3d(u.Vector(*sc))
        w.static_mesh_component.set_material(0, mat)
        w.static_mesh_component.set_cast_shadow(False)
    # soft shadowless fill light from the camera side so the walls are not black
    fill = acts.spawn_actor_from_class(u.PointLight, u.Vector(x0 + 260, y0, 230), u.Rotator(0, 0, 0))
    fill.set_actor_label('Wiki_Studio_Fill')
    lc = fill.get_component_by_class(u.PointLightComponent)
    lc.set_intensity(60.0)
    lc.set_attenuation_radius(2000.0)
    lc.set_cast_shadows(False)


def bear():
    return next((a for a in acts.get_all_level_actors() if a.get_actor_label() == LABEL), None)


def apply(a, mat):
    # same jelly material on every part of the model
    for i in range(a.static_mesh_component.get_num_materials()):
        a.static_mesh_component.set_material(i, mat)


def set_stencil(a, on):
    a.static_mesh_component.set_render_custom_depth(bool(on))
    a.static_mesh_component.set_custom_depth_stencil_value(1 if on else 0)


act = P['action']
if act == 'setup':
    if not eal.does_asset_exist(TMP_MI):
        mi = u.AssetToolsHelpers.get_asset_tools().create_asset('MI_Wiki_Sweep', TMP, u.MaterialInstanceConstant,
                                                               u.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mi, u.load_asset(MASTER))
    if not bear():
        # user's bear model; copy transform/materials from the placed 'Gummy_UV_Fixed' actor
        ref = next(a for a in acts.get_all_level_actors() if a.get_actor_label() == 'Gummy_UV_Fixed')
        a = acts.spawn_actor_from_object(u.load_asset('/Game/JellyGame/Art/Characters/Jelly/Gummy_UV_Fixed'),
                                         u.Vector(STUDIO[0], STUDIO[1], ref.get_actor_location().z), ref.get_actor_rotation())
        a.set_actor_label(LABEL)
        for i, m in enumerate(ref.static_mesh_component.get_materials()):
            a.static_mesh_component.set_material(i, m)
    if not any(f.get_actor_label().startswith('Wiki_Studio_') for f in acts.get_all_level_actors()):
        build_studio()
    print('setup ok')
elif act == 'set':
    mi = u.load_asset(TMP_MI)
    lib.clear_all_material_instance_parameters(mi)
    base = u.load_asset(mi_path(P['base'])) if P.get('base') else None
    for p in (base.get_editor_property('scalar_parameter_values') if base else []):
        lib.set_material_instance_scalar_parameter_value(mi, str(p.parameter_info.name), p.parameter_value)
    for p in (base.get_editor_property('vector_parameter_values') if base else []):
        lib.set_material_instance_vector_parameter_value(mi, str(p.parameter_info.name), p.parameter_value)
    for k, v in P.get('params', {}).items():
        if isinstance(v, list):
            lib.set_material_instance_vector_parameter_value(mi, k, u.LinearColor(*v, 1))
        else:
            lib.set_material_instance_scalar_parameter_value(mi, k, float(v))
    lib.update_material_instance(mi)
    a = bear()
    apply(a, mi)
    set_stencil(a, P.get('stencil', False))
    print('set', P['base'], P.get('params'))
elif act == 'assign':
    a = bear()
    apply(a, u.load_asset(mi_path(P['mi'])))
    set_stencil(a, P.get('stencil', False))
    print('assign', P['mi'])
elif act == 'teardown':
    a = bear()
    if a:
        acts.destroy_actor(a)
    if eal.does_directory_exist(TMP):
        eal.delete_directory(TMP)
    for f in acts.get_all_level_actors():
        if f.get_actor_label().startswith('Wiki_Studio_'):
            acts.destroy_actor(f)
    print('teardown ok', not eal.does_directory_exist(TMP))
