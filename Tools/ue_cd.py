import unreal as u
w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(w, 'r.CustomDepth 3')
print('custom depth', u.SystemLibrary.get_console_variable_int_value('r.CustomDepth'))
u.EditorAssetLibrary.delete_asset('/Game/JellyGame/Art/Jelly/MI_PP_Test')
