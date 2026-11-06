import unreal as u
lib = u.MaterialEditingLibrary
m = u.load_asset('/Game/JellyGame/Art/Jelly/M_PP_JellyPaintFilter')
mi = u.load_asset('/Game/JellyGame/Art/Jelly/MI_PP_Test') or u.AssetToolsHelpers.get_asset_tools().create_asset('MI_PP_Test', '/Game/JellyGame/Art/Jelly', u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
lib.set_material_instance_parent(mi, m)
lib.set_material_instance_scalar_parameter_value(mi, 'Ignore Stencil', 1.0)
lib.set_material_instance_scalar_parameter_value(mi, 'Brush Radius', 8.0)
lib.update_material_instance(mi)
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() == 'Jelly_PaintFilter_PPV':
        st = a.get_editor_property('settings')
        wb = u.WeightedBlendable(); wb.set_editor_property('weight', 1.0); wb.set_editor_property('object', mi)
        wbs = u.WeightedBlendables(); wbs.set_editor_property('array', [wb]); st.set_editor_property('weighted_blendables', wbs)
        a.set_editor_property('settings', st); print('pp set to test MI', a.get_editor_property('unbound'), a.get_editor_property('enabled') if True else '')
