import unreal as u, json, os
P = json.load(open(os.path.join(u.Paths.project_dir(), 'Saved', 'jelly_mi.json')))
lib = u.MaterialEditingLibrary
mi = u.load_asset('/Game/JellyGame/Art/Jelly/' + P['mi'])
for k, v in P['params'].items():
    if isinstance(v, list): lib.set_material_instance_vector_parameter_value(mi, k, u.LinearColor(*v, 1))
    else: lib.set_material_instance_scalar_parameter_value(mi, k, v)
lib.update_material_instance(mi); mi.modify(); u.EditorAssetLibrary.save_loaded_asset(mi); print('set', P['mi'], P['params'])
