from helpers import *
import helpers as h
h.admin=login(cred['admin_username'],cred['admin_password'])
f=json.loads((rt/'test-artifacts/api-fixtures.json').read_text());b=f['batch_id'];v=f['revision'];r=f['publish_record'];path='passport-batches/'+b+'/publication'
check('Restart API published current retained',ok(path)['current']['id']==v['id'])
q={'review_id':v['source_review_record_id'],'candidate_hash':v['source_content_hash'],'idempotency_key':r['idempotency_key'],'expected_current_revision_id':r['expected_current_revision_id']}
check('Exact repeated request returns same immutable record',ok(path,q)['record']['id']==r['id'])
check('Idempotency key different hash rejected',req(path,{**q,'candidate_hash':'0'*64}).get('code')==409)
check('Idempotency key different expected current rejected',req(path,{**q,'expected_current_revision_id':str(uuid.uuid4())}).get('code')==409)
(rt/'test-artifacts/post-restart.json').write_text(json.dumps(checks,indent=2))
