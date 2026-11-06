import unreal as u
lib = u.MaterialEditingLibrary
m = u.load_asset('/Game/JellyGame/Art/Jelly/M_Jelly_Gummy')
names = [str(n) for n in lib.get_scalar_parameter_names(m)]
print('has star', [n for n in names if 'Star' in n or 'Edge' in n])
mi = u.load_asset('/Game/JellyGame/Art/Jelly/MI_Jelly_RedPainted')
print('mi star glint', lib.get_material_instance_scalar_parameter_value(mi, 'Star Glint'), 'edge', lib.get_material_instance_scalar_parameter_value(mi, 'Edge Line'))
print('num expr', lib.get_num_material_expressions(m))
print('cosine', [x for x in dir(u.MaterialExpressionCosine) if 'period' in x.lower()])
c = [e for e in lib.get_material_expressions(m) if isinstance(e, u.MaterialExpressionCosine)]
print('cos periods', [e.get_editor_property('period') for e in c])
