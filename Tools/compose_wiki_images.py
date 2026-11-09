"""Build the README / wiki images from the raw shots of capture_wiki_images.py.

    python Tools/compose_wiki_images.py
Output: Docs/wiki/images/*.jpg
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / 'Saved' / 'Screenshots' / 'WindowsEditor'
OUT = ROOT / 'Docs' / 'wiki' / 'images'
OUT.mkdir(parents=True, exist_ok=True)
FONT = 'C:/Windows/Fonts/malgunbd.ttf'
FONT_R = 'C:/Windows/Fonts/malgun.ttf'
CROP = (660, 140, 1260, 840)      # one bear, 600x700 from the 1920x1080 shot
TIGHT = (720, 200, 1200, 848)     # tighter crop for the banner


def raw(name, box=CROP):
    return Image.open(SHOTS / f'wiki_{name}.png').convert('RGB').crop(box)


def font(size, bold=True):
    return ImageFont.truetype(FONT if bold else FONT_R, size)


def label_bar(img, text, sub=None):
    w, h = img.size
    bar = 64 if sub else 46
    out = Image.new('RGB', (w, h + bar), (24, 24, 30))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    d.text((w // 2, h + 8), text, font=font(22), fill=(240, 240, 245), anchor='mt')
    if sub:
        d.text((w // 2, h + 38), sub, font=font(16, False), fill=(170, 170, 185), anchor='mt')
    return out


def row(images, gap=8, bg=(24, 24, 30)):
    w = sum(i.width for i in images) + gap * (len(images) - 1)
    h = max(i.height for i in images)
    out = Image.new('RGB', (w, h), bg)
    x = 0
    for i in images:
        out.paste(i, (x, 0)); x += i.width + gap
    return out


def save(img, name):
    img.save(OUT / f'{name}.jpg', quality=88, optimize=True)
    print('wrote', name)


GALLERY = [  # development order
    ('evo1_flat', '① 단색', '초기: 색 하나'),
    ('evo2_thickness', '② 두께', '얇으면 밝고 두꺼우면 진하게'),
    ('evo3_thin_translucent', '③ 투과', 'Thin Translucent · Raspberry'),
    ('evo4_iridescent', '④ 다색 빛', 'PinkIridescent'),
    ('evo5_painted', '⑤ 그림체', 'AmberPainted'),
    ('evo6_brush', '⑥ 붓질 + 유화', 'PinkPainted'),
    ('evo7_combined', '⑦ 통합', 'RedPainted'),
    ('evo8_inner_glitter', '⑧ 속 글리터', 'InnerGlitter (최신)'),
]


def gallery():
    for key, title, sub in GALLERY:
        save(label_bar(raw(key).resize((420, 490), Image.LANCZOS), title, sub), key)
    # banner: tight crops side by side + title
    tiles = [raw(k, TIGHT).resize((180, 243), Image.LANCZOS) for k, _, _ in GALLERY]
    strip = row(tiles, gap=0)
    banner = Image.new('RGB', (strip.width, strip.height + 120), (18, 18, 26))
    banner.paste(strip, (0, 120))
    d = ImageDraw.Draw(banner)
    d.text((32, 22), 'UE5 Stylized Jelly Lab', font=font(46), fill=(255, 236, 244))
    d.text((34, 80), '두께로 색이 달라지는 젤리 · 다색 빛 · 붓질 그림체 — Unreal 5.8 Material Graph + Substance Painter',
           font=font(19, False), fill=(190, 185, 205))
    save(banner, 'banner')


def layers():
    names = [('layer1_color', '① 색', '단색'), ('layer2_thickness', '② + 두께', '얇은 곳 밝게 · 두꺼운 곳 진하게'),
             ('layer3_transparency', '③ + 투명', '뒤가 젤리 색으로 비침'), ('layer4_shine', '④ + 반짝임', '하이라이트 · 속 빛')]
    save(row([label_bar(raw(k).resize((330, 385), Image.LANCZOS), t, s) for k, t, s in names]), 'layers')


SLIDERS = [
    ('Density', [0.5, 1.6, 3.5]), ('Opacity Thick', [0.2, 0.5, 0.95]),
    ('Transmission Brightness', [0.0, 0.6, 1.5]), ('Inner Glow', [0.0, 1.1, 3.0]),
    ('Highlight Intensity', [0.0, 2.2, 5.0]), ('Normal Strength', [0.0, 0.18, 0.8]),
    ('Gradient Amount', [0.0, 0.5, 1.0]), ('Rim Light A', [0.0, 4.0, 8.0]), ('Iridescence', [0.0, 0.6, 2.0]),
    ('Paint Style', [0.0, 0.5, 1.0]), ('Cel Amount', [0.0, 0.5, 1.0]), ('Brush Amount', [0.0, 1.0, 2.0]),
    ('Outline Amount', [0.0, 1.0, 2.5]), ('Edge Line', [0.0, 0.4, 1.0]), ('Star Glint', [0.0, 3.0, 8.0]),
]


def sliders():
    for param, values in SLIDERS:
        key = param.lower().replace(' ', '_')
        tiles = [label_bar(raw(f'slider_{key}_{i}').resize((300, 350), Image.LANCZOS), f'{param} = {v:g}')
                 for i, v in enumerate(values)]
        save(row(tiles), f'slider_{key}')
    FB = (845, 330, 1075, 598)
    save(row([label_bar(raw('filter_0', FB).resize((360, 420), Image.LANCZOS), '유화 필터 끔', '스텐실 0'),
              label_bar(raw('filter_1', FB).resize((360, 420), Image.LANCZOS), '유화 필터 켬', '스텐실 1')]), 'filter')


if __name__ == '__main__':
    import sys
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if which in ('all', 'gallery'):
        gallery()
    if which in ('all', 'layers'):
        layers()
    if which in ('all', 'sliders'):
        sliders()
