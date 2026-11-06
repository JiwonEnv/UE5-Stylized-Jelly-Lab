import unreal as u
reg = u.AssetRegistryHelpers.get_asset_registry()
eal = u.EditorAssetLibrary
paths = eal.list_assets('/Game/JellyGame', True, False)
opts = u.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True)
for p in sorted(paths):
    pkg = p.split('.')[0]
    a = reg.get_asset_by_object_path(p)
    cls = str(a.asset_class_path.asset_name)
    refs = reg.get_referencers(pkg, opts) or []
    print(cls, '|', pkg, '| refs:', ','.join(sorted(str(r).split('/')[-1] for r in refs)))
