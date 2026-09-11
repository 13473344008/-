from helpers import *
import helpers as h,struct,zlib

def init():
 h.admin=login(cred['admin_username'],cred['admin_password'])
 for kind in ['editor','reviewer','viewer','editor_reviewer']:
  username='t9-'+kind+'-'+runid;role=scalar('select role_id from sys_role where role_key=?',('passport_'+kind,))
  ok('sys-user',{'username':username,'password':cred['test_password'],'nickName':'T9 '+kind,'phone':'00000000000','email':'t9@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
  tokens[kind]=login(username,cred['test_password']);users[kind]={'username':username,'id':scalar('select user_id from sys_user where username=?',(username,))}
 (rt/'test-artifacts'/('fresh-users.json' if mode=='fresh' else 'users.json')).write_text(json.dumps(users))

def png(color):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,2,0,0,0))+chunk(b'tEXt',b'Comment\x00PRIVATE-METADATA-T9')+chunk(b'IDAT',zlib.compress(b'\0'+bytes(color)*2+b'\0'+bytes(color)*2))+chunk(b'IEND',b'')
def asset(bid,public=True,index=1):
 section=sample('gallery'+str(index));section.update(section_type='asset_gallery',is_public=public,status='ready');section['translations']=[{'language_code':'en','translation_status':'approved','title':'T9 test image','content':{'caption':'T9 controlled test fixture'}}]
 sp='passport-batches/'+bid+'/sections';sid=ok(sp,{'expected_token':ok(sp)['token'],'section':section},token='editor')['id']
 aid=str(uuid.uuid4());raw=png((index*30%255,40,80));key=aid+'.png';(rt/'private-media'/key).write_bytes(raw);now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z');uid=users['editor']['id']
 # Controlled fixture attaches existing-model media while Draft. Approval itself always uses the real API.
 with db() as c:
  c.execute('INSERT INTO media_assets(id,created_at,created_by,storage_key,original_filename,mime_type,file_size,sha256,is_public_eligible) VALUES(?,?,?,?,?,?,?,?,?)',(aid,now,uid,key,'../../unsafe PRIVATE filename.png','image/png',len(raw),hashlib.sha256(raw).hexdigest(),int(public)))
  c.execute('INSERT INTO asset_links(id,created_at,created_by,updated_at,updated_by,custom_section_id,media_asset_id,asset_key,asset_role,public_label,is_public) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),now,uid,now,uid,sid,aid,'image'+str(index),'section_image','T9 test image',int(public)))
 return {'media_id':aid,'key':key,'hash':hashlib.sha256(raw).hexdigest()}
def pubreq(bid):
 r=ok('passport-batches/'+bid+'/review')['current'];current=ok('passport-batches/'+bid+'/publication')['current'];return {'review_id':r['id'],'candidate_hash':r['candidate_hash'],'idempotency_key':str(uuid.uuid4()),'expected_current_revision_id':current['id'] if current else None}
def publish(bid,request=None,token='admin'):return req('passport-batches/'+bid+'/publication',request or pubreq(bid),token=token)
def approved(pid,suffix,assets=False):
 b=batch(pid,'TEST-T9-'+suffix+'-'+runid);a=asset(b) if assets else None;submit(b);assert decision(b).get('code')==200;return b,a

def main():
 init();pid,rid=product('TEST-P-T9-'+runid);bid=batch(pid,'TEST-T9-MAIN-'+runid);path='passport-batches/'+bid
 check('Draft publish denied',req(path+'/publication',{'review_id':str(uuid.uuid4()),'candidate_hash':'0'*64,'idempotency_key':str(uuid.uuid4()),'expected_current_revision_id':None}).get('code')==409)
 a=asset(bid);private=asset(bid,False,2)
 w=work(bid);w['inspections']=[{'item_code':'PRIVATE_TEST','name':'PRIVATE-INSPECTION-T9','value_type':'text','text_value':'PRIVATE-RESULT','judgement':'informational','min_inclusive':True,'max_inclusive':True,'sort_order':1,'is_public':False}]
 # Full aggregate editing rejects unmanaged linked section assets? Section assets are unaffected by batch core save.
 ok(path,w,'PUT','editor')
 submit(bid);rq=pubreq(bid);check('Pending review publish denied',publish(bid,rq).get('code')==409)
 check('Reviewer approves',decision(bid).get('code')==200)
 check('Tampered candidate hash rejected',publish(bid,{**rq,'candidate_hash':'0'*64}).get('code')==409)
 for role,code in [('editor',403),('reviewer',403),('viewer',403),(None,401)]:check('Publish role '+str(role),publish(bid,rq,role).get('code')==code)
 result=publish(bid,rq);check('Admin ready publish V1 succeeds',result.get('code')==200 and result['data']['record']['publish_status']=='published')
 v=result['data'];p=v['revision'];raw=(rt/'publish'/p['snapshot_path']).read_bytes();payload=json.loads(raw);check('Actual canonical payload SHA256',hashlib.sha256(raw).hexdigest()==p['payload_hash']);check('Public schema version',payload['schema_version']=='1.0');check('Internal values excluded',b'internal_note' not in raw and b'PRIVATE-' not in raw and b'storage_key' not in raw and b'created_by' not in raw);check('Private inspections omitted',payload['inspection']==[]);check('Private sections omitted',len(payload['custom_sections'])==1);check('Private assets omitted',len(payload['assets'])==1)
 actual=(rt/'publish'/payload['assets'][0]['path']).read_bytes();check('Normalized image SHA',hashlib.sha256(actual).hexdigest()==payload['assets'][0]['sha256']);check('Image metadata stripped',b'PRIVATE-METADATA-T9' not in actual);check('Unsafe original name not used publicly',b'unsafe PRIVATE' not in raw and payload['assets'][0]['path'].startswith('assets/sha256/'))
 check('Current JSON exact bytes',raw==(rt/'publish/published'/('TEST-T9-MAIN-'+runid+'.json')).read_bytes())
 check('Same idempotency key returns original record',publish(bid,rq)['data']['record']['id']==v['record']['id']);check('Same candidate new request cannot duplicate',publish(bid).get('code')==409)
 with db() as c:
  for name,sql,args in [('immutable revision','UPDATE passport_revisions SET payload_hash=? WHERE id=?',('0'*64,p['id'])),('immutable published asset','UPDATE published_assets SET public_label=? WHERE passport_revision_id=?',('changed',p['id'])),('immutable record','DELETE FROM publish_records WHERE id=?',(v['record']['id'],))]:
   try:c.execute(sql,args);blocked=False
   except sqlite3.IntegrityError:blocked=True
   check(name,blocked)
 # Source file replacement cannot change immutable historical public bytes.
 (rt/'private-media'/a['key']).write_bytes(png((90,90,90)));check('Source replacement leaves V1 asset unchanged',(rt/'publish'/payload['assets'][0]['path']).read_bytes()==actual)
 # Missing original after approval fails; new attempt after restoring source succeeds.
 bad,ba=approved(pid,'MISSING',True);saved=(rt/'private-media'/ba['key']).read_bytes();(rt/'private-media'/ba['key']).unlink();failed=publish(bad);check('Missing source creates failed record',failed.get('code')==200 and failed['data']['record']['publish_status']=='failed');check('Failure preserves approval and no public head',ok('passport-batches/'+bad+'/review')['state']=='ready_for_publish' and ok('passport-batches/'+bad+'/publication')['current'] is None)
 (rt/'private-media'/ba['key']).write_bytes(saved);retry=publish(bad);check('Retry separate attempt succeeds',retry['data']['record']['publish_status']=='published' and retry['data']['record']['id']!=failed['data']['record']['id'])
 concurrent,_=approved(pid,'RACE');requests=[pubreq(concurrent) for _ in range(5)]
 with concurrent_futures() as pool:out=list(pool.map(lambda q:publish(concurrent,q),requests))
 check('Five same-batch publishes produce one success',sum(x.get('code')==200 and x.get('data',{}).get('record',{}).get('publish_status')=='published' for x in out)==1)
 distinct=[approved(pid,'DIFF'+str(i))[0] for i in range(3)];qs=[pubreq(b) for b in distinct]
 with concurrent_futures() as pool:out=list(pool.map(lambda item:publish(*item),zip(distinct,qs)))
 check('Different batches publish concurrently',all(x.get('code')==200 and x['data']['record']['publish_status']=='published' for x in out))
 # Keep approved fixtures for injected service tests, browser tests use their own authentic workflow.
 faults={}
 for stage in ['build','write','copy1','copy2','validation','rename','finalize']:
  b,aa=approved(pid,'FAULT'+stage,True)
  if stage=='copy2':
   ok('passport-batches/'+b+'/review/return',{'review_id':ok('passport-batches/'+b+'/review')['current']['id'],'reason':'Add second controlled image'},token='editor');asset(b,True,3);submit(b);assert decision(b).get('code')==200
  faults[stage]={'batch_id':b,'request':pubreq(b)}
 fixture={'product_id':pid,'batch_id':bid,'revision':p,'publish_record':v['record'],'faults':faults,'runid':runid};(rt/'test-artifacts'/('fresh-api-fixtures.json' if mode=='fresh' else 'api-fixtures.json')).write_text(json.dumps(fixture,ensure_ascii=False,indent=2))
 check('DB integrity',scalar('pragma integrity_check')=='ok')
 with db() as c:check('Foreign keys',c.execute('pragma foreign_key_check').fetchall()==[])
def concurrent_futures():return concurrent.futures.ThreadPoolExecutor(5)
if __name__=='__main__':
 try:main()
 finally:(rt/'test-artifacts'/('api-'+mode+'.json')).write_text(json.dumps(checks,indent=2))
