"""Run a Python file inside the open UE editor via Python Remote Execution.
    python ue_run.py script.py [timeout]"""
import sys, time
RE = r'C:\Program Files\Epic Games\UE_5.8\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python'
sys.path.insert(0, RE)
import remote_execution as rex
path = sys.argv[1]
timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 600
r = rex.RemoteExecution(); r.start()
t0 = time.time()
while not r.remote_nodes and time.time() - t0 < 8:
    time.sleep(0.25)
nodes = r.remote_nodes
if not nodes:
    print('NO UE NODES'); r.stop(); sys.exit(2)
proj = [n for n in nodes if 'Jelly' in (n.get('project_name', '') + n.get('project_root', ''))] or nodes
r.open_command_connection(proj[0]['node_id'])
import os; code = os.path.abspath(path).replace(chr(92), "/")
res = r.run_command(code, unattended=True, exec_mode=rex.MODE_EXEC_FILE)
for o in res.get('output', []):
    print(o.get('output', '').rstrip())
print('SUCCESS' if res.get('success') else 'FAILED', res.get('result', '')[:3000])
r.stop()
