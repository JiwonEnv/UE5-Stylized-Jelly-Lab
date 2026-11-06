# Runs inside Substance 3D Painter 12 (via sp_run.py). Builds the gummy-jelly layer stack.
# Channels: BaseColor = whitish tint/variation (UE multiplies the jelly colour on top)
#           Height     = soft lumps + drips (-> Normal_DirectX on export)
#           Roughness  = glassy base + smudges (Painter preview)
#           User0      = suspended bubbles mask      User1 = smudge mask
import substance_painter as sp
from substance_painter import layerstack as ls, resource as rs, textureset as ts
import os, struct, zlib

# Legacy colour-managed projects reject uniform colours from the Python API (Painter 12.2),
# so channel values are fed as tiny solid bitmaps imported as project resources.
SWATCH_DIR = 'E:/Project/Unreal-Engine-5-Jelly-Game/SourceAssets/Characters/Jelly/PainterSwatches'
os.makedirs(SWATCH_DIR, exist_ok=True)
_swatch_cache = {}


def _png(path, rgb):
    w = h = 8
    row = bytes([0]) + bytes(rgb) * w
    raw = row * h
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    sig = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    data = sig + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')
    open(path, 'wb').write(data)


def Color(r, g, b):
    return ('rgb', (r, g, b))


def swatch(v):
    rgb = v[1] if isinstance(v, tuple) else (v, v, v)
    key = tuple(int(round(max(0, min(1, c)) * 255)) for c in rgb)
    if key not in _swatch_cache:
        path = f'{SWATCH_DIR}/sw_{key[0]:03d}_{key[1]:03d}_{key[2]:03d}.png'
        if not os.path.exists(path):
            _png(path, key)
        r = rs.import_project_resource(path, rs.Usage.TEXTURE)
        _swatch_cache[key] = r.identifier()
    return _swatch_cache[key]

CT = ls.ChannelType
BAKED_DIR = 'E:/Project/Unreal-Engine-5-Jelly-Game/SourceAssets/Characters/Jelly/MeshMaps'


def baked(name):
    return rs.import_project_resource(f'{BAKED_DIR}/GummyBear_{name}.png', rs.Usage.TEXTURE).identifier()

tset = ts.all_texture_sets()[0]
stack = tset.get_stack()


def res(name):
    leaf = name.split('/')[-1]
    words = [w for w in leaf.replace('mg_', '').split('_') if w and not w.isdigit()]
    queries = [leaf, ' '.join(words), words[0] if words else leaf] + words
    hits = []
    for q in queries:
        hits = [r for r in rs.search(q) if r.identifier().context == 'starter_assets' and r.identifier().name == name]
        if hits:
            break
    if not hits:
        raise RuntimeError('resource not found: ' + name)
    return hits[0].identifier()


for ch, fmt, label in ((CT.User0, ts.ChannelFormat.L8, 'Bubbles'), (CT.User1, ts.ChannelFormat.L8, 'Smudge'),
                       (CT.User2, ts.ChannelFormat.L16, 'Thickness'),
                       (CT.User4, ts.ChannelFormat.L8, 'BrushStrokes'), (CT.User5, ts.ChannelFormat.L8, 'PaintDabs')):
    if not stack.has_channel(ch):
        stack.add_channel(ch, fmt, label)
for ch, fmt in ((CT.Height, ts.ChannelFormat.L16F), (CT.Roughness, ts.ChannelFormat.L8)):
    if not stack.has_channel(ch):
        stack.add_channel(ch, fmt)

if stack.has_channel(CT.User3):
    stack.remove_channel(CT.User3)  # curvature data was never used in UE

with ls.ScopedModification('Jelly stack'):
    for n in ls.get_root_layer_nodes(stack):
        ls.delete_node(n)

    def top():
        roots = ls.get_root_layer_nodes(stack)
        return ls.InsertPosition.above_node(roots[0]) if roots else ls.InsertPosition.from_textureset_stack(stack)

    def fill(name, values, opacity=None):
        """values: {ChannelType: float|Color}; only these channels are active."""
        layer = ls.insert_fill(top())
        layer.set_name(name)
        layer.active_channels = set(values)
        for ch, v in values.items():
            layer.set_source(ch, swatch(v))
            if opacity is not None:
                layer.set_opacity(opacity, ch)
        return layer

    def mask_fill(layer, resource, params=None, triplanar=False, opacity=1.0, blend=None):
        if not layer.has_mask():
            layer.add_mask(ls.MaskBackground.Black)
        mstack = layer.mask_effects()
        pos = ls.InsertPosition.above_node(mstack[0]) if mstack else ls.InsertPosition.inside_node(layer, ls.NodeStack.Mask)
        fx = ls.insert_fill(pos)
        src = fx.set_source(None, resource)
        if params:
            try:
                src.set_parameters(params)
            except Exception as e:
                print('  param warn', layer.get_name(), e)
        if triplanar:
            fx.set_projection_mode(ls.ProjectionMode.Triplanar)
        if blend is not None:
            fx.set_blending_mode(blend)
        fx.set_opacity(opacity)
        return fx

    def mask_generator(layer, resource, params=None, blend=None, opacity=1.0):
        if not layer.has_mask():
            layer.add_mask(ls.MaskBackground.Black)
        mstack = layer.mask_effects()
        pos = ls.InsertPosition.above_node(mstack[0]) if mstack else ls.InsertPosition.inside_node(layer, ls.NodeStack.Mask)
        g = ls.insert_generator_effect(pos, resource)
        if params:
            try:
                g.get_source().set_parameters(params)
            except Exception as e:
                print('  gen param warn', layer.get_name(), e)
        if blend is not None:
            g.set_blending_mode(blend)
        g.set_opacity(opacity)
        return g

    def levels(layer, lo, hi):
        mstack = layer.mask_effects()
        lv = ls.insert_levels_effect(ls.InsertPosition.above_node(mstack[0]))
        try:
            p = lv.get_parameters() if hasattr(lv, 'get_parameters') else None
            if p is not None:
                p.input_min, p.input_max = lo, hi
                lv.set_parameters(p)
        except Exception as e:
            print('  levels warn', layer.get_name(), e)
        return lv

    report = []

    def step(name, fn):
        try:
            fn(); report.append(name + ' OK')
        except Exception as e:
            report.append(f'{name} FAIL {type(e).__name__}: {e}')

    # 1. base
    step('Jelly Base', lambda: fill('Jelly Base', {CT.BaseColor: Color(0.98, 0.97, 0.97), CT.Roughness: 0.04,
                                                   CT.Height: 0.0, CT.User0: 0.0, CT.User1: 0.0,
                                                   CT.User4: 0.0, CT.User5: 0.0}))

    # 2. soft colour clouds (lavender / warm variation like the painted gummy refs)
    def colour_clouds():
        l = fill('Color Clouds Cool', {CT.BaseColor: Color(0.80, 0.78, 0.95)}, opacity=0.55)
        mask_fill(l, res('noise_clouds_2/clouds_2'), triplanar=True)
        l2 = fill('Color Clouds Warm', {CT.BaseColor: Color(1.0, 0.88, 0.80)}, opacity=0.45)
        mask_fill(l2, res('noise_clouds_3/clouds_3'), triplanar=True)
    step('Color Clouds', colour_clouds)

    # baked data channels (thickness / curvature from the mesh SDF) -> exported into the UE mask
    def baked_layers():
        l = ls.insert_fill(top()); l.set_name('Baked Thickness'); l.active_channels = {CT.User2}
        l.set_source(CT.User2, baked('Thickness'))
    step('Baked Maps', baked_layers)

    # 3. cavities read denser (curvature generator, concave)
    def cavity():
        l = fill('Cavity Density', {CT.BaseColor: Color(0.72, 0.68, 0.72)}, opacity=0.6)
        mask_fill(l, baked('Cavity'))
        try:
            l.mask_effects()[0].get_source().set_parameters({'invert': True})
        except Exception as e:
            print('  cavity invert warn', e)
    step('Cavity Density', cavity)

    # 4. soft lumps: very low-frequency 3D noise into height
    def lumps():
        l = fill('Soft Lumps', {CT.Height: 0.35}, opacity=0.35)
        mask_fill(l, res('3D_perlin_noise_fractal/3D_perlin_noise_fractal'))
    step('Soft Lumps', lumps)

    # 5. drips flowing down (triplanar leaks => world-down streaks)
    def drips():
        l = fill('Drips', {CT.Height: 0.6, CT.Roughness: 0.02}, opacity=0.8)
        mask_fill(l, res('grunge_rusty_leaks/grunge_rusty_leaks'), triplanar=True)
        mask_generator(l, res('mg_position/mg_position'), blend=ls.BlendingMode.Multiply)
    step('Drips', drips)

    # 6. micro ripples
    def ripples():
        l = fill('Micro Ripples', {CT.Height: 0.15}, opacity=0.25)
        mask_fill(l, res('noise_liquid/liquid'), triplanar=True)
    step('Micro Ripples', ripples)

    # 7. smudges / fingerprints (roughness + User1)
    def smudges():
        l = fill('Smudges', {CT.Roughness: 0.22, CT.User1: 1.0})
        mask_fill(l, res('grunge_wipe_smudgy_heavy/grunge_wipe_smudgy_heavy'), triplanar=True, opacity=0.45)
    step('Smudges', smudges)

    # 8. suspended bubbles (User0) - sparse spots
    def bubbles():
        l = fill('Bubbles', {CT.User0: 1.0, CT.BaseColor: Color(1, 1, 1)}, opacity=1.0)
        l.set_opacity(0.25, CT.BaseColor)  # bubbles only faintly visible in colour
        fx = mask_fill(l, res('noise_gaussian_spots_1/gaussian_spots_1'), triplanar=True)
        print('  bubble params', list(fx.get_source().get_parameters().keys())[:30])
    step('Bubbles', bubbles)

    # 9. painterly data (UE uses these to break cel-band edges like brush strokes)
    def strokes():
        l = fill('Brush Strokes', {CT.User4: 1.0})
        mask_fill(l, res('grunge_wipe_brushed_large/grunge_wipe_brushed_large'), triplanar=True)
        l2 = fill('Paint Dabs', {CT.User5: 1.0})
        mask_fill(l2, res('grunge_plaster_painted/grunge_plaster_painted'), triplanar=True)
    step('Brush Strokes', strokes)

print('\n'.join(report))
print('layers:', [n.get_name() for n in ls.get_root_layer_nodes(stack)])
