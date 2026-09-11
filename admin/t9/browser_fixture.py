from verify_api import *
import helpers as h
h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
for role in ['editor','reviewer']:tokens[role]=login(users[role]['username'],cred['test_password'])
action,bid=sys.argv[1:3]
if action=='asset':
 a=asset(bid);(rt/'test-artifacts/browser-asset.json').write_text(json.dumps(a));print(json.dumps(a))
elif action=='failure':
 # T9-only V2 fixture, no production Published-to-Draft endpoint or UI is added.
 with db() as c:c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=?",(bid,))
 submit(bid);assert decision(bid).get('code')==200
 a=json.loads((rt/'test-artifacts/browser-asset.json').read_text());p=rt/'private-media'/a['key'];p.rename(p.with_suffix('.missing'));print(json.dumps({'ready':True}))
elif action=='restore':
 a=json.loads((rt/'test-artifacts/browser-asset.json').read_text());p=rt/'private-media'/a['key'];p.with_suffix('.missing').rename(p);print(json.dumps({'restored':True}))
