"""Generate a tileable, sparse star-sparkle sprite texture (1024^2) for the jelly material.

R = 4-point stars (cross glints)       G = 6-point stars (like the amber apple)
B = small square glints (like the blue apple's tiny highlight dots)
Each channel has a handful of stars at random positions/sizes on a black background, so when it
is projected tri-planar over the object you get a few crisp sparkles, not a pattern.

    Tools/.jellyvenv/Scripts/python Tools/GenerateStarSparkleTexture.py
"""
from pathlib import Path
import numpy as np
from PIL import Image

N = 1024
OUT = Path(__file__).resolve().parents[1] / 'SourceAssets' / 'Characters' / 'Jelly' / 'Textures' / 'JellyStarSparkles.png'
rng = np.random.default_rng(77)
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)


def star(img, cx, cy, radius, points, rot, core=0.22, sharp=10.0):
    for ox in (-N, 0, N):          # tileable
        for oy in (-N, 0, N):
            dx, dy = xx - (cx + ox), yy - (cy + oy)
            r = np.hypot(dx, dy) / radius
            if r.min() > 1.2:
                continue
            th = np.arctan2(dy, dx) + rot
            spikes = np.abs(np.cos(th * points / 2)) ** sharp
            prof = core + (1 - core) * spikes
            s = np.clip(1 - r / prof, 0, 1) ** 1.6
            glow = np.clip(1 - r / 0.35, 0, 1) ** 2
            np.maximum(img, np.clip(s + glow * 0.6, 0, 1), out=img)


def square(img, cx, cy, half, rot):
    c, s = np.cos(rot), np.sin(rot)
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            dx, dy = xx - (cx + ox), yy - (cy + oy)
            u, v = dx * c + dy * s, -dx * s + dy * c
            d = np.maximum(np.abs(u), np.abs(v)) - half
            np.maximum(img, np.clip(0.5 - d / 1.2, 0, 1), out=img)


R = np.zeros((N, N), np.float32); G = np.zeros_like(R); B = np.zeros_like(R)
for _ in range(7):
    star(R, rng.random() * N, rng.random() * N, rng.uniform(40, 95), 4, rng.uniform(0, 0.3))
for _ in range(7):
    star(G, rng.random() * N, rng.random() * N, rng.uniform(40, 95), 6, rng.uniform(0, 0.5), core=0.18, sharp=14.0)
for _ in range(14):
    square(B, rng.random() * N, rng.random() * N, rng.uniform(6, 16), rng.uniform(-0.3, 0.3))

OUT.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray(np.uint8(np.stack([R, G, B], -1) * 255 + 0.5)).save(OUT)
print('wrote', OUT)
