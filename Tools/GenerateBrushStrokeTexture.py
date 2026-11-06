"""Generate a tileable painterly brush-stroke texture (1024^2) for the jelly material.

R = stroke ID      : each stroke is one flat random value (used to break shading into stroke-shaped
                     patches and to jitter hue per stroke)
G = highlight dash : sparse short thin white dashes (painted highlight marks)
B = bristle        : streaks running along each stroke (dry-brush texture)

    Tools/.jellyvenv/Scripts/python Tools/GenerateBrushStrokeTexture.py
"""
from pathlib import Path
import numpy as np
from PIL import Image

N = 1024
OUT = Path(__file__).resolve().parents[1] / 'SourceAssets' / 'Characters' / 'Jelly' / 'Textures' / 'JellyBrushStrokes.png'
rng = np.random.default_rng(20261106)


def value_noise(scale, seed):
    r = np.random.default_rng(seed)
    g = r.random((scale, scale))
    img = Image.fromarray((g * 255).astype(np.uint8)).resize((N, N), Image.Resampling.BICUBIC)
    a = np.asarray(img, np.float32) / 255
    return a


angle_field = value_noise(6, 3) * np.pi * 1.4 + 0.3   # coherent stroke directions
edge_noise = value_noise(256, 9)                       # ragged edges

R = np.full((N, N), 0.5, np.float32)
G = np.zeros((N, N), np.float32)
B = np.full((N, N), 0.5, np.float32)


def stamp(cx, cy, length, width, ang, value, target, bristle=None, soft=1.5):
    ca, sa = np.cos(ang), np.sin(ang)
    ext = int(length / 2 + width) + 3
    xs = np.arange(int(cx) - ext, int(cx) + ext)
    ys = np.arange(int(cy) - ext, int(cy) + ext)
    X, Y = np.meshgrid(xs, ys)
    dx, dy = X - cx, Y - cy
    u = dx * ca + dy * sa          # along stroke
    v = -dx * sa + dy * ca         # across stroke
    # tapered ends, slightly wobbly width
    half_w = width / 2 * (0.75 + 0.25 * np.cos(np.clip(u / (length / 2), -1, 1) * np.pi / 2))
    xi, yi = X % N, Y % N
    rag = (edge_noise[yi, xi] - 0.5) * width * 0.35
    d_across = np.abs(v) - half_w - rag
    d_along = np.abs(u) - length / 2
    d = np.maximum(d_across, d_along)
    alpha = np.clip(0.5 - d / soft, 0, 1)
    m = alpha > 0
    target[yi[m], xi[m]] = target[yi[m], xi[m]] * (1 - alpha[m]) + value * alpha[m]
    if bristle is not None:
        streak = 0.5 + 0.5 * np.sin(v * (9.0 / max(width, 1)) * np.pi + rng.random() * 6.28)
        streak = streak * 0.6 + 0.4 * edge_noise[(yi * 3) % N, (xi * 3) % N]
        bristle[yi[m], xi[m]] = bristle[yi[m], xi[m]] * (1 - alpha[m]) + streak[m] * alpha[m]


# big + medium strokes, painted in layers
for count, lmin, lmax, wmin, wmax in ((260, 120, 260, 40, 80), (700, 60, 150, 20, 46)):
    for _ in range(count):
        cx, cy = rng.random() * N, rng.random() * N
        ang = angle_field[int(cy) % N, int(cx) % N] + rng.normal(0, 0.25)
        stamp(cx, cy, rng.uniform(lmin, lmax), rng.uniform(wmin, wmax), ang, rng.random(), R, B)

# highlight dashes: short, thin, mostly aligned with the local stroke direction
for _ in range(420):
    cx, cy = rng.random() * N, rng.random() * N
    ang = angle_field[int(cy) % N, int(cx) % N] + rng.normal(0, 0.5)
    stamp(cx, cy, rng.uniform(14, 60), rng.uniform(3, 9), ang, 1.0, G, soft=1.0)

OUT.parent.mkdir(parents=True, exist_ok=True)
rgb = np.stack([R, G, B], -1)
Image.fromarray(np.uint8(np.clip(rgb, 0, 1) * 255 + 0.5)).save(OUT)
print('wrote', OUT, 'R std %.3f G mean %.3f' % (R.std(), G.mean()))
