"""Bake thickness / curvature / AO for SM_GummyBear from its analytic SDF (Painter 12.2's
ray bakers return blank maps for this mesh, while Position bakes fine).

Per-vertex values are computed from the SDF, then rasterised into UV space (2048) with padding.
Output: SourceAssets/Characters/Jelly/MeshMaps/GummyBear_{Thickness,Curvature,AO}.png

    Tools/.jellyvenv/Scripts/python Tools/BakeGummyBearMeshMaps.py
"""
from pathlib import Path
import numpy as np
from PIL import Image
from GenerateGummyBearMesh import bear_sdf, OUT as OBJ

RES = 2048
OUT_DIR = OBJ.parent / 'MeshMaps'


def load_obj(path):
    v, vt, vn, f = [], [], [], []
    for line in open(path):
        if line.startswith('v '):
            v.append(line.split()[1:4])
        elif line.startswith('vt '):
            vt.append(line.split()[1:3])
        elif line.startswith('vn '):
            vn.append(line.split()[1:4])
        elif line.startswith('f '):
            f.append([int(p.split('/')[0]) - 1 for p in line.split()[1:4]])
    return (np.array(v, np.float64), np.array(vt, np.float64), np.array(vn, np.float64), np.array(f, np.int64))


def sdf(p, shift):
    return bear_sdf(p - shift)


def thickness(p, n, shift, rays=24, max_d=24.0, steps=48):
    rng = np.random.default_rng(7)
    acc = np.zeros(len(p))
    for _ in range(rays):
        # cosine-ish cone around -n (spread ~55deg)
        r = rng.normal(size=(len(p), 3))
        r -= (r * n).sum(1, keepdims=True) * n
        r /= np.linalg.norm(r, axis=1, keepdims=True) + 1e-9
        a = np.sqrt(rng.random((len(p), 1))) * 0.95
        d = -n * np.sqrt(1 - a ** 2) + r * a
        t = np.full(len(p), 0.08)
        alive = np.ones(len(p), bool)
        for _ in range(steps):
            q = p + d * t[:, None]
            s = sdf(q[alive], shift)
            step = np.maximum(-s, 0.06)
            inside = s < 0
            idx = np.flatnonzero(alive)
            t[idx[inside]] += step[inside]
            alive[idx[~inside]] = False
            alive &= t < max_d
            if not alive.any():
                break
        acc += np.minimum(t, max_d)
    return acc / rays


def curvature(p, n, shift, e=0.6):
    # mean curvature ~ laplacian of SDF; positive = convex
    lap = sum(sdf(p + o, shift) + sdf(p - o, shift) for o in np.eye(3) * e) - 6 * sdf(p, shift)
    return lap / (e * e)


def ambient_occlusion(p, n, shift):
    occ, w = np.zeros(len(p)), 1.0
    for i in range(1, 6):
        h = 0.8 * i
        occ += w * (h - sdf(p + n * h, shift))
        w *= 0.6
    return np.clip(1 - 0.18 * occ, 0, 1)


def rasterise(uv, faces, values, res=RES):
    img = np.zeros((res, res), np.float32)
    cov = np.zeros((res, res), bool)
    P = uv * res - 0.5
    P[:, 1] = res - 1 - P[:, 1]  # v up -> image rows down
    for tri in faces:
        a, b, c = P[tri]
        x0, y0 = np.floor(np.minimum(np.minimum(a, b), c)).astype(int)
        x1, y1 = np.ceil(np.maximum(np.maximum(a, b), c)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, res - 1), min(y1, res - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / den
        w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / den
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-3) & (w1 >= -1e-3) & (w2 >= -1e-3)
        if not m.any():
            continue
        va, vb, vc = values[tri]
        img[ys[m], xs[m]] = w0[m] * va + w1[m] * vb + w2[m] * vc
        cov[ys[m], xs[m]] = True
    # padding: grow coverage outward
    for _ in range(24):
        if cov.all():
            break
        acc = np.zeros_like(img); cnt = np.zeros_like(img)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sv = np.roll(np.roll(img, dy, 0), dx, 1); sc = np.roll(np.roll(cov, dy, 0), dx, 1)
            acc += sv * sc; cnt += sc
        grow = (~cov) & (cnt > 0)
        img[grow] = acc[grow] / cnt[grow]; cov |= grow
    img[~cov] = img[cov].mean()
    return img


def smooth_vertices(values, v, faces, iters=8):
    """Average with neighbours; vertices are split along UV seams, so weld by position first."""
    key = np.round(v / 0.05).astype(np.int64)
    _, weld = np.unique(key, axis=0, return_inverse=True)
    weld = weld.ravel()
    n = weld.max() + 1
    f = weld[faces]
    edges = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    edges = np.concatenate([edges, edges[:, ::-1]])
    val = np.bincount(weld, values, n) / np.bincount(weld, None, n)
    deg = np.bincount(edges[:, 0], None, n)
    for _ in range(iters):
        val = 0.5 * val + 0.5 * np.bincount(edges[:, 0], val[edges[:, 1]], n) / np.maximum(deg, 1)
    return val[weld]


def save(name, a):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.uint8(np.clip(a, 0, 1) * 255 + 0.5)).save(OUT_DIR / f'GummyBear_{name}.png')


def main():
    v, vt, vn, f = load_obj(OBJ)
    # find the vertical offset applied when the OBJ was written (stand on y=0)
    cands = np.linspace(-4, 4, 801)
    sample = v[:: max(1, len(v) // 2000)]
    errs = [np.abs(bear_sdf(sample - np.array([0, s, 0]))).mean() for s in cands]
    shift = np.array([0, cands[int(np.argmin(errs))], 0])
    print('shift', shift, 'mean |sdf|', min(errs))

    n = vn / np.linalg.norm(vn, axis=1, keepdims=True)
    th = thickness(v, n, shift)
    cu = curvature(v, n, shift)
    ao = ambient_occlusion(v, n, shift)
    print('thickness cm: min %.2f p50 %.2f max %.2f' % (th.min(), np.median(th), th.max()))

    th = smooth_vertices(th, v, f, 10)
    cu = smooth_vertices(cu, v, f, 2)
    print('smoothed thickness cm: min %.2f p50 %.2f max %.2f' % (th.min(), np.median(th), th.max()))
    th_n = np.clip((th - 3.0) / 15.0, 0, 1)                   # ~3cm -> 0 (ears/feet rims), ~18cm -> 1 (belly)
    cu_n = np.clip(0.5 + cu * 0.9, 0, 1)                      # 0.5 flat, >0.5 convex
    save('Thickness', rasterise(vt, f, th_n))
    save('Curvature', rasterise(vt, f, cu_n))
    save('AO', rasterise(vt, f, ao))
    print('saved to', OUT_DIR)


if __name__ == '__main__':
    main()
