"""T4 database-only fixture verification; no business API or publish engine."""
import sqlite3,json,uuid,datetime,hashlib,concurrent.futures,time,base64,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];RT=R/'runtime/t4';DB=Path(sys.argv[1]) if len(sys.argv)>1 else RT/'db/passport-admin-validated.db'
results=[]
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
id=lambda:str(uuid.uuid4())
def connect():
 c=sqlite3.connect(DB,timeout=5,isolation_level=None);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON');c.execute('PRAGMA busy_timeout=5000');c.execute('PRAGMA journal_mode=WAL');return c
c=connect()
def check(name,condition,detail=None):
 results.append({'name':name,'status':'PASS' if condition else 'FAIL','detail':detail})
 if not condition:raise AssertionError(name)
def reject(name,fn,contains=None):
 try:
  fn()
 except sqlite3.IntegrityError as e:
  check(name,not contains or contains.lower() in str(e).lower(),str(e));return
 check(name,False,'Unexpectedly accepted')
def insert(t,**kw):
 cols=c.execute('PRAGMA table_info("'+t+'")').fetchall()
 v={'id':id(),'created_at':now(),'created_by':1,'updated_at':now(),'updated_by':1}
 v={k:x for k,x in v.items() if k in [f['name'] for f in cols]};v.update(kw)
 sql='INSERT INTO "'+t+'" ('+','.join('"'+k+'"' for k in v)+') VALUES('+','.join('?' for k in v)+')'
 c.execute(sql,list(v.values()));return v['id']
def scalar(sql,*args):return c.execute(sql,args).fetchone()[0]
def product(code):return insert('products',product_code=code)
def revision(p,n=1):return insert('product_revisions',product_id=p,revision_number=n)
def translate(pr,lang='en'):return insert('product_revision_translations',product_revision_id=pr,language_code=lang,translation_status='approved',product_name='T4 TEST Potato Flakes')
def seal(pr):c.execute("UPDATE product_revisions SET revision_status='sealed',sealed_at=?,sealed_by=1,content_hash=? WHERE id=?",(now(),'a'*64,pr))
def batch(code,p,pr):return insert('batches',batch_code=code,product_id=p,base_product_revision_id=pr)
def item(b,code,judgement='not_tested',value=None):return insert('inspection_items',batch_id=b,item_code=code,name='T4 '+code,value_type='decimal',numeric_value=value,judgement=judgement)
def audit(b,typ='batch_created'):return insert('passport_audit_events',batch_id=b,actor_user_id=1,entity_type='batches',entity_id=b,event_type=typ,summary='T4 TEST RECORD — NOT FOR COMMERCIAL USE')
def asset_file(name,bytes):
 path=RT/'assets-private'/name;path.parent.mkdir(exist_ok=True);path.write_bytes(bytes);return path
# Actual tiny valid PNG fixture; these are test files, not COA evidence.
pngA=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXioAAAAASUVORK5CYII=')
pngB=pngA+b'T4-image-B-fixture'
def media(name,data):
 p=asset_file(name,data);return insert('media_assets',storage_key='assets-private/'+name,original_filename=name,mime_type='image/png',file_size=len(data),sha256=hashlib.sha256(data).hexdigest(),is_public_eligible=1)
def passport(b,pr,n,source=None,rollback=None):
 return insert('passport_revisions',batch_id=b,version_number=n,base_product_revision_id=pr,source_revision_id=source,rollback_source_revision_id=rollback,source_edit_version=None if rollback else 1,source_content_hash='b'*64,frozen_input=json.dumps({'test_only':True}),schema_version='1.0',builder_version='t4-schema-fixture',published_by=1,reviewed_by=1,reviewed_at=now(),release_identifier=id())
def publish_fixture(b,prid,mediaid=None):
 rel=scalar('SELECT release_identifier FROM passport_revisions WHERE id=?',prid)
 record=insert('publish_records',batch_id=b,passport_revision_id=prid,release_identifier=rel,idempotency_key='T4-'+id())
 c.execute('UPDATE batches SET active_publish_record_id=? WHERE id=?',(record,b))
 if mediaid:
  h=hashlib.sha256(pngA).hexdigest();relative=f'assets/sha256/{h[:2]}/{h}.png';p=RT/'frozen'/relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(pngA)
  insert('published_assets',passport_revision_id=prid,source_media_asset_id=mediaid,asset_key='product-image',asset_role='product_image',original_filename='image-A.png',public_label='T4 Test image',published_filename=h+'.png',mime_type='image/png',file_size=len(pngA),sha256=h,published_path=relative,source_asset_sha256=h,transform_version='identity-v1')
 payload=json.dumps({'schema_version':'1.0','notice':'TEST RECORD — NOT FOR COMMERCIAL USE','t4_schema_fixture':True},sort_keys=True)
 c.execute('UPDATE passport_revisions SET payload=?,payload_hash=?,content_hash=?,snapshot_path=?,asset_manifest_hash=?,sealed_at=? WHERE id=?',(payload,hashlib.sha256(payload.encode()).hexdigest(),'c'*64,'versions/T4/v'+str(scalar('SELECT version_number FROM passport_revisions WHERE id=?',prid))+'.json','d'*64,now(),prid))
 c.execute("UPDATE publish_records SET publish_status='switching' WHERE id=?",(record,))
 c.execute('UPDATE passport_revisions SET published_at=? WHERE id=?',(now(),prid))
 c.execute("UPDATE publish_records SET publish_status='published',completed_at=?,asset_count=? WHERE id=?",(now(),1 if mediaid else 0,record))
 c.execute("UPDATE batches SET current_passport_revision_id=?,workflow_status='published',active_publish_record_id=NULL WHERE id=?",(prid,b))
 return record
try:
 c.execute('BEGIN IMMEDIATE')
 check('19 business tables exist',all(scalar("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?",t)==1 for t in json.loads((R/'admin/t4/schema_catalog.json').read_text())['tables']))
 check('foreign_keys enabled',scalar('PRAGMA foreign_keys')==1)
 p=product('T4-PF-STD');pr=revision(p);translate(pr)
 reject('Product code UNIQUE',lambda:product('T4-PF-STD'),'UNIQUE')
 reject('Product revision UNIQUE',lambda:revision(p),'UNIQUE')
 for lang in ['zh-CN','es','ar','fr','de']:translate(pr,lang)
 check('six translations coexist',scalar('SELECT count(*) FROM product_revision_translations WHERE product_revision_id=?',pr)==6)
 reject('Translation UNIQUE',lambda:translate(pr),'UNIQUE')
 sec=insert('custom_sections',product_revision_id=pr,section_key='t4_section',sort_order=1,status='ready')
 st=insert('custom_section_translations',custom_section_id=sec,language_code='en',translation_status='approved',title='T4',content='{"text":"TEST"}')
 c.execute('UPDATE product_revisions SET package_quantity=?,package_unit=? WHERE id=?',('25','kg',pr));seal(pr)
 b=batch('PF-T4-001',p,pr)
 reject('Batch code UNIQUE',lambda:batch('PF-T4-001',p,pr),'UNIQUE')
 reject('Batch base NOT NULL',lambda:batch('PF-T4-NULL',p,None))
 p2=product('T4-OTHER');pr2=revision(p2);translate(pr2);seal(pr2)
 reject('Batch cross-product base rejected',lambda:batch('PF-T4-CROSS',p,pr2))
 reject('Referenced template delete rejected',lambda:c.execute('DELETE FROM product_revisions WHERE id=?',(pr,)))
 reject('Referenced product FK delete rejected',lambda:c.execute('DELETE FROM products WHERE id=?',(p,)),'FOREIGN KEY')
 r2=revision(p,2);translate(r2);seal(r2);c.execute('UPDATE products SET current_revision_id=? WHERE id=?',(r2,p))
 check('New R2 does not change Batch R1',scalar('SELECT base_product_revision_id FROM batches WHERE id=?',b)==pr)
 reject('Batch rebind rejected',lambda:c.execute('UPDATE batches SET base_product_revision_id=? WHERE id=?',(r2,b)))
 reject('Frozen template body update',lambda:c.execute("UPDATE product_revisions SET package_quantity='30' WHERE id=?",(pr,)))
 reject('Frozen template translation update',lambda:c.execute("UPDATE product_revision_translations SET product_name='changed' WHERE product_revision_id=?",(pr,)))
 reject('Frozen section update',lambda:c.execute("UPDATE custom_sections SET sort_order=3 WHERE id=?",(sec,)))
 reject('Frozen section translation delete',lambda:c.execute('DELETE FROM custom_section_translations WHERE id=?',(st,)))
 reject('Frozen child insert rejected',lambda:insert('custom_sections',product_revision_id=pr,section_key='late',sort_order=2))
 ba=batch('PF-T4-INHERIT',p,pr);bb=batch('PF-T4-SET',p,pr);bc=batch('PF-T4-CLEAR',p,pr)
 insert('batch_overrides',batch_id=bb,field_key='package_quantity',value_kind='decimal',value_text='20')
 insert('batch_overrides',batch_id=bc,field_key='package_quantity',value_kind='decimal',operation='clear')
 def effective(bid):
  o=c.execute('SELECT operation,value_text FROM batch_overrides WHERE batch_id=? AND field_key=?',(bid,'package_quantity')).fetchone()
  return '25' if o is None else None if o['operation']=='clear' else o['value_text']
 check('Override inherit/set/clear', [effective(x) for x in [ba,bb,bc]]==['25','20',None])
 c.execute('DELETE FROM batch_overrides WHERE batch_id=?',(bb,));check('Cancel override restores inheritance',effective(bb)=='25')
 reject('Override whitelist rejects workflow_status',lambda:insert('batch_overrides',batch_id=bb,field_key='workflow_status',value_kind='text',value_text='published'),'CHECK')
 before=scalar('PRAGMA schema_version')
 for name in ['MOISTURE','REDUCING_SUGAR','VISCOSITY','LEAD','ARSENIC','TPC','BULK_DENSITY']:item(b,name)
 check('Unknown inspection added without ALTER',scalar('PRAGMA schema_version')==before and scalar('SELECT count(*) FROM inspection_items WHERE batch_id=?',b)==7)
 for state in ['pass','fail','not_tested','not_applicable']:item(b,'STATE_'+state.upper(),state,'1.2' if state in ['pass','fail'] else None)
 check('four inspection judgements persisted',scalar('SELECT count(DISTINCT judgement) FROM inspection_items WHERE batch_id=?',b)==4)
 reject('Pass without value rejected',lambda:item(b,'BAD_PASS','pass'))
 audit(b);check('Audit persisted',scalar('SELECT count(*) FROM passport_audit_events WHERE batch_id=?',b)==1)
 reject('Audit update forbidden',lambda:c.execute("UPDATE passport_audit_events SET summary='changed' WHERE batch_id=?",(b,)))
 a=media('image-A.png',pngA)
 v1=passport(b,pr,1);publish_fixture(b,v1,a)
 reject('Passport version UNIQUE',lambda:passport(b,pr,1),'UNIQUE')
 reject('Published revision update forbidden',lambda:c.execute("UPDATE passport_revisions SET payload='{}' WHERE id=?",(v1,)))
 reject('Published revision delete forbidden',lambda:c.execute('DELETE FROM passport_revisions WHERE id=?',(v1,)))
 reject('Published asset update forbidden',lambda:c.execute("UPDATE published_assets SET public_label='changed' WHERE passport_revision_id=?",(v1,)))
 media('image-B.png',pngB);c.execute("UPDATE media_assets SET availability_status='disabled' WHERE id=?",(a,))
 reject('Media delete does not cascade',lambda:c.execute('DELETE FROM media_assets WHERE id=?',(a,)),'FOREIGN KEY')
 pa=c.execute('SELECT * FROM published_assets WHERE passport_revision_id=?',(v1,)).fetchone();check('V1 frozen image A hash unchanged',hashlib.sha256((RT/'frozen'/pa['published_path']).read_bytes()).hexdigest()==pa['sha256']==hashlib.sha256(pngA).hexdigest())
 v2=passport(b,pr,2,v1);publish_fixture(b,v2)
 v3=passport(b,pr,3,v2);publish_fixture(b,v3)
 v4=passport(b,pr,4,v3,v2);publish_fixture(b,v4)
 check('V1 V2 V3 retained; V4 rollback source V2',scalar('SELECT count(*) FROM passport_revisions WHERE batch_id=?',b)==4 and scalar('SELECT rollback_source_revision_id FROM passport_revisions WHERE id=?',v4)==v2)
 c.execute('COMMIT')
 def tx(code,fail):
  c.execute('BEGIN IMMEDIATE')
  try:
   nb=batch(code,p,pr);item(nb,'MOISTURE');insert('batch_overrides',batch_id=nb,field_key='package_quantity',value_kind='decimal',value_text='20');audit(nb)
   if fail:item(nb,'MOISTURE')
   c.execute('COMMIT');return nb
  except Exception:c.execute('ROLLBACK');raise
 reject('Transaction deliberate failure',lambda:tx('PF-T4-TX-FAIL',True),'UNIQUE')
 check('Failed transaction leaves zero Batch',scalar("SELECT count(*) FROM batches WHERE batch_code='PF-T4-TX-FAIL'")==0)
 nb=tx('PF-T4-TX-OK',False);check('Transaction all 4 records commit',all(scalar('SELECT count(*) FROM '+t+' WHERE '+('id' if t=='batches' else 'batch_id')+'=?',nb)==1 for t in ['batches','inspection_items','batch_overrides','passport_audit_events']))
 # Concurrent independent writers, each transaction includes batch/inspection/audit.
 def worker(i):
  conn=connect();bid=id();stamp=now();start=time.monotonic()
  try:
   conn.execute('BEGIN IMMEDIATE')
   conn.execute('INSERT INTO batches(id,created_at,created_by,updated_at,updated_by,batch_code,product_id,base_product_revision_id) VALUES(?,?,1,?,1,?,?,?)',(bid,stamp,stamp,'PF-T4-CON-'+str(i),p,pr))
   conn.execute('INSERT INTO inspection_items(id,created_at,created_by,updated_at,updated_by,batch_id,item_code,name) VALUES(?,?,1,?,1,?,?,?)',(id(),stamp,stamp,bid,'T4-ITEM','T4 Test'))
   conn.execute('INSERT INTO passport_audit_events(id,batch_id,actor_user_id,created_at,event_type,entity_type,entity_id,summary) VALUES(?,?,1,?,?,?,?,?)',(id(),bid,stamp,'batch_created','batches',bid,'T4 concurrency'))
   conn.execute('COMMIT');return {'success':True,'ms':round((time.monotonic()-start)*1000,2)}
  except Exception as e:
   if conn.in_transaction:conn.execute('ROLLBACK')
   return {'success':False,'error':str(e)}
  finally:conn.close()
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:con=list(pool.map(worker,range(50)))
 check('10 writers / 50 transactions',all(x['success'] for x in con),{'concurrency':10,'attempted':50,'success':sum(x['success'] for x in con),'failed':sum(not x['success'] for x in con),'retries':0,'busy_timeout_ms':5000,'journal_mode':scalar('PRAGMA journal_mode'),'max_latency_ms':max(x.get('ms',0) for x in con)})
 check('Concurrent writes no lost Batch/Inspection/Audit',scalar("SELECT count(*) FROM batches WHERE batch_code LIKE 'PF-T4-CON-%'")==50 and scalar("SELECT count(*) FROM inspection_items i JOIN batches b ON b.id=i.batch_id WHERE b.batch_code LIKE 'PF-T4-CON-%'")==50 and scalar("SELECT count(*) FROM passport_audit_events a JOIN batches b ON b.id=a.batch_id WHERE b.batch_code LIKE 'PF-T4-CON-%'")==50)
 check('integrity_check',scalar('PRAGMA integrity_check')=='ok')
 check('foreign_key_check',len(c.execute('PRAGMA foreign_key_check').fetchall())==0)
 (RT/'evidence/schema-fixtures.json').write_text(json.dumps({'product':p,'r1':pr,'r2':r2,'batch':b,'versions':[v1,v2,v3,v4],'media_A':a}))
except Exception as e:
 if c.in_transaction:c.execute('ROLLBACK')
 results.append({'name':'Harness completion','status':'FAIL','detail':str(e)})
 raise
finally:
 (RT/'evidence/schema-tests.json').write_text(json.dumps(results,indent=2,ensure_ascii=False))
 c.close()
 print('Schema checks:',len(results),'PASS',sum(x['status']=='PASS' for x in results),'FAIL',sum(x['status']=='FAIL' for x in results))
