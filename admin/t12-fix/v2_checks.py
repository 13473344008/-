from flow import *
auth();f=json.loads(statefile.read_text());bp='passport-batches/'+f['batch_id']
try:
 v=ok(bp+'/publication')['current'];check('Real UI V2 published',v['version_number']==2);f['versions']=[f['versions'][0],v['id']];save(f)
 old=json.loads((rt/'test-artifacts/v1-files.json').read_text());check('V1 immutable JSON and assets unchanged',all(hashlib.sha256((rt/'publish'/p).read_bytes()).hexdigest()==sha for p,sha in old.items() if not p.startswith('published/')))
 p=json.loads((rt/'publish/published/PF-T12-TEST-001.json').read_text());check('V2 actual images remain two',len(p['assets'])==2);check('V2 package22',p['packaging']['quantity']=='22');d=ok(bp+'/publication/compare?left='+f['versions'][0]+'&right='+v['id']);(rt/'test-artifacts/version-compare.json').write_text(json.dumps(d,indent=2));check('Compare actual asset differences',any(x['group']=='assets' for x in d['differences']));print([(x['group'],x['path']) for x in d['differences']])
 reviews=ok(bp+'/review')['history'];check('Rejected review preserved exact reason',sum(x.get('rejection_reason')=='T12 TEST — please adjust packaging statement.' for x in reviews)==2);check('Four separate candidate attempts retained',len(reviews)==4)
 (rt/'test-artifacts/v2-files.json').write_text(json.dumps({str(p.relative_to(rt/'publish')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (rt/'publish').rglob('*') if p.is_file()},indent=2))
finally:(rt/'test-artifacts/v2-checks.json').write_text(json.dumps(checks,indent=2))
