"""Make a copy of the InnerGlitter_Restored material whose textures can be swapped per instance.

The original material samples its 5 textures with plain TextureSample nodes (fixed). This copy keeps
every node and connection as-is and plugs a TextureObjectParameter into each sample's `Tex` input, so
the texture becomes an instance parameter. (Rewiring the outputs is avoided on purpose: querying
expression input names crashed UE 5.8.4's MaterialEditor from Python.)

Originals are not modified:
  M_Jelly_Gummy_RedPainted_InnerGlitter_Restored  -> M_Jelly_Gummy_RedPainted_InnerGlitter_TexParam
  MI_Jelly_RedPainted_InnerGlitter_Restored       -> MI_Jelly_RedPainted_InnerGlitter_TexParam
"""
import unreal as u

lib = u.MaterialEditingLibrary
eal = u.EditorAssetLibrary
BASE = '/Game/JellyGame/Art/Materials/Jelly'
SRC_M = f'{BASE}/M_Jelly_Gummy_RedPainted_InnerGlitter_Restored'
SRC_MI = f'{BASE}/Instances/MI_Jelly_RedPainted_InnerGlitter_Restored'
DST_M = f'{BASE}/M_Jelly_Gummy_RedPainted_InnerGlitter_TexParam'
DST_MI = f'{BASE}/Instances/MI_Jelly_RedPainted_InnerGlitter_TexParam'

# texture asset name -> (parameter name, group)  — names match M_Jelly_Gummy where possible
PARAMS = {
    'T_GummyBear_BC': 'BaseColor Tint',
    'T_GummyBear_Mask': 'Mask',
    'T_GummyBear_N_SoftRippleVaried': 'Normal',
    'T_GummyBear_PaintBroadTile': 'Paint Mask',
    'T_GummyBear_BrushBroadTile': 'Brush Strokes',
}

for p in (DST_M, DST_MI):
    if eal.does_asset_exist(p):
        raise RuntimeError(f'{p} already exists; delete or rename it first')

m = eal.duplicate_asset(SRC_M, DST_M)
samples = [e for e in lib.get_material_expressions(m) if type(e) is u.MaterialExpressionTextureSample]
made = {}
for s in samples:
    tex = s.get_editor_property('texture')
    if tex is None or tex.get_name() not in PARAMS:
        print('skip', s.get_name(), tex.get_name() if tex else None)
        continue
    name = PARAMS[tex.get_name()]
    if name not in made:
        x, y = lib.get_material_expression_node_position(s)
        obj = lib.create_material_expression(m, u.MaterialExpressionTextureObjectParameter, x - 260, y)
        obj.set_editor_property('parameter_name', name)
        obj.set_editor_property('group', 'Textures')
        obj.set_editor_property('texture', tex)
        obj.set_editor_property('sampler_type', s.get_editor_property('sampler_type'))
        made[name] = obj
    if not lib.connect_material_expressions(made[name], '', s, 'Tex'):
        raise RuntimeError(f'could not connect {name} -> {s.get_name()}.Tex')
    print('param', name, '->', s.get_name())

lib.recompile_material(m)
eal.save_loaded_asset(m)

mi = eal.duplicate_asset(SRC_MI, DST_MI)
lib.set_material_instance_parent(mi, m)
lib.update_material_instance(mi)
eal.save_loaded_asset(mi)

st_old = lib.get_statistics(u.load_asset(SRC_M))
st_new = lib.get_statistics(m)
print('texture params:', [str(n) for n in lib.get_texture_parameter_names(m)])
print('PS instructions old/new:', st_old.num_pixel_shader_instructions, st_new.num_pixel_shader_instructions,
      '| samplers old/new:', st_old.num_samplers, st_new.num_samplers)
print('MI parent:', mi.get_editor_property('parent').get_name(),
      '| MI scalar overrides kept:', len(mi.get_editor_property('scalar_parameter_values')))
