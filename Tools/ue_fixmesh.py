import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/SM_GummyBear')
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
ns = m.get_editor_property('nanite_settings'); ns.enabled = False
try:
    sms.set_nanite_settings(m, ns, True); print('set_nanite_settings ok')
except Exception as e:
    print('set_nanite_settings fail', e)
bs = sms.get_lod_build_settings(m, 0)
bs.recompute_normals = True
sms.set_lod_build_settings(m, 0, bs)
print('tris now', m.get_num_triangles(0), 'nanite', m.get_editor_property('nanite_settings').enabled)
u.EditorAssetLibrary.save_loaded_asset(m)
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
for a in acts.get_all_level_actors():
    if a.get_actor_label() == 'Test Ground Cube':
        a.set_is_temporarily_hidden_in_editor(False)
        a.set_actor_hidden_in_game(False)
        a.static_mesh_component.set_visibility(True)
        a.static_mesh_component.set_material(0, u.load_asset('/Game/JellyGame/Art/Jelly/M_LookDev_Floor'))
        print('floor visible', not a.is_hidden_ed())
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
