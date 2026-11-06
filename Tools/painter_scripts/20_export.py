import substance_painter as sp
OUT = 'E:/Project/Unreal-Engine-5-Jelly-Game/SourceAssets/Characters/Jelly/Textures'
def rgb(name, mtype='documentMap'):
    return [{'destChannel': c, 'srcChannel': c, 'srcMapType': mtype, 'srcMapName': name} for c in 'RGB']
def gray(dest, name, mtype):
    return {'destChannel': dest, 'srcChannel': 'L', 'srcMapType': mtype, 'srcMapName': name}
preset = {'name': 'JellyGummy', 'maps': [
    {'fileName': 'GummyBear_BaseColor', 'channels': rgb('basecolor')},
    {'fileName': 'GummyBear_Normal', 'channels': rgb('Normal_DirectX', 'virtualMap')},
    {'fileName': 'GummyBear_Mask', 'channels': [
        gray('R', 'user2', 'documentMap'),
        gray('B', 'user0', 'documentMap'), gray('A', 'user1', 'documentMap')]},
    {'fileName': 'GummyBear_Paint', 'channels': [
        gray('R', 'user4', 'documentMap'), gray('G', 'user5', 'documentMap')]},
]}
cfg = {'exportPath': OUT, 'exportShaderParams': False, 'defaultExportPreset': 'JellyGummy',
       'exportPresets': [preset],
       'exportList': [{'rootPath': sp.textureset.all_texture_sets()[0].name()}],
       'exportParameters': [{'parameters': {'fileFormat': 'png', 'bitDepth': '8', 'dithering': True,
                                            'paddingAlgorithm': 'infinite', 'sizeLog2': 11}}]}
r = sp.export.export_project_textures(cfg)
print(r.status, r.message)
for k, v in r.textures.items():
    print(k, v)
