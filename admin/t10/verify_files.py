from pathlib import Path
import sqlite3,json,hashlib,re,subprocess
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t10';checks=[];counts={}
def check(n,v):checks.append({'name':n,'status':'PASS' if v else 'FAIL'});assert v,n
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):
 # Matches Go's fixed escaping for U+2028/U+2029, with UTF-8 key ordering and exact integers.
 return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).replace('\u2028','\\u2028').replace('\u2029','\\u2029').encode()
for root,dbfile in [(rt,'passport-admin-t10.db'),(rt/'fresh','fresh-acceptance.db')]:
 c=sqlite3.connect(root/'db'/dbfile);c.row_factory=sqlite3.Row
 check(root.name+' integrity',c.execute('pragma integrity_check').fetchone()[0]=='ok');check(root.name+' foreign keys',c.execute('pragma foreign_key_check').fetchall()==[])
 check(root.name+' one successful revision per review',c.execute('select count(*) from (select source_review_record_id from passport_revisions where published_at is not null AND rollback_source_revision_id IS NULL group by source_review_record_id having count(*)>1)').fetchone()[0]==0)
 check(root.name+' unique batch version',c.execute('select count(*) from (select batch_id,version_number from passport_revisions group by batch_id,version_number having count(*)>1)').fetchone()[0]==0)
 check(root.name+' no unresolved operations',c.execute("select count(*) from publish_records where publish_status not in ('published','failed')").fetchone()[0]==0)
 check(root.name+' no injected DB triggers',c.execute("select count(*) from sqlite_master where type='trigger' and name like 't10_fault%'").fetchone()[0]==0)
 for name,sql in {
  'orphan revisions':"select count(*) from passport_revisions p left join batches b on b.id=p.batch_id where b.id is null",
  'orphan assets':"select count(*) from published_assets a left join passport_revisions p on p.id=a.passport_revision_id where p.id is null",
  'orphan records':"select count(*) from publish_records r left join passport_revisions p on p.id=r.passport_revision_id where p.id is null",
  'orphan reviews':"select count(*) from review_records r left join batches b on b.id=r.batch_id where b.id is null",
  'invalid rollback source':"select count(*) from passport_revisions p left join passport_revisions s on s.id=p.rollback_source_revision_id where p.rollback_source_revision_id is not null and (s.id is null or s.batch_id!=p.batch_id or s.published_at is null or s.version_number>=p.version_number)",
  'unsuccessful current':"select count(*) from batches b join passport_revisions p on p.id=b.current_passport_revision_id join publish_records r on r.passport_revision_id=p.id where p.published_at is null or r.publish_status!='published'",
  'duplicate successful transition':"select count(*) from (select batch_id,expected_current_revision_id from publish_records where publish_status='published' group by batch_id,expected_current_revision_id having count(*)>1)"
 }.items():check(root.name+' '+name,c.execute(sql).fetchone()[0]==0)
 revisions=c.execute('select * from passport_revisions where sealed_at is not null').fetchall();published=0;assetcount=0
 for p in revisions:
  raw=(root/'publish'/p['snapshot_path']).read_bytes();data=json.loads(raw);check('payload '+p['id'],sha(root/'publish'/p['snapshot_path'])==p['payload_hash'] and raw.decode()==p['payload'] and canonical(data)==raw)
  business=dict(data);business.pop('publication');check('content hash '+p['id'],hashlib.sha256(canonical(business)).hexdigest()==p['content_hash'])
  manifest=json.loads((root/'releases/manifests'/f'{p["release_identifier"]}.json').read_text());rec=c.execute('select * from publish_records where passport_revision_id=?',(p['id'],)).fetchone();assets=c.execute('select * from published_assets where passport_revision_id=? order by asset_key',(p['id'],)).fetchall();assetcount+=len(assets)
  assetdefs=[dict(key=a['asset_key'],role=a['asset_role'],label=a['public_label'],path=a['published_path'],mime_type=a['mime_type'],file_size=a['file_size'],sha256=a['sha256']) for a in assets]
  check('asset manifest '+p['id'],data['assets']==assetdefs and hashlib.sha256(canonical(assetdefs)).hexdigest()==p['asset_manifest_hash'] and rec['asset_count']==len(assets))
  # Manifest 1.0 encodes version in the immutable snapshot path; later builds also include explicit version_number.
  version=int(re.search(r'/v([0-9]+)\.json$',manifest['snapshot_path'])[1]);check('release manifest '+p['id'],version==p['version_number'] and manifest.get('version_number',version)==version and manifest['passport_revision_id']==p['id'] and manifest['publish_record_id']==rec['id'] and manifest['review_id']==p['source_review_record_id'] and manifest['payload_hash']==p['payload_hash'] and manifest['content_hash']==p['content_hash'] and manifest['asset_manifest_hash']==p['asset_manifest_hash'] and manifest['asset_count']==len(assets))
  tmp=root/'releases/tmp'/rec['id'];check('temporary release '+p['id'],(tmp/'passport.json').read_bytes()==raw and (tmp/'assets.json').read_bytes()==canonical(assetdefs))
  for a in assets:
   file=root/'publish'/a['published_path'];check('asset bytes '+a['id'],file.is_file() and not file.is_symlink() and sha(file)==a['sha256'] and file.stat().st_size==a['file_size'])
  if p['published_at'] is not None:
   published+=1;check('success record '+p['id'],rec['publish_status']=='published' and rec['completed_at'] is not None and rec['switched_at'] is not None)
   check('success audit '+p['id'],c.execute("select count(*) from passport_audit_events where event_type IN ('publish_succeeded','rollback_succeeded') and json_extract(after_data,'$.publish_record_id')=?",(rec['id'],)).fetchone()[0]==1)
 for b in c.execute('select b.batch_code,b.workflow_status,b.active_publish_record_id,p.snapshot_path,p.payload_hash from batches b join passport_revisions p on b.current_passport_revision_id=p.id'):
  check('head '+b['batch_code'],sha(root/'publish/published'/f'{b["batch_code"]}.json')==b['payload_hash'] and b['workflow_status'] in ['published','archived'] and b['active_publish_record_id'] is None)
 check(root.name+' public tree has only generated public artifacts',all(not p.is_symlink() and p.suffix in ['.json','.png'] and any(str(p.relative_to(root/'publish')).startswith(k) for k in ['versions/','published/','assets/sha256/']) for p in (root/'publish').rglob('*') if p.is_file()))
 counts[root.name]={'published_revisions':published,'sealed_revisions':len(revisions),'published_asset_rows':assetcount,'records':c.execute('select count(*) from publish_records').fetchone()[0],'failed_records':c.execute("select count(*) from publish_records where publish_status='failed'").fetchone()[0],'tables':21,'business_columns':sum(len(c.execute('pragma table_info('+t+')').fetchall()) for t in list(json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables'])+['review_records','publication_health']),'triggers':c.execute("select count(*) from sqlite_master where type='trigger'").fetchone()[0]};c.close()
b=json.loads((R/'docs/BASELINE_SHA256.json').read_text())['files'];check('53 baseline unchanged',len(b)==53 and all(sha(R/p)==h for p,h in b.items()));check('7 site files unchanged',sum(p.startswith('site/') for p in b)==7 and all(sha(R/p)==h for p,h in b.items() if p.startswith('site/')))
old=json.loads((rt/'test-artifacts/protected-before.json').read_text());changed=[p for p,h in old.items() if not (R/p).exists() or sha(R/p)!=h];check('T4-T9 historical files and migrations unchanged',not changed)
check('Backend upstream tracked unchanged',subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin',text=True)=='')
check('Only existing two UI locale tracked files modified',sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=R/'admin/go-admin-ui',text=True).splitlines())==['src/lang/en-US/index.ts','src/lang/zh-CN/index.ts'])
for repo in ['go-admin','go-admin-ui']:check(repo+' diff check',subprocess.run(['git','diff','--check'],cwd=R/'admin'/repo,capture_output=True).returncode==0)
(rt/'test-artifacts/files.json').write_text(json.dumps({'checks':checks,'counts':counts,'protected_count':len(old)},indent=2));print(len(checks),'PASS',counts)
