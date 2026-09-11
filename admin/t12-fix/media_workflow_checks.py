from media_checks import upload
from flow import *
auth();f=json.loads(statefile.read_text());b=f['clone_id'];bp='passport-batches/'+b
try:
 sid=next(s['id'] for s in ok(bp+'/sections')['sections'] if s['section_key']=='media_guard');path=bp+'/sections/'+sid+'/media';a=ok(path)['items'][0];check('Batch Draft gallery upload persisted',bool(a['id']))
 w=work(b);w['content'].update(production_date='2026-09-10',expiry_date='2027-09-10');ok(bp,w,'PUT','editor')
 for sec in ok(bp+'/sections')['sections']:
  if sec['status']=='draft' and sec['operation'] not in ['hide','inherit']:
   q={k:sec[k] for k in ['section_key','operation','section_type','sort_order','is_visible','is_public','allow_hide','status']};q['status']='ready';q['translations']=[{**{k:t[k] for k in ['language_code','title','content']},'translation_status':'approved'} for t in sec['translations']];putsection(bp+'/sections',q,sec['id'])
 check('Private gallery excluded from public candidate',a['asset_key'] not in json.dumps(ok(bp+'/preview?kind=working')['payload']['assets']))
 # Supply new explicit dates to this independent clone; original clone-reset evidence is preserved.
 w=work(b);w['content'].update(production_date='2026-09-10',expiry_date='2027-09-10');ok(bp,w,'PUT','editor');submit(b)
 for state in ['pending_review','ready_for_publish']:
  check(state+' media upload locked',upload(path)['code']==409);check(state+' media detach locked',req(path+'/'+a['id'],{'expected_token':ok(path)['token']},'DELETE','editor')['code']==409);check(state+' clone rejected',req(bp+'/clone',{'batch_code':'PF-T12-TEST-LOCKED-'+state,'expected_edit_version':ok(bp)['batch']['edit_version']},token='editor')['code']==409)
  if state=='pending_review':check('Guard Reviewer approve',decision(b)['code']==200)
 check('Guard image candidate published',publish(b)['data']['record']['publish_status']=='published');check('Published media locked',upload(path)['code']==409)
 source=ok(path)['items'];cl=ok(bp+'/clone',{'batch_code':'PF-T12-TEST-MEDIA-CLONE','expected_edit_version':ok(bp)['batch']['edit_version']},token='editor')['id'];cs=next(s for s in ok('passport-batches/'+cl+'/sections')['sections'] if s['section_key']=='media_guard');copies=ok('passport-batches/'+cl+'/sections/'+cs['id']+'/media')['items'];check('Clone gets new working links to immutable media',copies[0]['id']!=source[0]['id'] and copies[0]['media_id']==source[0]['media_id']);check('Clone private flag preserved',not copies[0]['is_public'])
finally:(rt/'test-artifacts/media-workflow-checks.json').write_text(json.dumps(checks,indent=2))
