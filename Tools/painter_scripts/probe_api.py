import substance_painter.baking as b, substance_painter.layerstack as ls, substance_painter.project as pr, substance_painter.source as src
for mod in (b, ls, pr, src):
    print(mod.__name__, [x for x in dir(mod) if not x.startswith('_')])
print(b.BakingParameters.__doc__[:1500] if b.BakingParameters.__doc__ else '')
print([x for x in dir(b.BakingParameters) if not x.startswith('_')])
print(pr.Settings.__doc__[:1200] if pr.Settings.__doc__ else '')
