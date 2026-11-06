import unreal as u
m = u.load_asset('/Game/JellyGame/Art/Jelly/M_Jelly_Gummy')
for name in ('editor_only_data', 'expressions', 'expression_collection'):
    try:
        v = m.get_editor_property(name); print(name, type(v))
    except Exception as e: print('no', name, e)
print([x for x in dir(u.MaterialEditingLibrary) if 'xpression' in x])
