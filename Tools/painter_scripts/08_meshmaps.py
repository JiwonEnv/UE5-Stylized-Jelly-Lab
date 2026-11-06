import substance_painter as sp
t = sp.textureset.all_texture_sets()[0]
for u in sp.textureset.MeshMapUsage.__members__.values():
    r = t.get_mesh_map_resource(u)
    print(u, r.url() if r else None)
print('uv tiles', t.has_uv_tiles(), 'meshes', t.all_mesh_names())
