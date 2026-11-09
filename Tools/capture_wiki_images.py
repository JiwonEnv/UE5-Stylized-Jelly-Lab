"""Capture all wiki screenshots from the open UE editor (L_JellyLookDev).

    python Tools/capture_wiki_images.py          (needs UE Python Remote Execution)
Raw shots land in Saved/Screenshots/WindowsEditor/wiki_*.png; Tools/compose_wiki_images.py builds the
final images. Uses a temporary bear + temporary instance, removed at the end; the level is not saved.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'Tools'
SAVED = ROOT / 'Saved'
SHOTS = SAVED / 'Screenshots' / 'WindowsEditor'


def ue(script, payload_file, payload):
    (SAVED / payload_file).write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
    out = subprocess.run([sys.executable, '-I', str(TOOLS / 'ue_run.py'), str(TOOLS / script), '120'],
                         capture_output=True, text=True).stdout
    if 'SUCCESS' not in out:
        raise RuntimeError(out[-2000:])


def shot(name, one='Sweep', dist=1.0):
    ue('ue_shot.py', 'jelly_shot.json', {'side': 1, 'one': one, 'name': 'wiki_' + name, 'dist': dist})
    time.sleep(7)
    if not (SHOTS / f'wiki_{name}.png').exists():
        time.sleep(6)
    print('shot', name, flush=True)


def act(payload, settle=2.5):
    ue('ue_wiki_shot.py', 'wiki_shot.json', payload)
    time.sleep(settle)


GALLERY = [  # development order: (file, instance or None=set, params, paint filter)
    ('evo1_flat', None, {'Density': 0.0, 'Opacity Thin': 1.0, 'Opacity Thick': 1.0, 'Transmission Brightness': 0.0,
                         'Inner Glow': 0.0, 'Highlight Intensity': 0.0, 'Normal Strength': 0.0}, False),
    ('evo2_thickness', None, {'Opacity Thin': 1.0, 'Opacity Thick': 1.0, 'Transmission Brightness': 0.0,
                              'Inner Glow': 0.0, 'Highlight Intensity': 0.0, 'Normal Strength': 0.0}, False),
    ('evo3_thin_translucent', 'MI_Jelly_Raspberry', None, False),
    ('evo4_iridescent', 'MI_Jelly_PinkIridescent', None, False),
    ('evo5_painted', 'MI_Jelly_AmberPainted', None, True),
    ('evo6_brush', 'MI_Jelly_PinkPainted', None, True),
    ('evo7_combined', 'MI_Jelly_RedPainted', None, True),
    ('evo8_inner_glitter', 'MI_Jelly_RedPainted_InnerGlitter_TexParam', None, True),
]

FLAT = {'Opacity Thin': 1.0, 'Opacity Thick': 1.0, 'Transmission Brightness': 0.0, 'Inner Glow': 0.0,
        'Highlight Intensity': 0.0, 'Normal Strength': 0.0}
LAYERS = [
    ('layer1_color', dict(FLAT, Density=0.0)),
    ('layer2_thickness', dict(FLAT)),
    ('layer3_transparency', {'Inner Glow': 0.0, 'Highlight Intensity': 0.0}),
    ('layer4_shine', {}),
]

SLIDERS = [  # (base preset, parameter, values, paint filter)
    ('MI_Jelly_Raspberry', 'Density', [0.5, 1.6, 3.5], False),
    ('MI_Jelly_Raspberry', 'Opacity Thick', [0.2, 0.5, 0.95], False),
    ('MI_Jelly_Raspberry', 'Transmission Brightness', [0.0, 0.6, 1.5], False),
    ('MI_Jelly_Raspberry', 'Inner Glow', [0.0, 1.1, 3.0], False),
    ('MI_Jelly_Raspberry', 'Highlight Intensity', [0.0, 2.2, 5.0], False),
    ('MI_Jelly_Raspberry', 'Normal Strength', [0.0, 0.18, 0.8], False),
    ('MI_Jelly_PinkIridescent', 'Gradient Amount', [0.0, 0.5, 1.0], False),
    ('MI_Jelly_PinkIridescent', 'Rim Light A', [0.0, 4.0, 8.0], False),
    ('MI_Jelly_PinkIridescent', 'Iridescence', [0.0, 0.6, 2.0], False),
    ('MI_Jelly_RedPainted', 'Paint Style', [0.0, 0.5, 1.0], True),
    ('MI_Jelly_RedPainted', 'Cel Amount', [0.0, 0.5, 1.0], False),
    ('MI_Jelly_RedPainted', 'Brush Amount', [0.0, 1.0, 2.0], False),
    ('MI_Jelly_RedPainted', 'Outline Amount', [0.0, 1.0, 2.5], False),
    ('MI_Jelly_RedPainted', 'Edge Line', [0.0, 0.4, 1.0], True),
    ('MI_Jelly_AmberPainted', 'Star Glint', [0.0, 3.0, 8.0], False),
]


def slug(s):
    return s.lower().replace(' ', '_')


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else 'all'
    act({'action': 'setup'})
    try:
        if only in ('all', 'gallery'):
            for name, mi, params, stencil in GALLERY:
                if mi:
                    act({'action': 'assign', 'mi': mi, 'stencil': stencil})
                else:
                    act({'action': 'set', 'base': 'MI_Jelly_Raspberry', 'params': params, 'stencil': stencil})
                shot(name)
        if only in ('all', 'layers'):
            for name, params in LAYERS:
                act({'action': 'set', 'base': 'MI_Jelly_Raspberry', 'params': params, 'stencil': False})
                shot(name)
        pick = set(sys.argv[2].split(',')) if len(sys.argv) > 2 else None
        if only in ('all', 'sliders'):
            for base, param, values, stencil in SLIDERS:
                if pick and slug(param) not in pick:
                    continue
                for i, v in enumerate(values):
                    act({'action': 'set', 'base': base, 'params': {param: v}, 'stencil': stencil})
                    shot(f'slider_{slug(param)}_{i}')
            if not pick or 'filter' in pick:
                for i, on in enumerate((False, True)):
                    act({'action': 'set', 'base': 'MI_Jelly_RedPainted', 'params': {}, 'stencil': on})
                    shot(f'filter_{i}', dist=2.6)  # farther: the filter works in screen pixels
    finally:
        act({'action': 'teardown'})
    if only in ('all', 'banner'):
        shot('banner', one='')
    print('DONE', flush=True)


if __name__ == '__main__':
    main()
