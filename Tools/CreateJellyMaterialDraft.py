import unreal as u

path='/Game/JellyGame/Experiments/PainterPipeline'
name='M_Jelly_Subsurface_Draft'
asset=u.load_asset(path+'/'+name)
if not asset:
    asset=u.AssetToolsHelpers.get_asset_tools().create_asset(name,path,u.Material,u.MaterialFactoryNew())
lib=u.MaterialEditingLibrary
lib.delete_all_material_expressions(asset)
asset.set_editor_property('shading_model',u.MaterialShadingModel.MSM_SUBSURFACE)
def color(label, rgba, y, prop):
    n=lib.create_material_expression(asset,u.MaterialExpressionVectorParameter,-400,y)
    n.set_editor_property('parameter_name',label)
    n.set_editor_property('default_value',u.LinearColor(*rgba))
    assert lib.connect_material_property(n,'',prop)
def scalar(label, value, y, prop):
    n=lib.create_material_expression(asset,u.MaterialExpressionScalarParameter,-400,y)
    n.set_editor_property('parameter_name',label)
    n.set_editor_property('default_value',value)
    assert lib.connect_material_property(n,'',prop)
color('Jelly Color',(0.89,0.26,0.39,1),-300,u.MaterialProperty.MP_BASE_COLOR)
color('Subsurface Tint',(1.0,0.12,0.22,1),0,u.MaterialProperty.MP_SUBSURFACE_COLOR)
scalar('Roughness',0.22,200,u.MaterialProperty.MP_ROUGHNESS)
scalar('Specular',0.5,350,u.MaterialProperty.MP_SPECULAR)
scalar('Subsurface Density',0.2,500,u.MaterialProperty.MP_OPACITY)
lib.recompile_material(asset)
u.EditorAssetLibrary.save_loaded_asset(asset)
actors=u.get_editor_subsystem(u.EditorActorSubsystem)
levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
test_level='/Game/JellyGame/Maps/L_JellyMaterialPreview'
if not u.EditorAssetLibrary.does_asset_exist(test_level):
    assert u.EditorAssetLibrary.duplicate_asset('/Game/JellyGame/Maps/L_PainterMaterialTest',test_level)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
if not world or world.get_name()!='L_JellyMaterialPreview':
    assert levels.load_level(test_level)
for actor in actors.get_all_level_actors():
    if actor.get_actor_label()=='Painter Baked Mesh - ORM Material':
        actor.static_mesh_component.set_material(0,asset)
        print('JELLY_TEST_MATERIAL_APPLIED')
print('JELLY_MATERIAL_CREATED: '+asset.get_path_name())

from pathlib import Path
root=Path(u.Paths.project_dir()).resolve()/'SourceAssets'/'MaterialPrototypes'
tools=u.AssetToolsHelpers.get_asset_tools()
for index, kind in enumerate(('Cookie','Tissue','Dust'),1):
    material_name='M_'+kind+'_Prototype'
    material=u.load_asset(path+'/'+material_name) or tools.create_asset(material_name,path,u.Material,u.MaterialFactoryNew())
    lib.delete_all_material_expressions(material)
    for row,(suffix,compression,sampler,outputs) in enumerate((
        ('BaseColor',None,u.MaterialSamplerType.SAMPLERTYPE_COLOR,[('',u.MaterialProperty.MP_BASE_COLOR)]),
        ('Normal_DirectX',u.TextureCompressionSettings.TC_NORMALMAP,u.MaterialSamplerType.SAMPLERTYPE_NORMAL,[('',u.MaterialProperty.MP_NORMAL)]),
        ('ORM',u.TextureCompressionSettings.TC_MASKS,u.MaterialSamplerType.SAMPLERTYPE_MASKS,[('R',u.MaterialProperty.MP_AMBIENT_OCCLUSION),('G',u.MaterialProperty.MP_ROUGHNESS),('B',u.MaterialProperty.MP_METALLIC)]),
        ('Mask',u.TextureCompressionSettings.TC_MASKS,u.MaterialSamplerType.SAMPLERTYPE_MASKS,[]),
    )):
        texture_name='T_'+kind+'_'+suffix
        texture=u.load_asset(path+'/'+texture_name)
        if not texture:
            task=u.AssetImportTask()
            task.filename=str(root/kind/(kind+'_'+suffix+'.png'))
            task.destination_path=path
            task.destination_name=texture_name
            task.automated=True
            tools.import_asset_tasks([task])
            texture=next(iter(task.get_objects()),None)
            if texture and texture.get_name()!=texture_name:
                assert u.EditorAssetLibrary.rename_asset(texture.get_path_name(),path+'/'+texture_name)
        assert texture, texture_name
        if compression is not None:
            texture.set_editor_property('compression_settings',compression)
            texture.set_editor_property('srgb',False)
        u.EditorAssetLibrary.save_loaded_asset(texture)
        node=lib.create_material_expression(material,u.MaterialExpressionTextureSampleParameter2D,-480,row*245)
        node.set_editor_property('texture',texture)
        node.set_editor_property('sampler_type',sampler)
        node.set_editor_property('parameter_name',suffix)
        for channel,prop in outputs:
            assert lib.connect_material_property(node,channel,prop)
        if suffix=='Mask':
            lerp=lib.create_material_expression(material,u.MaterialExpressionLinearInterpolate,-180,row*245)
            lerp.set_editor_property('const_a',0.22)
            lerp.set_editor_property('const_b',0.48)
            assert lib.connect_material_expressions(node,'R',lerp,'Alpha')
            assert lib.connect_material_property(lerp,'',u.MaterialProperty.MP_SPECULAR)
    lib.recompile_material(material)
    assert u.EditorAssetLibrary.save_loaded_asset(material)
    if any(a.get_actor_label()=='Painter Baked Mesh - ORM Material' for a in actors.get_all_level_actors()):
        label=kind+' Material Prototype'
        preview=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
        if not preview:
            preview=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,230*index,120))
            preview.set_actor_label(label)
        preview.static_mesh_component.set_static_mesh(u.load_asset(path+'/SM_PainterTest'))
        preview.static_mesh_component.set_material(0,material)
if any(a.get_actor_label()=='Painter Baked Mesh - ORM Material' for a in actors.get_all_level_actors()):
    assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
print('JELLYGAME_MATERIAL_PREVIEWS_READY')
