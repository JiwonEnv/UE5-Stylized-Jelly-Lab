import unreal as u
try:
    print('remaining jobs', u.ShaderCompilingManager if hasattr(u,'ShaderCompilingManager') else 'n/a')
except Exception as e: print(e)
w = u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
u.SystemLibrary.execute_console_command(w, 'r.ShaderCompiler.FinishCompilation')  # may be unknown; harmless
