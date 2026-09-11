from helpers import *
import helpers as h,struct,zlib

def init():
 h.admin=login(cred['admin_username'],cred['admin_password'])
 for kind in ['editor','reviewer','viewer','editor_reviewer']:
  username='t11-'+kind+'-'+runid;role=scalar('select role_id from sys_role where role_key=?',('passport_'+kind,))
  ok('sys-user',{'username':username,'password':cred['test_password'],'nickName':'T11 '+kind,'phone':'00000000000','email':'t11@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
  tokens[kind]=login(username,cred['test_password']);users[kind]={'username':username,'id':scalar('select user_id from sys_user where username=?',(username,))}
 (rt/'test-artifacts'/('fresh-users.json' if mode=='fresh' else 'users.json')).write_text(json.dumps(users))

def png(color):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,2,0,0,0))+chunk(b'tEXt',b'Comment\x00PRIVATE-METADATA-T11')+chunk(b'IDAT',zlib.compress(b'\0'+bytes(color)*2+b'\0'+bytes(color)*2))+chunk(b'IEND',b'')
def asset(bid,public=True,index=1):
 section=sample('gallery'+str(index));section.update(section_type='asset_gallery',is_public=public,status='ready');section['translations']=[{'language_code':'en','translation_status':'approved','title':'T11 test image','content':{'caption':'T11 controlled test fixture'}}]
 sp='passport-batches/'+bid+'/sections';sid=ok(sp,{'expected_token':ok(sp)['token'],'section':section},token='editor')['id']
 aid=str(uuid.uuid4());raw=png((index*30%255,40,80));key=aid+'.png';(rt/'private-media'/key).write_bytes(raw);now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z');uid=users['editor']['id']
 # Controlled fixture attaches existing-model media while Draft. Approval itself always uses the real API.
 with db() as c:
  c.execute('INSERT INTO media_assets(id,created_at,created_by,storage_key,original_filename,mime_type,file_size,sha256,is_public_eligible) VALUES(?,?,?,?,?,?,?,?,?)',(aid,now,uid,key,'../../unsafe PRIVATE filename.png','image/png',len(raw),hashlib.sha256(raw).hexdigest(),int(public)))
  c.execute('INSERT INTO asset_links(id,created_at,created_by,updated_at,updated_by,custom_section_id,media_asset_id,asset_key,asset_role,public_label,is_public) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),now,uid,now,uid,sid,aid,'image'+str(index),'section_image','T11 test image',int(public)))
 return {'media_id':aid,'key':key,'hash':hashlib.sha256(raw).hexdigest()}
def pubreq(bid):
 r=ok('passport-batches/'+bid+'/review')['current'];current=ok('passport-batches/'+bid+'/publication')['current'];return {'review_id':r['id'],'candidate_hash':r['candidate_hash'],'idempotency_key':str(uuid.uuid4()),'expected_current_revision_id':current['id'] if current else None}
def publish(bid,request=None,token='admin'):return req('passport-batches/'+bid+'/publication',request or pubreq(bid),token=token)
def approved(pid,suffix,assets=False):
 b=batch(pid,'TEST-T11-'+suffix+'-'+runid);a=asset(b) if assets else None;submit(b);assert decision(b).get('code')==200;return b,a
