from flow import *
import urllib.request,urllib.error

def upload(path,name='main.png',mime='image/png',raw=None,role='editor',token=None,label='T12 TEST media',public=True):
 raw=(rt/'test-artifacts'/name).read_bytes() if raw is None else raw
 boundary='t12'+uuid.uuid4().hex;parts=[]
 values={'expected_token':token or ok(path,token=role)['token'],'public_label':label,'is_public':str(public).lower()}
 for k,v in values.items():parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
 parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+raw+b'\r\n');parts.append(f'--{boundary}--\r\n'.encode())
 tok=h.admin if role=='admin' else tokens.get(role)
 try:
  with urllib.request.urlopen(urllib.request.Request(base+path,data=b''.join(parts),headers={'Authorization':'Bearer '+tok,'Content-Type':'multipart/form-data; boundary='+boundary}),timeout=30) as res:return json.load(res)
 except urllib.error.HTTPError as e:return json.load(e)

def main():
 auth();pid=ok('passport-products',{'product_code':'PF-T12-TEST-MEDIA-CHECK','content':{'source_language':'en','process_steps':[]},'translations':[{'language_code':'en','translation_status':'approved','product_name':'Media checks TEST','process_labels':{}}]},token='editor')['id'];rid=ok('passport-products/'+pid)['revisions'][0]['id'];path=f'passport-products/{pid}/revisions/{rid}/media'
 initial=ok(path)['token'];r=upload(path);check('PNG actual business upload',r['code']==200);item=ok(path)['items'][0];check('Media detail MIME SHA size dimensions',item['mime_type']=='image/png' and item['width']==800 and item['height']==480 and item['sha256']==hashlib.sha256((rt/'test-artifacts/main.png').read_bytes()).hexdigest());check('Media DTO excludes storage_key','storage_key' not in item)
 check('Stale upload token rejected',upload(path,token=initial)['code']==409)
 for role in ['reviewer','viewer']:
  check(role+' read image',len(ok(path,token=role)['items'])==1);check(role+' upload forbidden',upload(path,role=role)['code']==403);check(role+' detach forbidden',req(path+'/'+item['id'],{'expected_token':ok(path)['token']},'DELETE',role)['code']==403)
 for name,mime,raw,label in [('fake.png','image/png',b'<script>alert(1)</script>','bad-content'),('fake.svg','image/png',(rt/'test-artifacts/main.png').read_bytes(),'bad-extension'),('fake.png','text/html',(rt/'test-artifacts/main.png').read_bytes(),'bad-mime'),('large.png','image/png',b'x'*(2097153),'oversize')]:check(label+' rejected',upload(path,name,mime,raw)['code']==422)
 # A valid header with prohibited dimensions must be rejected before allocating pixels.
 from PIL import Image
 import io
 buf=io.BytesIO();Image.new('RGB',(4097,1)).save(buf,format='PNG');check('Pixel limit rejected',upload(path,'wide.png','image/png',buf.getvalue())['code']==422)
 before=scalar('select count(*) from media_assets');files=set(p.name for p in (rt/'private-media').iterdir())
 ok(path+'/'+item['id'],{'expected_token':ok(path)['token']},'DELETE','editor');check('Draft detach allowed and keeps source',not ok(path)['items'] and scalar('select count(*) from media_assets')==before)
 with db() as c:c.execute("CREATE TRIGGER t12fix_media_audit_fail BEFORE INSERT ON passport_audit_events WHEN NEW.event_type='media_replaced' BEGIN SELECT RAISE(ABORT,'T12 transaction failure'); END")
 try:check('Media audit failure returned',upload(path)['code']==500)
 finally:
  with db() as c:c.execute('DROP TRIGGER t12fix_media_audit_fail')
 check('Failed upload has no partial DB or private file',scalar('select count(*) from media_assets')==before and set(p.name for p in (rt/'private-media').iterdir())==files and not ok(path)['items'])
 check('Private JPEG uploads',upload(path,'gallery.jpg','image/jpeg',public=False)['code']==200)
 private=ok(path)['items'][0];check('Explicit nonpublic link saved',not private['is_public']);ok(path+'/'+private['id'],{'expected_token':ok(path)['token']},'DELETE','editor')
 f=json.loads(statefile.read_text());sealed=f"passport-products/{f['product_id']}/revisions/{f['r1']}/media";check('Sealed template upload denied',upload(sealed)['code']==409);v=ok(sealed)['items'][0];check('Sealed template detach denied',req(sealed+'/'+v['id'],{'expected_token':ok(sealed)['token']},'DELETE','editor')['code']==409)
 other=f"passport-products/{pid}/revisions/{rid}/sections/{f['section_ids']['gallery']}/media";check('Cross owner gallery access denied',req(other)['code']==404)
 (rt/'test-artifacts/media-check-fixture.json').write_text(json.dumps({'product_id':pid,'r1':rid,'path':path}))
if __name__=='__main__':
 try:main()
 finally:(rt/'test-artifacts/media-checks.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
