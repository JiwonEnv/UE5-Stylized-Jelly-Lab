import substance_painter as sp
t = sp.textureset.all_texture_sets()[0]
for u in (sp.textureset.MeshMapUsage.Normal, sp.textureset.MeshMapUsage.WorldSpaceNormal, sp.textureset.MeshMapUsage.AO,
          sp.textureset.MeshMapUsage.Thickness, sp.textureset.MeshMapUsage.Curvature):
    try:
        t.set_mesh_map_resource(u, None); print('cleared', u)
    except Exception as e:
        print('fail', u, e)
