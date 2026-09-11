from pathlib import Path
import subprocess,json,sqlite3,hashlib,datetime
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t12-fix'
def cmd(args):return subprocess.check_output(args,cwd=r,stderr=subprocess.STDOUT,text=True).strip()
env={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'go':cmd([str(r/'runtime/t4/tools/go/bin/go'),'version']),'node':cmd(['node','--version']),'pnpm':cmd([str(r/'runtime/t4/tools/pnpm/node_modules/.bin/pnpm'),'--version']),'git':cmd(['git','--version']),'sqlite_cli':cmd(['sqlite3','--version']),'python_sqlite':sqlite3.sqlite_version,'go_sqlite':json.loads((rt/'logs/bootstrap.log').read_text().splitlines()[-1]),'backend_commit':cmd(['git','-C','admin/go-admin','rev-parse','HEAD']),'ui_commit':cmd(['git','-C','admin/go-admin-ui','rev-parse','HEAD'])}
(rt/'test-artifacts/environment.json').write_text(json.dumps(env,indent=2));print(json.dumps(env,indent=2))
