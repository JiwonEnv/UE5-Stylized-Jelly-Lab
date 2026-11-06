import substance_painter.resource as r
for q in ['brushed', 'stroke', 'paint', 'brush', 'scratches', 'streak', 'fibers', 'wipe']:
    print(q, [x.identifier().name for x in r.search(q) if x.identifier().context == 'starter_assets' and 'PROCEDURAL' in [str(z).split('.')[-1] for z in (x.usages() if True else [])]][:10])
