from flow import *
auth();details=[];before={};changed=[];changes=[]
try:
 with db() as c:versions=c.execute('select id,batch_id,snapshot_path,payload_hash,payload from passport_revisions where sealed_at is not null').fetchall()
 for rid,b,p,h,payload in versions:
  raw=(rt/'publish'/p).read_bytes();check('Payload bytes Hash '+p,hashlib.sha256(raw).hexdigest()==h and raw.decode()==payload)
  check('No private fields '+p,all(k not in raw for k in [b'internal_note',b'created_by',b'candidate_hash',b'storage_key',b'/Users/',b'PRIVATE-']))
  d=req('passport-batches/'+b+'/publication/versions/'+rid);d=d.get('data') if d['code']==200 else None
  if d is None:
   check('Failed prepared snapshot retained '+p,scalar('select published_at is null from passport_revisions where id=?',(rid,))==1);continue
  check('Full Manifest integrity '+p,d['integrity']['state']=='verified');details.append({'id':rid,'path':p,'integrity':d['integrity'],'assets':len(d['assets'])})
 with db() as c:
  check('Final integrity_check ok',c.execute('pragma integrity_check').fetchall()==[('ok',)])
  check('Final foreign_key_check empty',c.execute('pragma foreign_key_check').fetchall()==[])
  check('No recovery or active operation remains',c.execute('select count(*) from batches where active_publish_record_id is not null').fetchone()[0]==0)
  check('No T12 media fixture was inserted',c.execute('select count(*) from media_assets').fetchone()[0]==0)
 before=json.loads((rt/'test-artifacts/protected-before.json').read_text());changed=[p for p,h in before.items() if not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('T4-T11 protected evidence and migrations unchanged',not changed)
 baseline=json.loads((rt/'test-artifacts/baseline-before.json').read_text());check('53 baseline hashes unchanged',len(baseline)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in baseline.items()));check('POC seven files intact',sum(p.startswith('site/') for p in baseline)==7)
 source=json.loads((rt/'test-artifacts/source-before.json').read_text());changes=[p for p,h in source.items() if not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('Existing business source unchanged',not changes)
finally:(rt/'test-artifacts/final-verify.json').write_text(json.dumps({'checks':checks,'versions':details,'protected_count':len(before),'changed_protected':changed,'changed_business':changes},ensure_ascii=False,indent=2))
