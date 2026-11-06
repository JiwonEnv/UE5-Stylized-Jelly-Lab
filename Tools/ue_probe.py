import unreal
print(unreal.SystemLibrary.get_engine_version(), unreal.Paths.project_dir())
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
print('world', w.get_name())
