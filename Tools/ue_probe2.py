import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/SM_GummyBear')
ns = m.get_editor_property('nanite_settings')
print('nanite', ns.enabled, 'lods', m.get_num_lods(), 'tris lod0', m.get_num_triangles(0))
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
for a in acts.get_all_level_actors():
    if isinstance(a, u.StaticMeshActor) and not a.get_actor_label().startswith('Jelly_'):
        o, e = a.get_actor_bounds(False)
        print('SMA', a.get_actor_label(), a.static_mesh_component.static_mesh.get_name() if a.static_mesh_component.static_mesh else None, e)
    elif not isinstance(a, u.StaticMeshActor):
        print('actor', a.get_class().get_name(), a.get_actor_label())
