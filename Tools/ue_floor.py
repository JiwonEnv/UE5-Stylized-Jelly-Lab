import unreal as u
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
for a in acts.get_all_level_actors():
    if 'Ground' in a.get_actor_label():
        print(repr(a.get_actor_label()), a.is_hidden_ed(), a.is_temporarily_hidden_in_editor() if hasattr(a,'is_temporarily_hidden_in_editor') else '', a.get_editor_property('hidden') if True else '')
        a.set_is_temporarily_hidden_in_editor(False)
        a.set_editor_property('hidden', False)
        try: a.set_editor_property('is_editor_only_actor', False)
        except Exception: pass
        try: a.set_editor_property('b_hidden_ed', False)
        except Exception as e: print('bhe', e)
        a.static_mesh_component.set_material(0, u.load_asset('/Game/JellyGame/Art/Jelly/M_LookDev_Floor'))
        print('after', a.is_hidden_ed(), [m.get_name() for m in a.static_mesh_component.get_materials()])
u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
