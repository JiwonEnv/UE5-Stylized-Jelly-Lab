import substance_painter as sp
B = sp.baking
t = sp.textureset.all_texture_sets()[0]
p = B.BakingParameters.from_texture_set(t)
c = p.common(); th = p.baker(B.MeshMapUsage.Thickness); ao = p.baker(B.MeshMapUsage.AO)
p.set({c['OutputSize']: (11, 11), c['LowAsHigh']: True, th['MaxDistance']: 0.3, ao['MaxDistance']: 0.4})
p.set_textureset_enabled(True)
p.set_enabled_bakers([B.MeshMapUsage.AO, B.MeshMapUsage.Curvature, B.MeshMapUsage.Position,
                      B.MeshMapUsage.Thickness, B.MeshMapUsage.WorldSpaceNormal, B.MeshMapUsage.Normal])
print('enabled', p.get_enabled_bakers(), 'ts enabled', p.is_textureset_enabled())
print('LowAsHigh', p.common()['LowAsHigh'].value())
import builtins
builtins._jelly_bake_done = None
def done(e):
    builtins._jelly_bake_done = str(getattr(e, 'status', e))
sp.event.DISPATCHER.connect(sp.event.BakingProcessEnded, done)
B.bake_async(t)
print('bake started')
