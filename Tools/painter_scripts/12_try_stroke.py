import substance_painter.layerstack as ls, substance_painter.textureset as ts, substance_painter.resource as rs
import substance_painter.js as js
st = ts.all_texture_sets()[0].get_stack()
lay = [n for n in ls.get_root_layer_nodes(st) if n.get_name() == 'Brush Strokes'][0]
fx = lay.mask_effects()[0]
def rid(name):
    leaf = name.split('/')[-1]
    for q in (leaf, leaf.split('_')[1] if '_' in leaf else leaf):
        h = [r for r in rs.search(q) if r.identifier().context == 'starter_assets' and r.identifier().name == name]
        if h: return h[0].identifier()
cands = ['grunge_brushed/grunge_brushed', 'noise_messy_fibers_2/messy_fibers_2', 'grunge_wipe_brushed/grunge_wipe_brushed']
import time
for c in cands:
    r = rid(c)
    if not r: print('nf', c); continue
    fx.set_source(None, r)
    print('set', c, fx.get_source().get_parameters().get('$outputsize', ''))
    break
