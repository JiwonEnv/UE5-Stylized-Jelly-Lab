import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/SM_GummyBear')
print('nanite', m.get_editor_property('nanite_settings').enabled, 'tris', m.get_num_triangles(0), 'lods', m.get_num_lods())
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
print('world', w.get_name())
for a in acts.get_all_level_actors():
    if isinstance(a, u.StaticMeshActor):
        c = a.static_mesh_component
        print(a.get_actor_label(), c.static_mesh.get_name() if c.static_mesh else None, [mm.get_name() if mm else None for mm in c.get_materials()], a.get_actor_location(), a.is_hidden_ed())
fm = u.load_asset('/Game/JellyGame/Art/Jelly/M_LookDev_Floor')
print('floor expr', u.MaterialEditingLibrary.get_num_material_expressions(fm))
