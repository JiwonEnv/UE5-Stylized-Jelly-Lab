import substance_painter.layerstack as ls
print([x for x in dir(ls.LevelsEffectNode) if not x.startswith('_')])
import dataclasses; print([f.name for f in dataclasses.fields(ls.LevelsParams)] if dataclasses.is_dataclass(ls.LevelsParams) else dir(ls.LevelsParams))
