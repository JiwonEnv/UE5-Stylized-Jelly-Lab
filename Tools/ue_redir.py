import unreal as u
reg = u.AssetRegistryHelpers.get_asset_registry()
for p in u.EditorAssetLibrary.list_assets('/Game/JellyGame/Art/Jelly', True, True):
    a = reg.get_asset_by_object_path(p)
    print(str(a.asset_class_path.asset_name), p)
