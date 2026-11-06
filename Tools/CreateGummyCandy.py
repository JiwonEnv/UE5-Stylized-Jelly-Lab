"""Build the reference-driven gummy material and comparison level in Unreal."""
import unreal as u

folder = '/Game/JellyGame/Experiments/PainterPipeline'
name = 'M_GummyCandy_Gel'
assets = u.EditorAssetLibrary
tools = u.AssetToolsHelpers.get_asset_tools()
lib = u.MaterialEditingLibrary
material = u.load_asset(f'{folder}/{name}') or tools.create_asset(name, folder, u.Material, u.MaterialFactoryNew())
lib.delete_all_material_expressions(material)
material.set_editor_property('blend_mode', u.BlendMode.BLEND_TRANSLUCENT)
material.set_editor_property('shading_model', u.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
material.set_editor_property('translucency_lighting_mode', u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
material.set_editor_property('refraction_method', u.RefractionMode.RM_INDEX_OF_REFRACTION)

def parameter(label, value, x, y):
    cls = u.MaterialExpressionVectorParameter if isinstance(value, u.LinearColor) else u.MaterialExpressionScalarParameter
    node = lib.create_material_expression(material, cls, x, y)
    node.set_editor_property('parameter_name', label)
    node.set_editor_property('default_value', value)
    return node

def link(node, prop):
    assert lib.connect_material_property(node, '', prop), str(prop)

P = u.MaterialProperty
tint_node = parameter('Candy Tint', u.LinearColor(.85,.025,.065,1), -800, -420)
link(tint_node, P.MP_BASE_COLOR)
link(parameter('Wet Surface Roughness', .095, -500, 220), P.MP_ROUGHNESS)
link(parameter('Specular', .43, -500, 340), P.MP_SPECULAR)
link(parameter('IOR', 1.37, -500, 460), P.MP_REFRACTION)
fresnel = lib.create_material_expression(material, u.MaterialExpressionFresnel, -530, -20)
fresnel.set_editor_property('exponent', 2.4)
fresnel.set_editor_property('base_reflect_fraction', 0.0)
density = lib.create_material_expression(material, u.MaterialExpressionLinearInterpolate, -160, -130)
assert lib.connect_material_expressions(parameter('Core Density', .48, -800, -230), '', density, 'A')
assert lib.connect_material_expressions(parameter('Edge Density', .14, -800, -110), '', density, 'B')
assert lib.connect_material_expressions(fresnel, '', density, 'Alpha')
link(density, P.MP_OPACITY)
transmission = lib.create_material_expression(material, u.MaterialExpressionLinearInterpolate, -230, -530)
transmission.set_editor_property('const_b', .82)
assert lib.connect_material_expressions(tint_node, '', transmission, 'A')
assert lib.connect_material_expressions(fresnel, '', transmission, 'Alpha')
thin = lib.create_material_expression(material, u.MaterialExpressionThinTranslucentMaterialOutput, 80, -530)
assert lib.connect_material_expressions(transmission, '', thin, '')
lib.recompile_material(material)
assert assets.save_loaded_asset(material)

variants = []
for flavor, tint in (
    ('Coral', (.88,.045,.065)), ('Raspberry', (.72,.006,.14)), ('Amber', (.94,.31,.012)),
):
    instance_name = f'MI_Gel_{flavor}'
    instance = u.load_asset(f'{folder}/{instance_name}') or tools.create_asset(
        instance_name, folder, u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew()
    )
    lib.set_material_instance_parent(instance, material)
    if lib.set_material_instance_vector_parameter_value(instance, 'Candy Tint', u.LinearColor(*tint,1)):
        lib.update_material_instance(instance)
        assert assets.save_loaded_asset(instance)
    else:
        variant_name = f'M_Gel_{flavor}'
        instance = u.load_asset(f'{folder}/{variant_name}') or assets.duplicate_asset(
            f'{folder}/{name}', f'{folder}/{variant_name}'
        )
        variant_tint = lib.get_material_property_input_node(instance, P.MP_BASE_COLOR)
        assert variant_tint
        variant_tint.set_editor_property('default_value', u.LinearColor(*tint,1))
        lib.recompile_material(instance)
        assert assets.save_loaded_asset(instance)
    variants.append((flavor, instance))

levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
scene = '/Game/JellyGame/Maps/L_GummyGelLookDev'
if not assets.does_asset_exist(scene):
    assert assets.duplicate_asset('/Game/JellyGame/Maps/L_PainterMaterialTest', scene)
assert levels.load_level(scene)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
current = {a.get_actor_label(): a for a in actors.get_all_level_actors()}
mesh = u.load_asset(f'{folder}/SM_PainterTest')
for index, (flavor, instance) in enumerate(variants):
    label = f'Gummy {flavor}'
    actor = current.get(label)
    if not actor and index == 1:
        actor = current.get('Painter Baked Mesh - ORM Material')
    position = u.Vector(0, (index-1)*230, 120)
    if not actor:
        actor = actors.spawn_actor_from_class(u.StaticMeshActor, position)
    actor.set_actor_label(label)
    actor.set_actor_location(position, False, False)
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.static_mesh_component.set_material(0, instance)
    assert actor.static_mesh_component.get_material(0) == instance
camera = current.get('Painter Material Test Camera')
if camera:
    camera.set_actor_location(u.Vector(-1050,0,325), False, False)
    camera.set_actor_rotation(u.Rotator(0,-11,0), False)
assert levels.save_current_level()
u.log('GUMMY_CANDY_SAVED: 3 materials assigned and comparison level saved')
