import unreal as u, os, json
P = json.load(open(os.path.join(u.Paths.project_dir(), 'Saved', 'jelly_shot.json')))
SIDE = float(P.get('side', 1))
acts = u.get_editor_subsystem(u.EditorActorSubsystem)
les = u.get_editor_subsystem(u.LevelEditorSubsystem)
ues = u.get_editor_subsystem(u.UnrealEditorSubsystem)
bears = [a for a in acts.get_all_level_actors() if a.get_actor_label().startswith('Jelly_Bear_' + P.get('one', ''))]
mn = [1e9]*3; mx = [-1e9]*3
for b in bears:
    o, e = b.get_actor_bounds(False)
    for i, k in enumerate('xyz'):
        mn[i] = min(mn[i], getattr(o, k) - getattr(e, k)); mx[i] = max(mx[i], getattr(o, k) + getattr(e, k))
c = u.Vector(*[(a + b) / 2 for a, b in zip(mn, mx)])
dist = max(mx[1] - mn[1], 50) * (0.85 if len(bears) > 1 else 2.2)
cam = u.Vector(c.x + SIDE * dist, c.y, c.z + dist * 0.18)
ues.set_level_viewport_camera_info(cam, u.MathLibrary.find_look_at_rotation(cam, u.Vector(c.x, c.y, c.z - 4)))
# key light from camera side, high and to the left
for a in acts.get_all_level_actors():
    if isinstance(a, u.DirectionalLight):
        a.set_actor_rotation(u.Rotator(pitch=-38, yaw=(180 if SIDE > 0 else 0) + 35, roll=0), False)
try:
    les.editor_set_game_view(True)
except Exception as e:
    print('gameview', e)
u.SystemLibrary.execute_console_command(ues.get_editor_world(), 'HighResShot 1920x1080 filename=' + P.get('name', 'jelly'))
print('shot side', SIDE)
