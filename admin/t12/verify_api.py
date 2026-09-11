from helpers import *
import helpers as h,struct,zlib

def init():
 h.admin=login(cred['admin_username'],cred['admin_password'])
 for kind in ['editor','reviewer','viewer','editor_reviewer']:
  username='t12-'+kind+'-'+runid;role=scalar('select role_id from sys_role where role_key=?',('passport_'+kind,))
  ok('sys-user',{'username':username,'password':cred['test_password'],'nickName':'T12 '+kind,'phone':'00000000000','email':'t12@example.invalid','deptId':1,'postId':1,'roleId':role,'status':'2'})
  tokens[kind]=login(username,cred['test_password']);users[kind]={'username':username,'id':scalar('select user_id from sys_user where username=?',(username,))}
 (rt/'test-artifacts'/('fresh-users.json' if mode=='fresh' else 'users.json')).write_text(json.dumps(users))

def png(color):
 def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',2,2,8,2,0,0,0))+chunk(b'tEXt',b'Comment\x00PRIVATE-METADATA-T12')+chunk(b'IDAT',zlib.compress(b'\0'+bytes(color)*2+b'\0'+bytes(color)*2))+chunk(b'IEND',b'')
def pubreq(bid):
 r=ok('passport-batches/'+bid+'/review')['current'];current=ok('passport-batches/'+bid+'/publication')['current'];return {'review_id':r['id'],'candidate_hash':r['candidate_hash'],'idempotency_key':str(uuid.uuid4()),'expected_current_revision_id':current['id'] if current else None}
def publish(bid,request=None,token='admin'):return req('passport-batches/'+bid+'/publication',request or pubreq(bid),token=token)
def approved(pid,suffix,assets=False):
 assert not assets, 'T12 strict acceptance has no media fixture authorization'
 b=batch(pid,'TEST-T12-'+suffix+'-'+runid);a=None;submit(b);assert decision(b).get('code')==200;return b,a
