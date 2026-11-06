import unreal as u
lib = u.MaterialEditingLibrary
m = u.load_asset('/Game/JellyGame/Art/Jelly/M_Jelly_Gummy')
root = lib.get_material_property_input_node(m, u.MaterialProperty.MP_EMISSIVE_COLOR)
seen = set(); stack = [root]; kinds = {}; params = set()
while stack:
    n = stack.pop()
    if n is None or n.get_name() in seen: continue
    seen.add(n.get_name())
    k = n.get_class().get_name(); kinds[k] = kinds.get(k, 0) + 1
    if 'Parameter' in k:
        try: params.add(str(n.get_editor_property('parameter_name')))
        except Exception: pass
    for i in lib.get_inputs_for_material_expression(m, n) or []:
        stack.append(i)
print('reachable', len(seen), 'atan2', kinds.get('MaterialExpressionArctangent2'), 'sqrt', kinds.get('MaterialExpressionSquareRoot'))
print(sorted(params))
