"""Move every material / texture that the jelly look-dev no longer uses into /Game/_ToDelete.
Nothing is deleted: the folder can be reviewed and deleted from the Content Browser."""
import unreal as u
eal = u.EditorAssetLibrary
reg = u.AssetRegistryHelpers.get_asset_registry()
KEEP_CLASSES = ()
moved = []
cands = []
for p in eal.list_assets('/Game/JellyGame/Experiments/PainterPipeline', True, False):
    a = reg.get_asset_by_object_path(p)
    if str(a.asset_class_path.asset_name) in ('Material', 'MaterialInstanceConstant', 'Texture2D'):
        cands.append(p.split('.')[0])
for n in ('MI_Jelly_Amber', 'MI_Jelly_Pink', 'MI_Jelly_Mint'):
    cands.append('/Game/JellyGame/Art/Jelly/' + n)
for src in cands:
    if not eal.does_asset_exist(src):
        continue
    dst = src.replace('/Game/JellyGame/', '/Game/_ToDelete/JellyGame/')
    if eal.rename_asset(src, dst):
        moved.append(dst)
print('moved', len(moved))
for m in moved: print('  ', m)
