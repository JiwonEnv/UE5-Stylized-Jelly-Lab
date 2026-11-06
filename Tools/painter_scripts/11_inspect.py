import substance_painter.layerstack as ls, substance_painter.textureset as ts
st = ts.all_texture_sets()[0].get_stack()
for n in ls.get_root_layer_nodes(st)[:4]:
    print(n.get_name(), 'mask', n.has_mask(), n.is_mask_enabled() if n.has_mask() else '', n.get_mask_background() if n.has_mask() else '', 'active', n.active_channels)
    for fx in n.mask_effects():
        src = fx.get_source() if hasattr(fx, 'get_source') else None
        print('   fx', fx.get_name(), type(src).__name__, getattr(src, 'resource_id', None) and src.resource_id.name, 'opacity', fx.get_opacity(), fx.get_projection_mode() if hasattr(fx,'get_projection_mode') else '')
        if src is not None and hasattr(src, 'image_outputs'):
            try: print('     outputs', src.image_outputs, 'active', src.active_output)
            except Exception as e: print('     out err', e)
