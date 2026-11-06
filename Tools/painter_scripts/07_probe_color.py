import substance_painter.colormanagement as cm, substance_painter.layerstack as ls, substance_painter.textureset as ts
import _substance_painter.colormanagement as pcm
st=ts.all_texture_sets()[0].get_stack()
n=ls.get_root_layer_nodes(st)[-1]
print('private cs', [x for x in dir(pcm) if not x.startswith('__')])
for v in (0.35,):
    try: n.set_source(ls.ChannelType.Height, v); print('float ok')
    except Exception as e: print('float no', e)
try:
    print('avail', pcm.list_available_color_spaces() if hasattr(pcm,'list_available_color_spaces') else 'n/a')
except Exception as e: print(e)
