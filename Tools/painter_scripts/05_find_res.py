import substance_painter.resource as r
def us(x):
    try: return [str(z).split('.')[-1] for z in x.usages()]
    except Exception: return ['?']
for q in ['Gaussian', 'Spots', 'BnW', 'Dirt', 'Grunge Map', 'Mask Editor', 'Position', 'Thickness', 'Curvature', 'Blur', 'Water', 'Smudge', 'Gradient', '3D Worley', 'Worley', 'Dots', 'Speckle', 'Sparkle', 'Sugar']:
    res = r.search(q)
    print(q, '->', [(x.identifier().name, us(x)) for x in res if x.identifier().context=='starter_assets'][:10])
