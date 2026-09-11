from flow import *
auth();details=[];changes=[];counts={}
try:
 with db() as c:versions=c.execute('select id,batch_id,snapshot_path,payload_hash,payload from passport_revisions where sealed_at is not null').fetchall()
 for rid,b,p,h,payload in versions:
  raw=(rt/'publish'/p).read_bytes();check('Payload bytes Hash '+p,hashlib.sha256(raw).hexdigest()==h and raw.decode()==payload);check('Public whitelist '+p,all(k not in raw for k in [b'internal_note',b'created_by',b'candidate_hash',b'storage_key',b'/Users/',b'PRIVATE-']))
  response=req('passport-batches/'+b+'/publication/versions/'+rid)
  if response['code']==200:check('Server full JSON asset Manifest integrity '+p,response['data']['integrity']['state']=='verified')
  else:check('Failed prepared diagnostic not publicly listed '+p,response['code']==404 and scalar('select published_at is null from passport_revisions where id=?',(rid,))==1)
  details.append({'id':rid,'path':p,'publicly_published':response['code']==200})
 with db() as c:
  c.row_factory=sqlite3.Row
  assets=c.execute('select * from published_assets').fetchall();check('Nonempty Published Assets exercised',len(assets)>0)
  for a in assets:
   raw=(rt/'publish'/a['published_path']).read_bytes();check('Asset actual bytes '+a['id'],hashlib.sha256(raw).hexdigest()==a['sha256'] and len(raw)==a['file_size'])
  for m in c.execute('select * from media_assets'):
   raw=(rt/'private-media'/m['storage_key']).read_bytes();check('Private working source SHA '+m['id'],hashlib.sha256(raw).hexdigest()==m['sha256'] and len(raw)==m['file_size'])
  check('Final integrity and FK',c.execute('pragma integrity_check').fetchone()[0]=='ok' and not c.execute('pragma foreign_key_check').fetchall());check('No active or recovery remains',c.execute('select count(*) from batches where active_publish_record_id is not null').fetchone()[0]==0)
  check('No test fault trigger left',not c.execute("select name from sqlite_master where type='trigger' and name like 't12%' ").fetchall())
  for table,cols in [('product_revisions','product_id,revision_number'),('batches','batch_code'),('passport_revisions','batch_id,version_number'),('review_records','batch_id,attempt_number')]:
   check('No duplicate '+table,not c.execute('select '+cols+',count(*) from '+table+' group by '+cols+' having count(*)>1').fetchall())
  counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['products','product_revisions','batches','custom_sections','review_records','passport_revisions','publish_records','media_assets','asset_links','published_assets','passport_audit_events']};counts['unlinked_private_media_retained']=c.execute('select count(*) from media_assets m where not exists(select 1 from asset_links a where a.media_asset_id=m.id)').fetchone()[0]
 protected=json.loads((R/'runtime/t12/test-artifacts/protected-before.json').read_text());bad=[p for p,h in protected.items() if not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];check('All 31854 historical protected files unchanged',not bad)
 baseline=json.loads((R/'runtime/t12/test-artifacts/baseline-before.json').read_text());check('53 baseline hashes unchanged',len(baseline)==53 and all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in baseline.items()));check('Original site seven files unchanged',sum(p.startswith('site/') for p in baseline)==7)
 source=json.loads((rt/'test-artifacts/source-before.json').read_text());changes=[p for p,h in source.items() if not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];old_reports=['docs/T12_END_TO_END_ACCEPTANCE.md','docs/T12_TEST_RESULTS.json'];check('Original T12 failed reports unchanged',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==source[p] for p in old_reports))
finally:(rt/'test-artifacts/final-verify.json').write_text(json.dumps({'checks':checks,'versions':details,'counts':counts,'changed_existing_files':changes},ensure_ascii=False,indent=2))
