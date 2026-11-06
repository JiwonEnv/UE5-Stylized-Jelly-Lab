import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/SM_GummyBear')
sms = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
rs = sms.get_lod_reduction_settings(m, 0)
print('reduction pct tris', rs.percent_triangles, 'pct verts', getattr(rs, 'percent_vertices', None))
try:
    bs = sms.get_lod_build_settings(m, 0)
    print('build', bs.recompute_normals, bs.recompute_tangents)
except Exception as e: print('bs', e)
ns = m.get_editor_property('nanite_settings')
print('nanite fields', [x for x in dir(ns) if not x.startswith('_')][:40])
print('keep pct', getattr(ns, 'keep_percent_triangles', None), getattr(ns, 'fallback_percent_triangles', None))
