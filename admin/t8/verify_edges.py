import verify_api as v
from verify_api import *
def main():
 v.admin=login(cred['admin_username'],cred['admin_password']);users=json.loads((rt/'test-artifacts/users.json').read_text())
 for kind,user in users.items():tokens[kind]=login(user['username'],cred['test_password'])
 f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());pid=f['product_id'];bid=batch(pid,'BT-T8-EDGE-'+runid);path='passport-batches/'+bid;rp=path+'/review';w=work(bid)
 w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':'10.50'},{'field_key':'raw_material_name','operation':'clear'},{'field_key':'process','operation':'set','process':[{'step_key':'dry','label':'Dry TEST'}]}]
 w['inspections']=[{'item_code':'MOISTURE','name':'T8 moisture','value_type':'decimal','numeric_value':'0.00','unit':'%','standard_value':None,'min_limit':'0','max_limit':'10','min_inclusive':True,'max_inclusive':True,'specification':'T8 only','test_method':'TEST','judgement':'pass','sort_order':1,'internal_note':'T8 private','is_public':True,'tested_on':'2026-09-09'}];ok(path,w,'PUT','editor')
 sec=path+'/sections';d=sample('public_test');d['is_public']=True;sid=ok(sec,{'expected_token':ok(sec)['token'],'section':d},token='editor')['id'];r=ok(rp+'/readiness');check('Public draft section fails readiness',not r['ready'] and any(e['code']=='unready_public_section' for e in r['errors']))
 d['status']='ready';d['translations'][0]['translation_status']='approved';ok(sec+'/'+sid,{'expected_token':ok(sec)['token'],'section':d},'PUT','editor');check('Source-only ready public section accepted',ok(rp+'/readiness')['ready'])
 # Readiness detects malformed persisted JSON without relying on the write endpoint.
 for table,column,value,key in [('batch_overrides','value_text','-1','invalid_override'),('inspection_items','numeric_value','1e3','invalid_inspection')]:
  with db() as c:
   row=c.execute('select id,'+column+' from '+table+' where batch_id=?'+(" and field_key='package_quantity'" if table=='batch_overrides' else ''),(bid,)).fetchone();c.execute('update '+table+' set '+column+'=? where id=?',(value,row[0]))
  r=ok(rp+'/readiness');check('Readiness '+key,not r['ready'] and any(e['code']==key for e in r['errors']))
  with db() as c:c.execute('update '+table+' set '+column+'=? where id=?',(row[1],row[0]))
 submit(bid);c=ok(rp)['current']['candidate'];check('Frozen numeric precision',c['inspections'][0]['numeric_value']=='0.00');check('Frozen override provenance',next(x for x in c['effective'] if x['field_key']=='package_quantity')['value']=='10.50');check('Frozen public custom section',c['effective_sections'][0]['content']['text']=='T8 frozen custom text')
 for table,col,val,where,args in [('batch_overrides','value_text','11',"batch_id=? and field_key='package_quantity'",(bid,)),('inspection_items','numeric_value','9','batch_id=?',(bid,)),('custom_sections','sort_order',9,'id=?',(sid,)),('custom_section_translations','title','change','custom_section_id=?',(sid,))]:
  with db() as conn:
   try:conn.execute('update '+table+' set '+col+'=? where '+where,(val,*args));denied=False
   except sqlite3.IntegrityError:denied=True
  check('Pending DB freeze '+table,denied)
 cur=ok(rp)['current'];check('Candidate mismatch rejected',req(rp+'/approve',{'review_id':cur['id'],'candidate_hash':'0'*64},token='reviewer').get('code')==409)
 check('Stale attempt rejected',req(rp+'/approve',{'review_id':str(uuid.uuid4()),'candidate_hash':cur['candidate_hash']},token='reviewer').get('code')==409)
 check('Mismatch keeps pending',ok(rp)['current']['decision']=='pending')
 check('Other reviewer may approve',decision(bid).get('code')==200)
 # A previous batch editor remains disqualified after another actor submits.
 own=batch(pid,'BT-T8-CREATOR-'+runid,'editor_reviewer');submit(own,'editor');check('Creator cannot review someone else submission',decision(own,token='editor_reviewer').get('code')==403)
 # Admin archive; no implicit pending -> archived shortcut.
 arch=batch(pid,'BT-T8-ARCHIVE-'+runid);check('Editor archive forbidden',req('passport-batches/'+arch+'/review/archive',{},token='editor').get('code')==403);ok('passport-batches/'+arch+'/review/archive',{});check('Admin archives draft',ok('passport-batches/'+arch)['batch']['workflow_status']=='archived');check('Archived submit conflict',req('passport-batches/'+arch+'/review/submit',{'expected_edit_version':1},token='editor').get('code')==409)
 check('Pending archive conflict',req('passport-batches/'+own+'/review/archive',{}).get('code')==409)
 for action in ['submit','approve','reject','return']:
  check('Strict review DTO '+action,req(rp+'/'+action,{'created_by':1},token='admin').get('code')==422)
 check('History candidate is current only',all('candidate' not in x for x in ok(rp)['history']))
 check('Approval metadata persists',ok(rp)['current']['reviewer']==users['reviewer']['username'] and ok(rp)['current']['reviewed_at'] is not None)
try:main()
finally:(rt/'test-artifacts/edges.json').write_text(json.dumps(checks,indent=2))
