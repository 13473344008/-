from flow import *
auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b;old=(rt/'publish/versions/PF-T12-TEST-001/v1.json').read_bytes()
try:
 # Explicit T12 section 42 exception ONLY: reopen a local Published candidate for V2.
 with db() as c:
  c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=? AND workflow_status='published'",(b,));assert c.total_changes==1
 (rt/'test-artifacts/v2-fixture-disclosure.json').write_text(json.dumps({'authority':'T12 section42 expressly permits T9/T10 controlled candidate fixture','batch_id':b,'operation':'Clear current working review binding and reopen local Draft; preserved Published/history/current; no assets SQL; all following edit/submit/approve/publish use real API.'},indent=2))
 edit(b,'22',2);s=section('batch_statement',title='T12 Batch Packaging Statement');s['translations'][0]['content']['text']='T12 V2 TEST — updated packaging statement.';putsection(bp+'/sections',s,f['batch_section_id']);submit(b);check('V2 approved',decision(b)['code']==200);result=publish(b);check('V2 published',result['code']==200 and result['data']['revision']['version_number']==2 and result['data']['record']['publish_status']=='published');f['versions'].append(result['data']['revision']['id']);save(f)
 check('V1 bytes unchanged after V2',(rt/'publish/versions/PF-T12-TEST-001/v1.json').read_bytes()==old)
 diff=ok(bp+'/publication/compare?left='+f['versions'][0]+'&right='+f['versions'][1]);(rt/'test-artifacts/version-compare.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2));check('Version comparison has business changes',len(diff['differences'])>=3)
 v2=(rt/'publish/versions/PF-T12-TEST-001/v2.json').read_bytes();r=ok(bp+'/publication/rollback',{'target_revision_id':f['versions'][0],'expected_current_revision_id':f['versions'][1],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T12 TEST — restore approved V1 content'})
 check('Rollback creates V3',r['record']['publish_status']=='published' and r['revision']['version_number']==3 and r['revision']['rollback_source_revision_id']==f['versions'][0]);f['versions'].append(r['revision']['id']);save(f)
 check('Rollback preserves V1/V2',(rt/'publish/versions/PF-T12-TEST-001/v1.json').read_bytes()==old and (rt/'publish/versions/PF-T12-TEST-001/v2.json').read_bytes()==v2)
 for i,rid in enumerate(f['versions'],1):check('V'+str(i)+' full server integrity',ok(bp+'/publication/versions/'+rid+'/integrity')['state']=='verified')
 history=ok(bp+'/publication/history');(rt/'test-artifacts/main-history.json').write_text(json.dumps(history,ensure_ascii=False,indent=2));check('Three successful versions retained',len(history['versions'])==3)
finally:(rt/'test-artifacts/versions.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
