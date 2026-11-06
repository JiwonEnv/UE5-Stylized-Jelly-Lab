import unreal as u
eal = u.EditorAssetLibrary
reg = u.AssetRegistryHelpers.get_asset_registry()
opts = u.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
reds = []
for p in eal.list_assets('/Game/JellyGame', True, True):
    a = reg.get_asset_by_object_path(p)
    if str(a.asset_class_path.asset_name) == 'ObjectRedirector':
        reds.append(p.split('.')[0])
refs = set()
for r in reds:
    for x in reg.get_referencers(r, opts) or []:
        x = str(x)
        if x not in reds:
            refs.add(x)
print('redirectors', len(reds), 'referencers', sorted(refs))
les = u.get_editor_subsystem(u.LevelEditorSubsystem)
world = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
cur = world.get_path_name().split('.')[0]
for x in sorted(refs):
    if x == cur:
        world.modify(); les.save_current_level(); print('resaved level', x)
    else:
        eal.load_asset(x); print('resave', x, eal.save_asset(x, only_if_is_dirty=False))
still = []
for r in reds:
    left = [str(x) for x in (reg.get_referencers(r, opts) or []) if str(x) not in reds]
    if left:
        still.append((r, left))
    else:
        print('delete redirector', r, eal.delete_asset(r))
print('still referenced', still)
