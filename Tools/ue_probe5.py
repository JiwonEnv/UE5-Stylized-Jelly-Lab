import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/M_Jelly_Gummy')
for n in ('allow_translucent_custom_depth_writes', 'translucent_custom_depth_writes', 'allow_custom_depth_write'):
    try: print(n, m.get_editor_property(n))
    except Exception as e: print('no', n)
