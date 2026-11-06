import substance_painter as sp
t = sp.textureset.all_texture_sets()[0]
p = sp.baking.BakingParameters.from_texture_set(t)
print('COMMON', {k: str(v.value()) for k, v in p.common().items()})
print('ENABLED', p.get_enabled_bakers())
for u in (sp.baking.MeshMapUsage.Thickness, sp.baking.MeshMapUsage.Curvature, sp.baking.MeshMapUsage.AO):
    print(u, {k: str(v.value()) for k, v in p.baker(u).items()})
print(list(sp.baking.MeshMapUsage))
