import unreal as u, json, os
P = json.load(open(os.path.join(u.Paths.project_dir(), 'Saved', 'jelly_pp.json')))
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() == 'Jelly_PaintFilter_PPV':
        a.set_editor_property('blend_weight', float(P['w']))
        print('ppv weight', a.get_editor_property('blend_weight'))
