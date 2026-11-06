"""Generate an original, generic gummy-bear test mesh (single watertight surface + UVs).

A soft, sitting bear made from smooth-blended SDF primitives, so translucency/thickness
reads correctly (thin ears/feet vs. thick belly). Output: OBJ (Y-up, centimeters).

Run with the Tools/.jellyvenv interpreter (needs numpy, scikit-image, xatlas):
    Tools/.jellyvenv/Scripts/python Tools/GenerateGummyBearMesh.py
"""
from pathlib import Path
import numpy as np
from skimage import measure
import xatlas

OUT = Path(__file__).resolve().parents[1] / 'SourceAssets' / 'Characters' / 'Jelly' / 'SM_GummyBear.obj'
STEP = 0.32  # voxel size in cm


def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def ellipsoid(p, c, r):
    q = (p - np.asarray(c)) / np.asarray(r)
    return (np.linalg.norm(q, axis=-1) - 1.0) * min(r)


def capsule(p, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / (ba @ ba), 0, 1)
    return np.linalg.norm(pa - h[..., None] * ba, axis=-1) - r


def bear_sdf(p):
    d = ellipsoid(p, (0, 13, 0), (11.5, 13, 8.5))                      # body
    d = smin(d, ellipsoid(p, (0, 32, 0.5), (10.5, 9.2, 8.5)), 3.0)     # head
    for s in (-1, 1):
        d = smin(d, ellipsoid(p, (s * 7.6, 40.2, -0.5), (3.9, 3.9, 2.6)), 1.6)   # ears
        d = smin(d, capsule(p, (s * 9.5, 22, 1.5), (s * 12.5, 13, 5.5), 3.4), 2.4)  # arms
        d = smin(d, ellipsoid(p, (s * 6.4, 3.6, 4.5), (4.9, 4.2, 6.8)), 2.2)     # legs
    d = smin(d, ellipsoid(p, (0, 29.4, 7.0), (4.6, 3.6, 3.0)), 1.6)    # muzzle
    d = smin(d, ellipsoid(p, (0, 31.0, 9.6), (1.5, 1.1, 0.9)), 0.6)    # nose
    for s in (-1, 1):
        d = smax(d, -ellipsoid(p, (s * 3.6, 34.0, 8.6), (1.0, 1.2, 0.9)), 0.6)   # eye dimples
        d = smax(d, -ellipsoid(p, (s * 7.6, 40.0, 1.6), (2.1, 2.1, 1.0)), 0.7)   # inner-ear dip
    d = smin(d, ellipsoid(p, (0, 11, 6.8), (7.5, 8.5, 2.5)), 2.0)      # belly bulge
    return d


def main():
    xs = np.arange(-20, 20 + STEP, STEP)
    ys = np.arange(-3, 48 + STEP, STEP)
    zs = np.arange(-13, 17 + STEP, STEP)
    grid = np.stack(np.meshgrid(xs, ys, zs, indexing='ij'), axis=-1).astype(np.float32)
    sdf = bear_sdf(grid.reshape(-1, 3)).reshape(grid.shape[:3])
    sdf = np.maximum(sdf, -(grid[..., 1] - 0.0))  # flat-ish bottom so it sits on the floor

    verts, faces, _, _ = measure.marching_cubes(sdf, 0.0, spacing=(STEP, STEP, STEP))
    verts += np.array([xs[0], ys[0], zs[0]])
    faces = faces[:, ::-1]  # outward winding

    # Smooth normals from the SDF gradient.
    e = 0.05
    n = np.stack([bear_sdf(verts + o) - bear_sdf(verts - o) for o in np.eye(3) * e], axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9

    atlas = xatlas.Atlas()
    atlas.add_mesh(verts.astype(np.float32), faces.astype(np.uint32), n.astype(np.float32))
    pack = xatlas.PackOptions(); pack.resolution = 2048; pack.padding = 6
    atlas.generate(pack_options=pack)
    vmap, idx, uvs = atlas[0]

    v, nn = verts[vmap], n[vmap]
    v[:, 1] -= v[:, 1].min()  # stand on y=0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, 'w') as f:
        f.write('# Generic gummy bear test mesh (generated)\no SM_GummyBear\n')
        f.writelines(f'v {a:.4f} {b:.4f} {c:.4f}\n' for a, b, c in v)
        f.writelines(f'vt {a:.6f} {b:.6f}\n' for a, b in uvs)
        f.writelines(f'vn {a:.5f} {b:.5f} {c:.5f}\n' for a, b, c in nn)
        f.writelines(f'f {a+1}/{a+1}/{a+1} {b+1}/{b+1}/{b+1} {c+1}/{c+1}/{c+1}\n' for a, b, c in idx)
    print(f'wrote {OUT} verts={len(v)} tris={len(idx)} height={v[:,1].max():.1f}cm')


if __name__ == '__main__':
    main()
