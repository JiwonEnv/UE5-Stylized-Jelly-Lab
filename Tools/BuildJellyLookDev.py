"""Run inside UE5 Editor (py "Tools/BuildJellyLookDev.py") or via Python remote execution.

Builds M_Jelly_Gummy: a translucent, refracting gummy material whose colour is driven by
thickness (thin = bright/saturated, thick = deep), with sharp specular, fake inner scatter,
suspended bubbles and soft surface detail from the Substance Painter maps.
Then imports the gummy bear mesh + textures, creates colour instances and a look-dev level.
"""
from pathlib import Path
import unreal as u

ROOT = Path(u.Paths.project_dir()).resolve()
SRC = ROOT / 'SourceAssets' / 'Characters' / 'Jelly'
TEX_SRC = SRC / 'Textures'
DEST = '/Game/JellyGame/Art/Jelly'
MAT_NAME = 'M_Jelly_Gummy'
LEVEL = '/Game/JellyGame/Maps/L_JellyLookDev'
BASE_LEVEL = '/Game/JellyGame/Maps/L_PainterMaterialTest'

tools = u.AssetToolsHelpers.get_asset_tools()
lib = u.MaterialEditingLibrary
eal = u.EditorAssetLibrary
MP = u.MaterialProperty


def log(*a):
    u.log('[JellyLookDev] ' + ' '.join(str(x) for x in a))
    print('[JellyLookDev]', *a)


# ---------------------------------------------------------------- import
def import_file(path, name, dest=DEST):
    task = u.AssetImportTask()
    task.filename = str(path)
    task.destination_path = dest
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    tools.import_asset_tasks([task])
    asset = eal.load_asset(f'{dest}/{name}')
    if not asset:
        objs = list(task.get_objects()) or [eal.load_asset(p) for p in task.imported_object_paths]
        asset = next((o for o in objs if o), None)
    if not asset:
        raise RuntimeError(f'import failed: {path}')
    return asset


TEXTURES = {
    # name suffix: (file, srgb, compression)
    'BC': ('GummyBear_BaseColor.png', True, u.TextureCompressionSettings.TC_DEFAULT),
    'N': ('GummyBear_Normal.png', False, u.TextureCompressionSettings.TC_NORMALMAP),
    'Mask': ('GummyBear_Mask.png', False, u.TextureCompressionSettings.TC_MASKS),  # R thick G curv B bubbles A rough
    'Paint': ('GummyBear_Paint.png', False, u.TextureCompressionSettings.TC_MASKS),  # R brush strokes G paint dabs
    'Brush': ('JellyBrushStrokes.png', False, u.TextureCompressionSettings.TC_MASKS),  # R stroke ID G highlight dashes B bristle
    'Stars': ('JellyStarSparkles.png', False, u.TextureCompressionSettings.TC_MASKS),  # R 4-pt stars G 6-pt stars B square glints
}


def import_textures():
    out = {}
    for suffix, (fname, srgb, comp) in TEXTURES.items():
        f = TEX_SRC / fname
        if not f.exists():
            log('missing texture, using fallback:', f)
            out[suffix] = None
            continue
        t = import_file(f, 'T_GummyBear_' + suffix)
        t.set_editor_property('srgb', srgb)
        t.set_editor_property('compression_settings', comp)
        eal.save_loaded_asset(t)
        out[suffix] = t
    return out


def import_mesh():
    mesh = eal.load_asset(f'{DEST}/SM_GummyBear')
    if mesh:
        return disable_nanite(mesh)
    mesh = import_file(SRC / 'SM_GummyBear.obj', 'SM_GummyBear')
    if not isinstance(mesh, u.StaticMesh):
        mesh = next((eal.load_asset(p) for p in eal.list_assets(DEST, False)
                     if isinstance(eal.load_asset(p), u.StaticMesh)), None)
    return disable_nanite(mesh)


def disable_nanite(mesh):
    # Translucent materials render Nanite meshes with the coarse fallback (~3k tris) -> faceted jelly.
    ns = mesh.get_editor_property('nanite_settings')
    if ns.enabled:
        ns.enabled = False
        # set_editor_property alone does not rebuild render data; the subsystem call does
        u.get_editor_subsystem(u.StaticMeshEditorSubsystem).set_nanite_settings(mesh, ns, True)
        eal.save_loaded_asset(mesh)
        log('nanite disabled on', mesh.get_name())
    return mesh


# ---------------------------------------------------------------- graph helpers
class G:
    def __init__(self, mat):
        self.m = mat

    def node(self, cls, x, y, **props):
        n = lib.create_material_expression(self.m, cls, x, y)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def scalar(self, name, v, x, y, group='Jelly'):
        return self.node(u.MaterialExpressionScalarParameter, x, y, parameter_name=name, default_value=v, group=group)

    def color(self, name, rgb, x, y, group='Jelly'):
        return self.node(u.MaterialExpressionVectorParameter, x, y, parameter_name=name,
                         default_value=u.LinearColor(*rgb, 1.0), group=group)

    def tex(self, name, texture, x, y, sampler):
        n = self.node(u.MaterialExpressionTextureSampleParameter2D, x, y, parameter_name=name, sampler_type=sampler, group='Textures')
        if texture:
            n.set_editor_property('texture', texture)
        return n

    def link(self, a, a_out, b, b_in):
        if not lib.connect_material_expressions(a, a_out, b, b_in):
            raise RuntimeError(f'link failed {a.get_name()}.{a_out} -> {b.get_name()}.{b_in}')

    def op(self, cls, x, y, a, b=None, a_out='', b_out='', **props):
        n = self.node(cls, x, y, **props)
        self.link(a, a_out, n, 'A')
        if b is not None:
            self.link(b, b_out, n, 'B')
        return n

    def mul(self, x, y, a, b, a_out='', b_out=''):
        return self.op(u.MaterialExpressionMultiply, x, y, a, b, a_out, b_out)

    def add(self, x, y, a, b, a_out='', b_out=''):
        return self.op(u.MaterialExpressionAdd, x, y, a, b, a_out, b_out)

    def lerp(self, x, y, a, b, alpha, a_out='', b_out='', al_out=''):
        n = self.node(u.MaterialExpressionLinearInterpolate, x, y)
        self.link(a, a_out, n, 'A'); self.link(b, b_out, n, 'B'); self.link(alpha, al_out, n, 'Alpha')
        return n

    def one_minus(self, x, y, a, a_out=''):
        n = self.node(u.MaterialExpressionOneMinus, x, y)
        self.link(a, a_out, n, '')
        return n

    def power(self, x, y, base, exp, base_out='', exp_out=''):
        n = self.node(u.MaterialExpressionPower, x, y)
        self.link(base, base_out, n, 'Base'); self.link(exp, exp_out, n, 'Exp')
        return n

    def sat(self, x, y, a, a_out=''):
        n = self.node(u.MaterialExpressionSaturate, x, y)
        self.link(a, a_out, n, '')
        return n

    def const(self, x, y, v):
        if isinstance(v, (tuple, list)):
            return self.node(u.MaterialExpressionConstant3Vector, x, y, constant=u.LinearColor(*v, 1))
        return self.node(u.MaterialExpressionConstant, x, y, r=v)

    def smoothstep(self, x, y, lo, hi, val, val_out=''):
        n = self.node(u.MaterialExpressionSmoothStep, x, y)
        self.link(lo, '', n, 'Min'); self.link(hi, '', n, 'Max'); self.link(val, val_out, n, 'Value')
        return n

    def unary(self, cls, x, y, src, src_out='', **props):
        n = self.node(cls, x, y, **props)
        self.link(src, src_out, n, '')
        return n

    def div(self, x, y, a, b):
        return self.op(u.MaterialExpressionDivide, x, y, a, b)

    def dot(self, x, y, a, b):
        n = self.node(u.MaterialExpressionDotProduct, x, y)
        self.link(a, '', n, 'A'); self.link(b, '', n, 'B')
        return n

    def out(self, n, n_out, prop):
        if not lib.connect_material_property(n, n_out, prop):
            raise RuntimeError(f'output link failed -> {prop}')


def set_if(obj, prop, value):
    try:
        obj.set_editor_property(prop, value)
    except Exception as e:  # property names drift between engine versions
        log('skip', prop, e)


# ---------------------------------------------------------------- material
def build_material(tex):
    m = eal.load_asset(f'{DEST}/{MAT_NAME}') or tools.create_asset(MAT_NAME, DEST, u.Material, u.MaterialFactoryNew())
    lib.delete_all_material_expressions(m)
    # delete_all_material_expressions leaves custom output nodes (Thin Translucent) behind;
    # duplicates break compilation ("only one Thin Translucent Material node").
    for e in list(lib.get_material_expressions(m)):
        lib.delete_material_expression(m, e)
    m.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property('shading_model', u.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
    m.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    set_if(m, 'refraction_method', u.RefractionMode.RM_INDEX_OF_REFRACTION)
    set_if(m, 'screen_space_reflections', True)
    set_if(m, 'contact_shadows', True)
    set_if(m, 'two_sided', False)
    set_if(m, 'allow_translucent_custom_depth_writes', True)  # lets the paint post-filter mask jelly pixels

    g = G(m)
    S = u.MaterialSamplerType
    X = -1900

    # --- parameters
    jelly = g.color('Jelly Color', (0.95, 0.12, 0.16), X, -900)
    deep = g.color('Deep Color', (0.42, 0.01, 0.05), X, -760)
    glow_col = g.color('Inner Glow Color', (1.0, 0.35, 0.30), X, -620)
    density = g.scalar('Density', 1.6, X, -480)
    thick_bias = g.scalar('Thickness Bias', 0.0, X, -400)
    fake_thick_w = g.scalar('Fresnel Thickness Weight', 0.35, X, -320)
    glow = g.scalar('Inner Glow', 1.1, X, -240)
    opac_thin = g.scalar('Opacity Thin', 0.12, X, -160)
    opac_thick = g.scalar('Opacity Thick', 0.5, X, -80)
    rim_opac = g.scalar('Rim Opacity', 0.2, X, 0)
    rough_min = g.scalar('Roughness', 0.035, X, 80)
    smudge = g.scalar('Smudge Roughness', 0.06, X, 160)
    spec = g.scalar('Specular', 0.55, X, 240)
    ior = g.scalar('IOR', 1.33, X, 320)
    bubble_amt = g.scalar('Bubble Brightness', 0.5, X, 400)
    normal_str = g.scalar('Normal Strength', 0.18, X, 480)

    tbc = g.tex('BaseColor Tint', tex.get('BC'), X, 620, S.SAMPLERTYPE_COLOR)
    tn = g.tex('Normal', tex.get('N'), X, 900, S.SAMPLERTYPE_NORMAL)
    tm = g.tex('Mask', tex.get('Mask'), X, 1180, S.SAMPLERTYPE_MASKS)
    tp = g.tex('Paint Mask', tex.get('Paint'), X, 1460, S.SAMPLERTYPE_MASKS)

    # --- brush-stroke field: object-space triplanar sample of the stroke texture
    brush_amt = g.scalar('Brush Amount', 0.0, X, -2000, 'Brush Strokes')
    brush_scale = g.scalar('Brush Scale', 42.0, X, -1920, 'Brush Strokes')
    patch_brk = g.scalar('Brush Patch Breakup', 0.35, X, -1840, 'Brush Strokes')
    hue_a = g.color('Brush Hue A', (0.85, 0.78, 1.05), X, -2160, 'Brush Strokes')
    hue_b = g.color('Brush Hue B', (1.05, 0.90, 0.80), X, -2240, 'Brush Strokes')
    hue_jit = g.scalar('Brush Hue Jitter', 0.6, X, -2080, 'Brush Strokes')
    bristle_amt = g.scalar('Bristle', 0.25, X, -2320, 'Brush Strokes')
    dash_amt = g.scalar('Dash Highlights', 0.0, X, -2400, 'Brush Strokes')
    lp = g.div(-1600, -2100, g.op(u.MaterialExpressionSubtract, -1700, -2100,
                                  g.node(u.MaterialExpressionWorldPosition, -1800, -2120),
                                  g.node(u.MaterialExpressionObjectPositionWS, -1800, -2060)), brush_scale)
    nb = g.node(u.MaterialExpressionVertexNormalWS, -1800, -1980)
    wv = g.power(-1600, -1980, g.unary(u.MaterialExpressionAbs, -1700, -1980, nb), g.const(-1700, -1940, 4.0))
    wsum = g.dot(-1500, -1940, wv, g.const(-1600, -1920, (1.0, 1.0, 1.0)))
    wv = g.div(-1400, -1980, wv, wsum)
    brush_tex = tex.get('Brush')
    S_acc = None
    for k, (mask, wch) in enumerate((((False, True, True), 'R'), ((True, False, True), 'G'), ((True, True, False), 'B'))):
        uvk = g.unary(u.MaterialExpressionComponentMask, -1450, -2200 + k * 60, lp, r=mask[0], g=mask[1], b=mask[2], a=False)
        smp = g.node(u.MaterialExpressionTextureSample, -1300, -2200 + k * 60, sampler_type=S.SAMPLERTYPE_MASKS)
        if brush_tex:
            smp.set_editor_property('texture', brush_tex)
        g.link(uvk, '', smp, 'UVs')
        wk = g.unary(u.MaterialExpressionComponentMask, -1300, -1900 + k * 40, wv, r=wch == 'R', g=wch == 'G', b=wch == 'B', a=False)
        term_k = g.mul(-1150, -2200 + k * 60, smp, wk, 'RGB')
        S_acc = term_k if S_acc is None else g.add(-1050, -2200 + k * 60, S_acc, term_k)
    stroke_id = g.unary(u.MaterialExpressionComponentMask, -950, -2200, S_acc, r=True, g=False, b=False, a=False)
    stroke_dash = g.unary(u.MaterialExpressionComponentMask, -950, -2140, S_acc, r=False, g=True, b=False, a=False)
    stroke_bristle = g.unary(u.MaterialExpressionComponentMask, -950, -2080, S_acc, r=False, g=False, b=True, a=False)
    if not tex.get('BC'):
        tbc.set_editor_property('texture', eal.load_asset('/Engine/EngineResources/WhiteSquareTexture'))
    if not tex.get('N'):
        tn.set_editor_property('texture', eal.load_asset('/Engine/EngineMaterials/FlatNormal'))
    if not tex.get('Mask'):
        tm.set_editor_property('texture', eal.load_asset('/Engine/EngineResources/Black'))

    # --- thickness: baked map blended with a view-based fallback (centre thick, rim thin)
    fres = g.node(u.MaterialExpressionFresnel, -1500, -300, exponent=1.6, base_reflect_fraction=0.0)
    view_thick = g.one_minus(-1350, -300, fres)
    thick = g.lerp(-1200, -380, tm, view_thick, fake_thick_w, 'R')
    thick = g.sat(-1050, -380, g.add(-1120, -380, thick, thick_bias))

    # --- multi-colour height gradient (top = Jelly Color, mid, bottom), off by default
    grad_amt = g.scalar('Gradient Amount', 0.0, X, -1300, 'Color Gradient')
    mid_col = g.color('Gradient Mid Color', (0.55, 0.15, 0.85), X, -1220, 'Color Gradient')
    bot_col = g.color('Gradient Bottom Color', (0.20, 0.60, 1.00), X, -1140, 'Color Gradient')
    bear_h = g.scalar('Object Height', 44.0, X, -1060, 'Color Gradient')
    g_low = g.scalar('Gradient Bottom End', 0.3, X, -980, 'Color Gradient')
    g_top = g.scalar('Gradient Top Start', 0.32, X, -900, 'Color Gradient')
    g_width = g.scalar('Gradient Top Width', 0.22, X, -820, 'Color Gradient')
    g_core = g.scalar('Gradient Core Only', 0.0, X, -740, 'Color Gradient')
    wp = g.node(u.MaterialExpressionWorldPosition, -1700, -1250)
    op_ws = g.node(u.MaterialExpressionObjectPositionWS, -1700, -1180)
    dz = g.op(u.MaterialExpressionSubtract, -1580, -1220, wp, op_ws)
    hz = g.unary(u.MaterialExpressionComponentMask, -1480, -1220, dz, r=False, g=False, b=True, a=False)
    h = g.sat(-1280, -1220, g.div(-1380, -1220, hz, bear_h))
    low = g.lerp(-1150, -1260, bot_col, mid_col, g.sat(-1200, -1300, g.div(-1250, -1300, h, g_low)))
    up = g.sat(-1150, -1160, g.div(-1200, -1160, g.op(u.MaterialExpressionSubtract, -1250, -1160, h, g_top), g_width))
    grad = g.lerp(-1050, -1220, low, jelly, up)
    # optionally only the thick core takes the gradient (thin limbs / rims keep Jelly Color)
    core = g.lerp(-1000, -1060, g.const(-1100, -1080, 1.0), g.smoothstep(-1100, -1040, g.const(-1200, -1060, 0.35), g.const(-1200, -1020, 0.8), thick), g_core)
    grad_a = g.mul(-1000, -1000, grad_amt, core)
    jelly = g.lerp(-950, -1000, jelly, grad, grad_a)
    deep = g.lerp(-950, -900, deep, g.mul(-1050, -900, grad, g.const(-1150, -880, 0.55)), grad_a)

    # --- painterly banding of the thickness shading, off by default
    paint = g.scalar('Paint Style', 0.0, X, -1500, 'Painterly')
    bands = g.scalar('Paint Bands', 3.0, X, -1420, 'Painterly')
    banding = g.scalar('Paint Banding', 0.75, X, -1340, 'Painterly')
    stroke_brk = g.scalar('Stroke Breakup', 0.25, X, -1580, 'Painterly')
    brk = g.mul(-1150, -540, g.add(-1250, -540, tp, g.mul(-1250, -500, g.op(u.MaterialExpressionSubtract, -1350, -500, tp, g.const(-1450, -480, 0.8), 'G'), g.const(-1350, -460, 0.5)), 'R'), stroke_brk)
    brk = g.add(-1050, -580, brk, g.mul(-1100, -600, g.op(u.MaterialExpressionSubtract, -1200, -620, stroke_id, g.const(-1300, -620, 0.5)),
                                         g.mul(-1200, -580, patch_brk, brush_amt)))
    thick_b = g.add(-1150, -460, thick, g.mul(-1250, -440, brk, paint))
    tb = g.div(-1000, -420, g.unary(u.MaterialExpressionFloor, -1050, -460, g.add(-1100, -460, g.mul(-1150, -400, thick_b, bands), g.const(-1200, -430, 0.5))), bands)
    # saturate: stroke breakup can push the banded value outside 0..1 -> pow(negative) = NaN (green bloom specks)
    thick = g.sat(-850, -380, g.lerp(-900, -380, thick, tb, g.mul(-1000, -340, paint, banding)))

    # Beer-Lambert style absorption: colour^(density*thickness) -> thin parts bright, thick parts deep
    exp_ = g.add(-900, -520, g.mul(-1000, -520, thick, density), g.node(u.MaterialExpressionConstant, -1100, -560, r=0.35))
    absorb = g.power(-760, -620, jelly, exp_)
    body = g.lerp(-620, -700, absorb, deep, g.power(-760, -470, thick, g.node(u.MaterialExpressionConstant, -880, -440, r=2.2)))
    body = g.mul(-480, -700, body, tbc, '', 'RGB')
    fres_raw = g.node(u.MaterialExpressionFresnel, -1500, -150, exponent=1.0, base_reflect_fraction=0.0)
    outline_amt = g.scalar('Outline Amount', 0.0, X, -1260, 'Painterly')
    outline_col = g.color('Outline Color', (0.55, 0.05, 0.10), X, -1180, 'Painterly')
    edge = g.smoothstep(-700, -760, g.const(-820, -790, 0.55), g.const(-820, -760, 0.8), fres_raw)
    body = g.lerp(-380, -700, body, g.mul(-480, -760, body, outline_col), g.mul(-560, -740, edge, outline_amt))

    # --- painterly cel tones from a fixed key light, edges broken by brush strokes
    cel_amt = g.scalar('Cel Amount', 0.0, X, -1660, 'Painterly')
    shadow_tone = g.color('Shadow Tone', (0.70, 0.45, 0.55), X, -1740, 'Painterly')
    light_tone = g.color('Light Tone', (1.25, 1.15, 1.05), X, -1820, 'Painterly')
    nws_c = g.node(u.MaterialExpressionVertexNormalWS, -1300, -1500)
    ndl = g.add(-1050, -1500, g.dot(-1150, -1500, nws_c, g.const(-1300, -1440, (0.55, 0.35, 0.76))), brk)
    lit = g.smoothstep(-900, -1520, g.const(-1000, -1560, 0.15), g.const(-1000, -1530, 0.2), ndl)
    hi_t = g.smoothstep(-900, -1440, g.const(-1000, -1470, 0.72), g.const(-1000, -1440, 0.76), ndl)
    tone = g.mul(-750, -1480, g.lerp(-820, -1520, shadow_tone, g.const(-900, -1580, (1, 1, 1)), lit),
                 g.lerp(-820, -1440, g.const(-900, -1400, (1, 1, 1)), light_tone, hi_t))
    tone = g.lerp(-650, -1480, g.const(-750, -1420, (1, 1, 1)), tone, g.mul(-750, -1380, cel_amt, paint))
    body = g.mul(-300, -700, body, tone)
    sel_a = g.mul(-500, -2300, g.smoothstep(-600, -2300, g.const(-700, -2320, 0.62), g.const(-700, -2290, 0.7), stroke_id), g.mul(-600, -2250, hue_jit, brush_amt))
    sel_b = g.mul(-500, -2200, g.one_minus(-600, -2200, g.smoothstep(-700, -2200, g.const(-800, -2220, 0.28), g.const(-800, -2190, 0.36), stroke_id)), g.mul(-600, -2160, hue_jit, brush_amt))
    body = g.mul(-200, -700, g.mul(-250, -700, body, g.lerp(-400, -2300, g.const(-500, -2340, (1, 1, 1)), hue_a, sel_a)),
                 g.lerp(-400, -2200, g.const(-500, -2240, (1, 1, 1)), hue_b, sel_b))
    bristle_f = g.add(-500, -2080, g.const(-600, -2100, 0.82), g.mul(-600, -2060, stroke_bristle, g.const(-700, -2040, 0.36)))
    body = g.mul(-150, -700, body, g.lerp(-400, -2080, g.const(-500, -2120, 1.0), bristle_f, g.mul(-500, -2020, bristle_amt, brush_amt)))

    # Thin Translucent: the background seen through the jelly is multiplied by this transmittance,
    # so whatever is behind gets dyed (thin = light jelly colour, thick = deep colour).
    trans_b = g.scalar('Transmission Brightness', 1.0, X, 800)
    trans = g.mul(-480, -820, g.lerp(-620, -820, absorb, deep, thick), trans_b)
    thin_out = g.node(u.MaterialExpressionThinTranslucentMaterialOutput, -300, -820)
    g.link(trans, '', thin_out, '')

    # bubbles (mask B): lighter specks inside the body
    bub_sharp = g.scalar('Bubble Sharpness', 3.0, X, 560)
    bub = g.mul(-760, 1180, g.power(-900, 1180, tm, bub_sharp, 'B'), bubble_amt)
    base = g.lerp(-320, -650, body, g.node(u.MaterialExpressionConstant3Vector, -480, -560, constant=u.LinearColor(1, 1, 1, 1)),
                  g.mul(-480, -480, bub, g.node(u.MaterialExpressionConstant, -600, -430, r=0.6)))
    g.out(base, '', MP.MP_BASE_COLOR)

    # fake inner scatter: brighter where thin, tinted
    thin = g.one_minus(-900, -200, thick)
    scatter = g.power(-760, -200, thin, g.node(u.MaterialExpressionConstant, -900, -140, r=1.4))
    scatter = g.add(-680, -200, g.mul(-720, -230, scatter, g.node(u.MaterialExpressionConstant, -820, -230, r=0.7)), g.node(u.MaterialExpressionConstant, -820, -170, r=0.3))
    emis = g.mul(-520, -200, g.mul(-600, -200, g.mul(-700, -260, glow_col, absorb), g.mul(-700, -150, scatter, glow)), tone)
    emis = g.add(-450, -150, emis, g.mul(-600, -60, g.mul(-700, 1100, bub, glow_col), g.node(u.MaterialExpressionConstant, -720, 1040, r=0.25)))
    # --- two-colour rim light (side A = +Y world, side B = -Y), off by default
    rim_a_col = g.color('Rim Color A', (1.0, 0.82, 0.15), X, 900, 'Rim / Iridescence')
    rim_b_col = g.color('Rim Color B', (0.30, 0.85, 1.0), X, 980, 'Rim / Iridescence')
    rim_a = g.scalar('Rim Light A', 0.0, X, 1060, 'Rim / Iridescence')
    rim_b = g.scalar('Rim Light B', 0.0, X, 1140, 'Rim / Iridescence')
    rim_pow = g.scalar('Rim Power', 2.5, X, 1220, 'Rim / Iridescence')
    nws = g.node(u.MaterialExpressionVertexNormalWS, -1300, 1800)
    side = g.dot(-1150, 1800, nws, g.const(-1300, 1880, (0.0, 1.0, 0.25)))
    side = g.sat(-950, 1800, g.add(-1000, 1800, g.mul(-1050, 1800, side, g.const(-1150, 1880, 0.6)), g.const(-1150, 1920, 0.5)))
    rim = g.power(-950, 1700, fres_raw, rim_pow)
    rim_term = g.add(-650, 1750,
                     g.mul(-750, 1700, g.mul(-850, 1700, rim_a_col, rim_a), g.mul(-850, 1760, rim, side)),
                     g.mul(-750, 1820, g.mul(-850, 1820, rim_b_col, rim_b), g.mul(-850, 1880, rim, g.one_minus(-900, 1880, side))))
    emis = g.add(-450, 1750, emis, rim_term)

    # --- thin-film iridescence: rainbow hue shifting with view angle, off by default
    irid_amt = g.scalar('Iridescence', 0.0, X, 1300, 'Rim / Iridescence')
    irid_scale = g.scalar('Iridescence Scale', 1.6, X, 1380, 'Rim / Iridescence')
    irid_off = g.scalar('Iridescence Offset', 0.1, X, 1460, 'Rim / Iridescence')
    t = g.add(-1150, 2050, g.mul(-1250, 2050, fres_raw, irid_scale), irid_off)
    phase = g.add(-1050, 2050, t, g.const(-1150, 2120, (0.0, 0.33, 0.67)))
    rainbow = g.add(-850, 2050, g.mul(-900, 2050, g.unary(u.MaterialExpressionCosine, -950, 2050, phase, period=1.0), g.const(-950, 2120, 0.5)), g.const(-900, 2120, 0.5))
    emis = g.add(-450, 2050, emis, g.mul(-600, 2050, rainbow, g.mul(-700, 2100, g.power(-800, 2100, fres_raw, g.const(-880, 2150, 1.6)), irid_amt)))

    # --- painterly sparkles: tiny hard glints from the bubble mask, off by default
    sparkle = g.scalar('Sparkle', 0.0, X, 1540, 'Painterly')
    spk_src = g.power(-950, 2250, tm, g.const(-1050, 2290, 2.0), 'B')
    spk = g.smoothstep(-800, 2250, g.const(-900, 2220, 0.45), g.const(-900, 2290, 0.6), spk_src)
    emis = g.add(-450, 2250, emis, g.mul(-600, 2250, spk, g.mul(-700, 2300, sparkle, g.const(-800, 2320, 4.0))))

    # --- star sparkles: a sparse star-sprite texture projected tri-planar in OBJECT space, shown only
    #     on the side that faces the key highlights. (Reflection-space stars were tried first: on a
    #     curved bear the reflection vector changes so fast that they shrink to 1-3 pixels.)
    star_amt = g.scalar('Star Glint', 0.0, X, 1620, 'Sparkle / Edge')
    star_size = g.scalar('Star Size', 1.0, X, 1700, 'Sparkle / Edge')
    star_pts = g.scalar('Star Points', 4.0, X, 1780, 'Sparkle / Edge')      # 0 = square glints, 4, 6
    star_col = g.color('Star Color', (1.0, 1.0, 0.95), X, 1860, 'Sparkle / Edge')
    star_zone = g.scalar('Star Zone', 0.45, X, 2100, 'Sparkle / Edge')      # lower = stars spread further from highlights
    refl_s = g.node(u.MaterialExpressionReflectionVectorWS, -1300, 2400)
    rawp = g.op(u.MaterialExpressionSubtract, -1700, 2500, g.node(u.MaterialExpressionWorldPosition, -1800, 2480),
                g.node(u.MaterialExpressionObjectPositionWS, -1800, 2540))
    sp = g.div(-1600, 2500, rawp, g.mul(-1700, 2600, star_size, g.const(-1800, 2620, 22.0)))
    nst = g.node(u.MaterialExpressionVertexNormalWS, -1800, 2700)
    w8 = g.power(-1600, 2700, g.unary(u.MaterialExpressionAbs, -1700, 2700, nst), g.const(-1700, 2740, 8.0))
    w8 = g.div(-1450, 2700, w8, g.dot(-1550, 2740, w8, g.const(-1650, 2760, (1.0, 1.0, 1.0))))
    star_tex = tex.get('Stars')
    S_st = None
    for k, (mask, wch) in enumerate((((False, True, True), 'R'), ((True, False, True), 'G'), ((True, True, False), 'B'))):
        uvk = g.unary(u.MaterialExpressionComponentMask, -1450, 2500 + k * 60, sp, r=mask[0], g=mask[1], b=mask[2], a=False)
        smp = g.node(u.MaterialExpressionTextureSample, -1300, 2500 + k * 60, sampler_type=S.SAMPLERTYPE_MASKS)
        if star_tex:
            smp.set_editor_property('texture', star_tex)
        g.link(uvk, '', smp, 'UVs')
        wk = g.unary(u.MaterialExpressionComponentMask, -1300, 2800 + k * 40, w8, r=wch == 'R', g=wch == 'G', b=wch == 'B', a=False)
        tk = g.mul(-1150, 2500 + k * 60, smp, wk, 'RGB')
        S_st = tk if S_st is None else g.add(-1050, 2500 + k * 60, S_st, tk)
    s4 = g.unary(u.MaterialExpressionComponentMask, -950, 2500, S_st, r=True, g=False, b=False, a=False)
    s6 = g.unary(u.MaterialExpressionComponentMask, -950, 2560, S_st, r=False, g=True, b=False, a=False)
    sq = g.unary(u.MaterialExpressionComponentMask, -950, 2620, S_st, r=False, g=False, b=True, a=False)
    shape = g.lerp(-750, 2560, g.lerp(-850, 2520, sq, s4, g.sat(-900, 2480, g.div(-950, 2460, star_pts, g.const(-1050, 2460, 4.0)))),
                   s6, g.sat(-850, 2620, g.div(-900, 2620, g.op(u.MaterialExpressionSubtract, -950, 2660, star_pts, g.const(-1050, 2680, 4.0)), g.const(-1050, 2720, 2.0))))
    d_key = g.op(u.MaterialExpressionMax, -900, 2800,
                 g.dot(-1000, 2780, refl_s, g.const(-1100, 2780, (0.62, 0.38, 0.69))),
                 g.dot(-1000, 2840, refl_s, g.const(-1100, 2840, (0.80, -0.48, 0.36))))
    zone = g.smoothstep(-750, 2800, star_zone, g.add(-850, 2860, star_zone, g.const(-950, 2880, 0.2)), d_key)
    star = g.mul(-600, 2600, shape, zone)
    emis = g.add(-300, 2400, emis, g.mul(-400, 2450, g.mul(-450, 2450, star_col, star), g.mul(-500, 2500, star_amt, g.const(-600, 2520, 4.0))))

    # --- thin bright edge line just inside the silhouette (glassy rim of the blue apple)
    edge_amt = g.scalar('Edge Line', 0.0, X, 1940, 'Sparkle / Edge')
    edge_col = g.color('Edge Line Color', (1.0, 1.0, 1.0), X, 2020, 'Sparkle / Edge')
    eline = g.mul(-600, 3300, g.smoothstep(-700, 3300, g.const(-800, 3300, 0.45), g.const(-800, 3330, 0.55), fres_raw),
                  g.one_minus(-650, 3360, g.smoothstep(-700, 3360, g.const(-800, 3360, 0.72), g.const(-800, 3390, 0.82), fres_raw)))
    eline = g.mul(-500, 3300, eline, edge_amt)
    emis = g.add(-300, 3300, emis, g.mul(-400, 3300, edge_col, eline))
    op_star = g.add(-300, 2600, g.mul(-350, 2600, star, star_amt), eline)

    # studio softbox highlights (translucent forward shading only gets the sun's specular;
    # gummy refs read through big, crisp white window reflections)
    hl_int = g.scalar('Highlight Intensity', 2.2, X, 640)
    hl_sharp = g.scalar('Highlight Sharpness', 90.0, X, 720)
    refl = g.node(u.MaterialExpressionReflectionVectorWS, -1100, 1400)
    noise = g.node(u.MaterialExpressionNoise, -1100, 1340, scale=0.03, levels=2, output_min=-1.0, output_max=1.0)
    hl_tint = g.lerp(-500, 1380, g.const(-600, 1360, (1, 1, 1)),
                     g.add(-560, 1400, g.mul(-600, 1400, rainbow, g.const(-650, 1420, 0.6)), g.const(-650, 1440, 0.4)), irid_amt)
    hl = None
    for i, (d, w) in enumerate((((0.62, 0.38, 0.69), 1.0), ((0.80, -0.48, 0.36), 0.55), ((-0.2, 0.1, 0.97), 0.35))):
        dv = g.node(u.MaterialExpressionConstant3Vector, -1100, 1500 + i * 120, constant=u.LinearColor(*d, 1))
        dp = g.node(u.MaterialExpressionDotProduct, -950, 1450 + i * 120)
        g.link(refl, '', dp, 'A'); g.link(dv, '', dp, 'B')
        soft = g.power(-800, 1450 + i * 120, g.sat(-880, 1450 + i * 120, dp), hl_sharp)
        # painted: crisp-edged, wobbly shape (noise warps the threshold)
        wob = g.mul(-900, 1530 + i * 120, noise, g.const(-1000, 1560 + i * 120, 0.025))
        hard = g.smoothstep(-700, 1530 + i * 120, g.const(-800, 1500 + i * 120, 0.915 - 0.02 * i), g.const(-800, 1560 + i * 120, 0.93 - 0.02 * i),
                            g.add(-760, 1530 + i * 120, dp, wob))
        halo = g.smoothstep(-700, 1590 + i * 120, g.const(-800, 1590 + i * 120, 0.86 - 0.02 * i), g.const(-800, 1620 + i * 120, 0.875 - 0.02 * i),
                            g.add(-760, 1590 + i * 120, dp, wob))
        zone = g.smoothstep(-700, 1650 + i * 120, g.const(-800, 1650 + i * 120, 0.70 - 0.03 * i), g.const(-800, 1680 + i * 120, 0.74 - 0.03 * i),
                            g.add(-760, 1650 + i * 120, dp, wob))
        dashes = g.mul(-650, 1650 + i * 120, g.mul(-700, 1680 + i * 120, zone, stroke_dash), dash_amt)
        painted = g.add(-620, 1560 + i * 120, hard, g.mul(-660, 1620 + i * 120, dashes, g.one_minus(-700, 1620 + i * 120, hard)))
        term = g.mul(-650, 1450 + i * 120, g.lerp(-700, 1450 + i * 120, soft, painted, paint), g.const(-800, 1520 + i * 120, w))
        hl = term if hl is None else g.add(-520, 1450 + i * 120, hl, term)
    hl = g.mul(-400, 1450, g.mul(-450, 1450, hl, hl_int), hl_tint)
    emis = g.add(-300, -100, emis, hl)
    g.out(emis, '', MP.MP_EMISSIVE_COLOR)
    op_hl = g.add(-250, 1450, g.unary(u.MaterialExpressionComponentMask, -300, 1450, hl, r=True, g=False, b=False, a=False),
                  g.mul(-300, 1750, g.unary(u.MaterialExpressionComponentMask, -350, 1750, rim_term, r=True, g=True, b=False, a=False) if False else g.dot(-350, 1750, rim_term, g.const(-450, 1790, (0.33, 0.33, 0.33))), g.const(-400, 1800, 0.6)))  # highlights/rims stay opaque
    op_hl = g.add(-200, 1500, op_hl, op_star)

    # opacity: thin = see-through, thick = dense, rim adds some density (grazing reflection)
    op = g.lerp(-600, 60, opac_thin, opac_thick, thick)
    op = g.sat(-320, 60, g.add(-380, 60, g.add(-450, 60, op, g.mul(-600, 140, fres, rim_opac)), op_hl))
    g.out(op, '', MP.MP_OPACITY)

    # roughness: glassy base + painted smudges (mask A)
    rough = g.add(-450, 260, rough_min, g.mul(-600, 260, tm, smudge, 'A'))
    g.out(rough, '', MP.MP_ROUGHNESS)
    g.out(spec, '', MP.MP_SPECULAR)

    # normal with strength (flatten toward 0,0,1)
    flat = g.node(u.MaterialExpressionConstant3Vector, -760, 820, constant=u.LinearColor(0, 0, 1, 1))
    nrm = g.lerp(-600, 900, flat, tn, normal_str, '', 'RGB')
    g.out(nrm, '', MP.MP_NORMAL)

    g.out(ior, '', MP.MP_REFRACTION)

    lib.layout_material_expressions(m)
    lib.recompile_material(m)
    eal.save_loaded_asset(m)
    log('material built', m.get_path_name())
    return m


# ---------------------------------------------------------------- instances
PRESETS = {
    # name: jelly, deep, glow, density, opacity thin/thick
    'Raspberry': ((0.95, 0.10, 0.14), (0.40, 0.00, 0.04), (1.0, 0.30, 0.28), 1.6, 0.30, 0.86),
    'Orange':    ((1.00, 0.42, 0.04), (0.65, 0.12, 0.00), (1.0, 0.62, 0.20), 1.4, 0.30, 0.86),
    'Teal':      ((0.10, 0.62, 0.66), (0.01, 0.20, 0.26), (0.45, 0.95, 0.92), 1.5, 0.30, 0.86),
    'Blue':      ((0.18, 0.55, 1.00), (0.02, 0.14, 0.55), (0.55, 0.80, 1.00), 1.5, 0.30, 0.86),
    # stylised looks
    'PinkIridescent': ((1.00, 0.36, 0.76), (0.85, 0.08, 0.50), (1.0, 0.45, 0.85), 0.8, 0.30, 0.86),
    'AmberPainted':   ((1.00, 0.70, 0.10), (0.80, 0.36, 0.02), (1.0, 0.85, 0.35), 1.0, 0.30, 0.86),
    'PinkPainted':    ((1.00, 0.62, 0.75), (0.92, 0.38, 0.55), (1.0, 0.80, 0.90), 0.8, 0.30, 0.86),
    'RedPainted':     ((0.90, 0.05, 0.06), (0.35, 0.00, 0.02), (1.0, 0.25, 0.20), 1.8, 0.30, 0.86),
}

# extra parameter overrides per preset (scalars as float, colours as 3-tuples)
EXTRA = {
    'PinkPainted': {   # pastel pink painted apple
        'Paint Style': 1.0, 'Paint Bands': 3.0, 'Paint Banding': 0.6, 'Cel Amount': 1.0,
        'Shadow Tone': (0.86, 0.66, 0.88), 'Light Tone': (1.12, 1.08, 1.08), 'Stroke Breakup': 0.3,
        'Brush Amount': 1.0, 'Brush Patch Breakup': 0.45, 'Brush Hue A': (0.85, 0.78, 1.06), 'Brush Hue B': (1.06, 0.90, 0.84),
        'Brush Hue Jitter': 0.8, 'Dash Highlights': 1.3, 'Bristle': 0.2,
        'Outline Amount': 0.3, 'Outline Color': (0.85, 0.40, 0.55), 'Highlight Intensity': 2.5,
        'Transmission Brightness': 0.75, 'Opacity Thick': 0.6, 'Opacity Thin': 0.3,
        'Normal Strength': 0.08, 'Bubble Brightness': 0.1, 'Inner Glow': 0.8,
    },
    'RedPainted': {    # deep red inked apple + PinkIridescent's multi-colour light + star sparkles
        'Paint Style': 1.0, 'Paint Bands': 3.0, 'Paint Banding': 0.9, 'Cel Amount': 1.0,
        'Shadow Tone': (0.45, 0.12, 0.25), 'Light Tone': (1.2, 1.05, 1.05), 'Stroke Breakup': 0.3,
        'Brush Amount': 1.0, 'Brush Patch Breakup': 0.4, 'Brush Hue A': (0.95, 0.80, 1.10), 'Brush Hue B': (1.10, 0.85, 0.70),
        'Brush Hue Jitter': 0.5, 'Dash Highlights': 0.6, 'Bristle': 0.3,
        'Outline Amount': 1.0, 'Outline Color': (0.25, 0.02, 0.08), 'Highlight Intensity': 3.5,
        # from PinkIridescent: multi-colour core gradient, gold / blue rim lights, rainbow sheen
        'Gradient Amount': 0.35, 'Gradient Core Only': 1.0, 'Gradient Mid Color': (0.70, 0.02, 0.30), 'Gradient Bottom Color': (0.28, 0.12, 0.85),
        'Gradient Bottom End': 0.08, 'Gradient Top Start': 0.18, 'Gradient Top Width': 0.25,
        'Rim Light A': 3.0, 'Rim Color A': (1.0, 0.72, 0.05), 'Rim Light B': 1.2, 'Rim Color B': (0.45, 0.65, 1.0), 'Rim Power': 2.5,
        'Iridescence': 0.15,
        # sparkles
        'Star Glint': 3.0, 'Star Size': 2.0, 'Star Points': 4.0, 'Star Zone': 0.3, 'Edge Line': 0.4,
        # keep the red: low transmission + high opacity turns it grey-pink
        'Transmission Brightness': 0.45, 'Opacity Thick': 0.85, 'Opacity Thin': 0.4, 'Density': 1.8,
        'Normal Strength': 0.05, 'Bubble Brightness': 0.1, 'Inner Glow': 0.6,
    },
    'PinkIridescent': {
        'Gradient Amount': 1.0, 'Gradient Mid Color': (0.50, 0.10, 0.85), 'Gradient Bottom Color': (0.10, 0.35, 1.0),
        'Gradient Core Only': 1.0, 'Gradient Bottom End': 0.12, 'Gradient Top Start': 0.3, 'Gradient Top Width': 0.18,
        'Rim Light A': 4.0, 'Rim Color A': (1.0, 0.80, 0.0), 'Rim Light B': 0.7, 'Rim Color B': (0.30, 0.70, 1.0),
        'Rim Power': 1.5, 'Iridescence': 0.25, 'Inner Glow': 0.8,
        'Transmission Brightness': 0.5, 'Opacity Thick': 0.7, 'Opacity Thin': 0.25, 'Density': 1.3,
    },
    'AmberPainted': {
        'Paint Style': 1.0, 'Paint Bands': 3.0, 'Paint Banding': 0.9, 'Sparkle': 0.6,
        'Outline Amount': 1.0, 'Outline Color': (0.75, 0.30, 0.0), 'Highlight Intensity': 3.0,
        'Cel Amount': 1.0, 'Shadow Tone': (0.72, 0.40, 0.10), 'Light Tone': (1.12, 1.06, 0.85), 'Stroke Breakup': 0.3,
        'Star Glint': 3.0, 'Star Size': 1.8, 'Star Points': 6.0, 'Star Zone': 0.3, 'Edge Line': 0.4, 'Smudge Roughness': 0.0,
        'Brush Amount': 1.0, 'Dash Highlights': 1.0, 'Bristle': 0.25, 'Brush Hue A': (1.0, 0.92, 0.62), 'Brush Hue B': (1.0, 0.72, 0.42),
        'Transmission Brightness': 0.5, 'Opacity Thick': 0.8, 'Opacity Thin': 0.35, 'Density': 1.6, 'Inner Glow': 0.6,
        'Rim Light A': 0.5, 'Rim Color A': (1.0, 0.95, 0.70), 'Normal Strength': 0.1, 'Bubble Brightness': 0.2,
    },
}


def build_instances(parent):
    out = {}
    for name, (c, d, gc, dens, o_thin, o_thick) in PRESETS.items():
        path = f'{DEST}/MI_Jelly_{name}'
        mi = eal.load_asset(path) or tools.create_asset(f'MI_Jelly_{name}', DEST, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        lib.set_material_instance_parent(mi, parent)
        lib.clear_all_material_instance_parameters(mi)  # drop stale overrides (e.g. from manual tweaking)
        for pn, col in (('Jelly Color', c), ('Deep Color', d), ('Inner Glow Color', gc)):
            lib.set_material_instance_vector_parameter_value(mi, pn, u.LinearColor(*col, 1))
        for pn, v in (('Density', dens),):
            lib.set_material_instance_scalar_parameter_value(mi, pn, v)
        for pn, v in EXTRA.get(name, {}).items():
            if isinstance(v, tuple):
                lib.set_material_instance_vector_parameter_value(mi, pn, u.LinearColor(*v, 1))
            else:
                lib.set_material_instance_scalar_parameter_value(mi, pn, v)
        lib.update_material_instance(mi)
        eal.save_loaded_asset(mi)
        out[name] = mi
    log('instances', list(out))
    return out


# ---------------------------------------------------------------- level
def build_level(mesh, mis):
    les = u.get_editor_subsystem(u.LevelEditorSubsystem)
    acts = u.get_editor_subsystem(u.EditorActorSubsystem)
    world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    current = world.get_path_name().split('.')[0] if world else ''
    if current != LEVEL:
        if eal.does_asset_exist(LEVEL):
            les.load_level(LEVEL)
        else:
            # Never duplicate_asset + load_level a map in one session: the duplicated UWorld stays
            # referenced and the editor hits a fatal "World Memory Leaks" on map load.
            if current != BASE_LEVEL:
                les.load_level(BASE_LEVEL)
            world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
            if not u.EditorLoadingAndSavingUtils.save_map(world, LEVEL):
                raise RuntimeError('could not save look-dev level')
            les.load_level(LEVEL)
    for a in acts.get_all_level_actors():
        if a.get_actor_label().startswith('Jelly_') or isinstance(a, u.StaticMeshActor) and a.get_actor_label().startswith('Painter'):
            acts.destroy_actor(a)
    # OBJ is Y-up with the face toward +Z; the importer keeps those axes (and flips Y).
    # Pick the 90-degree rotation that puts the mesh's up on +Z and its face toward +X (camera).
    bb = mesh.get_bounding_box()
    local_up = u.Vector(0, 1 if abs(bb.max.y) > abs(bb.min.y) else -1, 0)
    local_face = u.Vector(0, 0, 1 if abs(bb.max.z) > abs(bb.min.z) * 0.9 else -1)
    best, score = u.Rotator(0, 0, 0), -9
    for p in (0, 90, 180, 270):
        for yw in (0, 90, 180, 270):
            for r in (0, 90, 180, 270):
                rot = u.Rotator(roll=r, pitch=p, yaw=yw)
                s = u.MathLibrary.greater_greater_vector_rotator(local_up, rot).z + u.MathLibrary.greater_greater_vector_rotator(local_face, rot).x
                if s > score + 1e-3:
                    best, score = rot, s
    log('bear rotation', best, 'score', score)
    order = ['Raspberry', 'Orange', 'PinkPainted', 'AmberPainted', 'RedPainted', 'PinkIridescent', 'Blue']
    painted = {'PinkPainted', 'AmberPainted', 'RedPainted'}
    spacing = 55.0
    for i, name in enumerate(order):
        y = (i - (len(order) - 1) / 2) * spacing
        # the importer mirrors the OBJ's Z, so the face ends up opposite to the guess: turn around
        rot = u.Rotator(roll=best.roll, pitch=best.pitch, yaw=best.yaw + 180)
        a = acts.spawn_actor_from_object(mesh, u.Vector(0, y, 0), rot)
        a.set_actor_label(f'Jelly_Bear_{name}')
        a.static_mesh_component.set_material(0, mis[name])
        # painted looks get the screen-space brush filter (Kuwahara) through custom stencil 1
        a.static_mesh_component.set_render_custom_depth(name in painted)
        a.static_mesh_component.set_custom_depth_stencil_value(1 if name in painted else 0)
        o, e = a.get_actor_bounds(False)
        a.set_actor_location(u.Vector(0, y, a.get_actor_location().z - (o.z - e.z)), False, False)
    pp = acts.spawn_actor_from_class(u.PostProcessVolume, u.Vector(0, 0, 0))
    pp.set_actor_label('Jelly_PaintFilter_PPV')
    pp.set_editor_property('unbound', True)
    settings = pp.get_editor_property('settings')
    wb = u.WeightedBlendable(); wb.set_editor_property('weight', 1.0); wb.set_editor_property('object', build_paint_filter())
    wbs = u.WeightedBlendables(); wbs.set_editor_property('array', [wb])
    settings.set_editor_property('weighted_blendables', wbs)
    pp.set_editor_property('settings', settings)
    floor_mat = build_floor_material()
    for a in acts.get_all_level_actors():
        if a.get_actor_label() in ('Test Ground', 'Test Ground Cube'):
            a.static_mesh_component.set_material(0, floor_mat)
    les.save_current_level()
    log('level saved', LEVEL)


KUWAHARA_HLSL = r"""
// Kuwahara oil-paint filter: pick the mean of the quadrant with the lowest variance.
float2 texel = View.BufferSizeAndInvSize.zw;
float2 uv = GetDefaultSceneTextureUV(Parameters, 14);
int r = (int)clamp(Radius, 1.0, 8.0);
float3 m[4]; float3 s2[4];
for (int q = 0; q < 4; q++) { m[q] = 0; s2[q] = 0; }
for (int j = -r; j <= r; j++) {
    for (int i = -r; i <= r; i++) {
        float3 c = SceneTextureLookup(uv + float2(i, j) * texel, 14, false).rgb;
        if (i <= 0 && j <= 0) { m[0] += c; s2[0] += c * c; }
        if (i >= 0 && j <= 0) { m[1] += c; s2[1] += c * c; }
        if (i <= 0 && j >= 0) { m[2] += c; s2[2] += c * c; }
        if (i >= 0 && j >= 0) { m[3] += c; s2[3] += c * c; }
    }
}
float n = (r + 1) * (r + 1);
float best = 1e9; float3 res = Scene;
for (int k = 0; k < 4; k++) {
    float3 mu = m[k] / n;
    float3 v = abs(s2[k] / n - mu * mu);
    float sv = v.r + v.g + v.b;
    if (sv < best) { best = sv; res = mu; }
}
return res;
"""


def build_paint_filter():
    name = 'M_PP_JellyPaintFilter'
    m = eal.load_asset(f'{DEST}/{name}') or tools.create_asset(name, DEST, u.Material, u.MaterialFactoryNew())
    for e in list(lib.get_material_expressions(m)):
        lib.delete_material_expression(m, e)
    m.set_editor_property('material_domain', u.MaterialDomain.MD_POST_PROCESS)
    set_if(m, 'blendable_location', u.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    g = G(m)
    scene = g.node(u.MaterialExpressionSceneTexture, -900, 0, scene_texture_id=u.SceneTextureId.PPI_POST_PROCESS_INPUT0)
    stencil = g.node(u.MaterialExpressionSceneTexture, -900, 300, scene_texture_id=u.SceneTextureId.PPI_CUSTOM_STENCIL)
    radius = g.scalar('Brush Radius', 4.0, -900, 160, 'Paint Filter')
    strength = g.scalar('Filter Strength', 1.0, -900, 460, 'Paint Filter')
    cust = g.node(u.MaterialExpressionCustom, -500, 0, code=KUWAHARA_HLSL,
                  output_type=u.CustomMaterialOutputType.CMOT_FLOAT3, description='Kuwahara')
    ins = []
    for nm in ('Scene', 'Radius'):
        ci = u.CustomInput()
        ci.set_editor_property('input_name', nm)
        ins.append(ci)
    cust.set_editor_property('inputs', ins)
    g.link(scene, 'Color', cust, 'Scene')
    g.link(radius, '', cust, 'Radius')
    scene_rgb = g.unary(u.MaterialExpressionComponentMask, -700, -100, scene, 'Color', r=True, g=True, b=True, a=False)
    st = g.unary(u.MaterialExpressionComponentMask, -700, 300, stencil, 'Color', r=True, g=False, b=False, a=False)
    mask = g.sat(-450, 300, g.one_minus(-500, 300, g.unary(u.MaterialExpressionAbs, -550, 300,
                 g.op(u.MaterialExpressionSubtract, -600, 300, st, g.const(-700, 360, 1.0)))))
    ignore = g.scalar('Ignore Stencil', 0.0, -900, 560, 'Paint Filter')  # 1 = filter the whole screen (debug)
    keep_hl = g.scalar('Preserve Highlights', 1.0, -900, 640, 'Paint Filter')
    lum = g.dot(-600, 520, scene_rgb, g.const(-700, 560, (0.3, 0.59, 0.11)))
    keep = g.mul(-450, 520, g.smoothstep(-500, 520, g.const(-600, 600, 0.78), g.const(-600, 630, 0.92), lum), keep_hl)
    mask = g.mul(-400, 450, mask, g.one_minus(-450, 450, keep))
    mask = g.op(u.MaterialExpressionMax, -400, 400, mask, ignore)
    out = g.lerp(-250, 0, scene_rgb, cust, g.mul(-350, 300, mask, strength))
    g.out(out, '', MP.MP_EMISSIVE_COLOR)
    lib.recompile_material(m)
    eal.save_loaded_asset(m)
    log('paint filter built', m.get_path_name())
    return m


def build_floor_material():
    name = 'M_LookDev_Floor'
    m = eal.load_asset(f'{DEST}/{name}') or tools.create_asset(name, DEST, u.Material, u.MaterialFactoryNew())
    lib.delete_all_material_expressions(m)
    g = G(m)
    g.out(g.color('Floor Color', (0.62, 0.61, 0.64), -400, 0, 'Floor'), '', MP.MP_BASE_COLOR)
    g.out(g.scalar('Floor Roughness', 0.55, -400, 200, 'Floor'), '', MP.MP_ROUGHNESS)
    lib.recompile_material(m)
    eal.save_loaded_asset(m)
    return m


def main():
    tex = import_textures()
    mesh = import_mesh()
    log('mesh', mesh.get_path_name() if mesh else None)
    m = build_material(tex)
    mis = build_instances(m)
    if mesh:
        build_level(mesh, mis)
    log('DONE')


main()
