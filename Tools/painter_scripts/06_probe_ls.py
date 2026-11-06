import substance_painter.layerstack as ls, substance_painter.source as so, substance_painter.textureset as ts, inspect
pub=lambda c:[x for x in dir(c) if not x.startswith('_')]
print('FillLayer', pub(ls.FillLayerNode))
print('FillEffect', pub(ls.FillEffectNode))
print('SourceSubstance', pub(so.SourceSubstance))
print('set_source:', (ls.FillLayerNode.set_source.__doc__ or '')[:900])
print('add_mask:', (ls.FillLayerNode.add_mask.__doc__ or '')[:300])
print('set_opacity:', (ls.FillLayerNode.set_opacity.__doc__ or '')[:300])
print('LevelsParams', (ls.LevelsParams.__doc__ or '')[:600])
print('Stack.add_channel', (ts.Stack.add_channel.__doc__ or '')[:500])
print('ChannelType', list(ls.ChannelType.__members__))
print('ChannelFormat', list(ts.ChannelFormat.__members__))
