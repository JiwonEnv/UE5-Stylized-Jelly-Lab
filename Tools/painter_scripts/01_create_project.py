import substance_painter as sp
MESH = 'E:/Project/Unreal-Engine-5-Jelly-Game/SourceAssets/Characters/Jelly/SM_GummyBear.obj'
if sp.project.is_open():
    sp.project.close()
s = sp.project.Settings(normal_map_format=sp.project.NormalMapFormat.DirectX,
                        default_texture_resolution=2048, import_cameras=False, mesh_unit_scale=1.0)
sp.project.create(mesh_file_path=MESH, settings=s)
print('created', sp.project.is_open(), [t.name() for t in sp.textureset.all_texture_sets()])
