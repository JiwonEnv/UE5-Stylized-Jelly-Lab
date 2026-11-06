"""Reorganize /Game/JellyGame/Art/Jelly into type-based folders (run inside the editor via ue_run.py).

Moves go through AssetTools so references are updated; redirectors left behind are fixed
from the Content Browser (see step 2). Dead redirectors (whose target no longer exists) left
in Experiments/PainterPipeline by the old _ToDelete quarantine are deleted.
"""
import unreal as u

eal = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()

OLD = '/Game/JellyGame/Art/Jelly'
ART = '/Game/JellyGame/Art'
MOVES = {
    'SM_GummyBear': f'{ART}/Characters/Jelly',
    'M_Jelly_Gummy': f'{ART}/Materials/Jelly',
    'MI_Jelly_AmberPainted': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_Blue': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_Orange': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_PinkIridescent': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_PinkPainted': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_Raspberry': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_RedPainted': f'{ART}/Materials/Jelly/Instances',
    'MI_Jelly_Teal': f'{ART}/Materials/Jelly/Instances',
    'M_LookDev_Floor': f'{ART}/Materials/LookDev',
    'M_PP_JellyPaintFilter': f'{ART}/Materials/PostProcess',
    'T_GummyBear_BC': f'{ART}/Textures/Jelly',
    'T_GummyBear_N': f'{ART}/Textures/Jelly',
    'T_GummyBear_Mask': f'{ART}/Textures/Jelly',
    'T_GummyBear_Paint': f'{ART}/Textures/Jelly',
    'T_GummyBear_Brush': f'{ART}/Textures/Jelly',
    'T_GummyBear_Stars': f'{ART}/Textures/Jelly',
}

# 1) batch move with reference update
renames = []
for name, dst in MOVES.items():
    src = f'{OLD}/{name}'
    if not eal.does_asset_exist(src):
        print('SKIP missing', src)
        continue
    eal.make_directory(dst)
    renames.append(u.AssetRenameData(eal.load_asset(src), dst, name))
if renames:
    print('rename_assets ->', tools.rename_assets(renames), 'count', len(renames))

# 2) Redirectors left in OLD (for still-referencing maps) must be fixed in the Content Browser:
#    right-click the old folder > Update Redirector References. UE 5.8 Python exposes no
#    fixup API, and delete_asset() on a redirector path follows it and deletes the real asset.

# 3) dead redirectors from the old quarantine (target deleted)
reg = u.AssetRegistryHelpers.get_asset_registry()
dead = []
for p in eal.list_assets('/Game/JellyGame/Experiments/PainterPipeline', True, False):
    pkg = p.split('.')[0]
    a = reg.get_asset_by_object_path(p)
    if str(a.asset_class_path.asset_name) == 'ObjectRedirector':
        dead.append(pkg)
for pkg in dead:
    print('delete dead redirector', pkg, eal.delete_asset(pkg))

# 4) save everything and drop the empty old folder
eal.save_directory('/Game/JellyGame', only_if_is_dirty=True, recursive=True)
left = eal.list_assets(OLD, True, True)
print('left in old folder', left)
if not left:
    print('delete old folder', eal.delete_directory(OLD))
