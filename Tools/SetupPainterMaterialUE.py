"""Run inside UE5 Editor: import Painter test output, connect ORM material, save level."""
import json
from pathlib import Path
import unreal as ue

ROOT=Path(ue.Paths.project_dir()).resolve()
SOURCE=ROOT/'SourceAssets'/'PainterMCPTest'
DEST='/Game/JellyGame/Experiments/PainterPipeline'
REPORT=ROOT/'Docs'/'SubstancePainterMCP'/'ue5-validation.json'
tools=ue.AssetToolsHelpers.get_asset_tools()
lib=ue.MaterialEditingLibrary
report={'engine':ue.SystemLibrary.get_engine_version(),'project_name':'Jelly Game','imports':{},'connections':{}}

def import_asset(source,name,options=None):
    existing=ue.load_asset(DEST+'/'+name)
    if existing:return existing
    task=ue.AssetImportTask()
    task.set_editor_property('filename',str(source))
    task.set_editor_property('destination_path',DEST)
    task.set_editor_property('destination_name',name)
    task.set_editor_property('automated',True)
    task.set_editor_property('save',True)
    task.set_editor_property('replace_existing',False)
    if options:
        task.set_editor_property('options',options)
        task.set_editor_property('factory',ue.FbxFactory())
    tools.import_asset_tasks([task])
    paths=list(task.get_editor_property('imported_object_paths'))
    if not paths:raise RuntimeError('Import failed: '+str(source))
    asset=ue.load_asset(paths[0])
    report['imports'][name]=asset.get_path_name()
    return asset

textures={}
for suffix,exported in [('BC','BaseColor'),('N','Normal'),('ORM','OcclusionRoughnessMetallic')]:
    t=import_asset(SOURCE/'Textures'/'UE5'/('test_low_MCPTest_'+exported+'.png'),'T_PainterTest_'+suffix)
    t.set_editor_property('srgb',suffix=='BC')
    if suffix=='N':
        t.set_editor_property('compression_settings',ue.TextureCompressionSettings.TC_NORMALMAP)
        t.set_editor_property('flip_green_channel',False)
    elif suffix=='ORM':t.set_editor_property('compression_settings',ue.TextureCompressionSettings.TC_MASKS)
    ue.EditorAssetLibrary.save_loaded_asset(t)
    textures[suffix]=t

options=ue.FbxImportUI()
options.set_editor_property('import_mesh',True)
options.set_editor_property('import_as_skeletal',False)
options.set_editor_property('mesh_type_to_import',ue.FBXImportType.FBXIT_STATIC_MESH)
options.set_editor_property('import_materials',False)
options.set_editor_property('import_textures',False)
options.static_mesh_import_data.set_editor_property('import_uniform_scale',100.0)
options.static_mesh_import_data.set_editor_property('combine_meshes',True)
options.static_mesh_import_data.set_editor_property('generate_lightmap_u_vs',False)
mesh=import_asset(SOURCE/'test_low.obj','SM_PainterTest',options)

material=ue.load_asset(DEST+'/M_PainterTest')
if material is None:material=tools.create_asset('M_PainterTest',DEST,ue.Material,ue.MaterialFactoryNew())
lib.delete_all_material_expressions(material)
samples={}
for suffix,y in [('BC',-300),('N',0),('ORM',300)]:
    node=lib.create_material_expression(material,ue.MaterialExpressionTextureSample,-500,y)
    node.set_editor_property('texture',textures[suffix])
    node.set_editor_property('sampler_type',{'BC':ue.MaterialSamplerType.SAMPLERTYPE_COLOR,'N':ue.MaterialSamplerType.SAMPLERTYPE_NORMAL,'ORM':ue.MaterialSamplerType.SAMPLERTYPE_MASKS}[suffix])
    node.set_editor_property('desc',{'BC':'Base Color (sRGB)','N':'DirectX Normal','ORM':'R: AO | G: Roughness | B: Metallic'}[suffix])
    samples[suffix]=node
for suffix,channel,prop in [('BC','RGB',ue.MaterialProperty.MP_BASE_COLOR),('N','RGB',ue.MaterialProperty.MP_NORMAL),('ORM','R',ue.MaterialProperty.MP_AMBIENT_OCCLUSION),('ORM','G',ue.MaterialProperty.MP_ROUGHNESS),('ORM','B',ue.MaterialProperty.MP_METALLIC)]:
    ok=lib.connect_material_property(samples[suffix],channel,prop)
    report['connections'][str(prop)]=ok
    if not ok:raise RuntimeError('Material connection failed: '+str(prop))
lib.recompile_material(material)
mesh.set_material(0,material)
ue.EditorAssetLibrary.save_loaded_asset(material)
ue.EditorAssetLibrary.save_loaded_asset(mesh)

level=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
level_path='/Game/JellyGame/Maps/L_PainterMaterialTest'
if ue.EditorAssetLibrary.does_asset_exist(level_path):level.load_level(level_path)
else:
    if not level.new_level(level_path):raise RuntimeError('Level creation failed')
    sphere=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(0,0,120))
    sphere.set_actor_label('Painter Baked Mesh - ORM Material')
    sphere.static_mesh_component.set_static_mesh(mesh)
    sphere.static_mesh_component.set_material(0,material)
    floor=actors.spawn_actor_from_class(ue.StaticMeshActor,ue.Vector(0,0,-10))
    floor.set_actor_label('Test Ground')
    floor.static_mesh_component.set_static_mesh(ue.load_asset('/Engine/BasicShapes/Cube.Cube'))
    floor.set_actor_scale3d(ue.Vector(12,12,0.2))
    light=actors.spawn_actor_from_class(ue.DirectionalLight,ue.Vector(0,0,450),ue.Rotator(-40,-35,0))
    light.set_actor_label('Key Light')
    light.light_component.set_editor_property('intensity',5.0)
    fill=actors.spawn_actor_from_class(ue.PointLight,ue.Vector(-180,180,250))
    fill.light_component.set_editor_property('intensity',1000.0)
    fill.light_component.set_editor_property('attenuation_radius',1200.0)
    sky=actors.spawn_actor_from_class(ue.SkyAtmosphere,ue.Vector())
    light.light_component.set_editor_property('atmosphere_sun_light',True)
    skylight=actors.spawn_actor_from_class(ue.SkyLight,ue.Vector(0,0,400))
    skylight.light_component.set_editor_property('real_time_capture',True)
    actors.spawn_actor_from_class(ue.PlayerStart,ue.Vector(-400,0,150),ue.Rotator(0,0,0))
    camera=actors.spawn_actor_from_class(ue.CameraActor,ue.Vector(-420,-420,260),ue.Rotator(-13,45,0))
    camera.set_actor_label('Painter Material Test Camera')
    camera.camera_component.set_editor_property('field_of_view',42.0)
    ue.EditorLevelLibrary.set_level_viewport_camera_info(ue.Vector(-420,-420,260),ue.Rotator(-13,45,0))
if not level.save_current_level():raise RuntimeError('Level save failed')
ue.EditorAssetLibrary.save_directory('/Game/JellyGame',only_if_is_dirty=False,recursive=True)
report['textures']={k:{'path':v.get_path_name(),'srgb':v.get_editor_property('srgb'),'compression':str(v.get_editor_property('compression_settings'))} for k,v in textures.items()}
report['material']=material.get_path_name()
report['mesh']=mesh.get_path_name()
report['mesh_material']=mesh.get_material(0).get_path_name()
report['used_textures']=[t.get_path_name() for t in lib.get_material_used_textures(material)]
report['level']=level_path
report['success']=all(report['connections'].values()) and len(report['used_textures'])==3 and report['mesh_material']==material.get_path_name()
REPORT.parent.mkdir(parents=True,exist_ok=True)
REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
ue.log('JELLY_PAINTER_TEST_SUCCESS '+str(report['success']))
