from pathlib import Path
import tempfile,shutil,subprocess,os,re,json
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t12-fix';checks=[]
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
ui=r/'admin/go-admin-ui';go=r/'admin/go-admin'
with tempfile.TemporaryDirectory(prefix='t12-contract-') as temp:
 t=Path(temp)
 for p in ['src/views','src/types','tests/e2e/mocked','scripts']:
  shutil.copytree(ui/p,t/p)
 def run():return subprocess.run(['node',str(t/'scripts/check-api-contract.mjs')],env={**os.environ,'GO_ADMIN_PATH':str(go)},capture_output=True,text=True)
 check('Generic contract full original suite now passes',run().returncode==0)
 page=t/'src/views/passport/products/index.vue';old=page.read_text();page.write_text(old+'\n<el-table-column prop="t12_nonexistent_field" />\n');res=run();check('Unknown Passport response field still fails',res.returncode!=0 and 't12_nonexistent_field' in res.stderr);page.write_text(old+'\n<!-- table.query.t12_nonexistent_query -->\n');res=run();check('Unknown Passport query still fails',res.returncode!=0 and 't12_nonexistent_query' in res.stderr)
server=(go/'app/passport/service/media.go').read_text();client=(ui/'src/api/passport/media.ts').read_text();block=server.split('type MediaItem struct {')[1].split('\n}')[0];allowed=set(re.findall(r'json:"([^"]+)"',block))-{'-'};ts=client.split('export interface MediaItem {')[1].split('}')[0];declared=set(re.findall(r'(\w+):',ts));check('MediaItem client exact server response fields',declared==allowed)
forms=set(re.findall(r"data.append\('([^']+)'",client));check('Upload client uses all and only explicit multipart parameters',forms=={'file','expected_token','public_label','is_public'})
api=(go/'app/passport/apis/media.go').read_text();check('Media handlers multipart bound and body capped','http.MaxBytesReader' in api and 'ParseMultipartForm' in api and 'io.LimitReader' in api)
router=(go/'app/admin/router/passport_media.go').read_text();check('New scoped media routes JWT live identity Casbin and data scope',all(x in router for x in ['MiddlewareFunc','LiveIdentity','AuthCheckRole','PermissionAction','a.List','a.Upload','a.Detach']))
check('Upload uses FormData without manual Content-Type','new FormData()' in client and 'Content-Type' not in client)
(rt/'test-artifacts/contracts.json').write_text(json.dumps({'checks':checks,'prior_diagnostics':'4 preexisting generic mapping diagnostics retained in original T12 log; fixed explicit Passport bindings, not removed from check or allowed fields.'},indent=2))
