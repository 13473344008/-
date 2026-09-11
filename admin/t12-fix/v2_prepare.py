from flow import *
auth();f=json.loads(statefile.read_text());p='passport-products/'+f['product_id'];b=f['batch_id']
try:
 r2=next(x for x in ok(p)['revisions'] if x['revision_number']==2);f['r2']=r2['id'];check('R2 sealed default',r2['revision_status']=='sealed' and ok(p)['product']['current_revision_id']==r2['id']);check('R2 default leaves main on R1',ok('passport-batches/'+b)['batch']['base_product_revision_id']==f['r1']);f['batch2']=batch(f['product_id'],'PF-T12-TEST-002');check('New Batch binds R2',ok('passport-batches/'+f['batch2'])['batch']['base_product_revision_id']==f['r2']);save(f)
 frozen=json.loads((rt/'test-artifacts/v1-files.json').read_text());check('R2 working image change leaves every V1 release file unchanged',all((rt/'publish'/p).exists() and hashlib.sha256((rt/'publish'/p).read_bytes()).hexdigest()==sha for p,sha in frozen.items()))
 with db() as c:
  c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=? AND workflow_status='published'",(b,));assert c.total_changes==1
 (rt/'test-artifacts/v2-fixture-disclosure.json').write_text(json.dumps({'authority':'Original T12 section42 expressly permits controlled V2 candidate fixture','batch_id':b,'operation':'Reopen local candidate only; preserve all Published/history/Current. No SQL media creation. Following gallery upload, edit, Submit, Reject, correction, resubmit, Approve and Publish are real browser actions.'},indent=2))
finally:(rt/'test-artifacts/v2-prepare.json').write_text(json.dumps(checks,indent=2))
