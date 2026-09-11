from flow import *
auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 source=json.loads((rt/'test-artifacts/clone-source-before.json').read_text())
 with db() as c:
  c.row_factory=sqlite3.Row
  check('Clone leaves Published source byte-for-byte unchanged',dict(c.execute('select * from batches where id=?',(b,)).fetchone())==source['batch']);check('Clone adds no source audit event',[dict(x) for x in c.execute('select * from passport_audit_events where batch_id=? order by id',(b,))]==source['audit'])
 clone=ok('passport-batches/'+f['clone_id']);cb=clone['batch'];check('New Clone Draft keeps Product R1',cb['workflow_status']=='draft' and cb['product_id']==f['product_id'] and cb['base_product_revision_id']==f['r1']);check('Clone dates reset',not cb['production_date'] and not cb['expiry_date']);check('Clone quality and review reset',cb['quality_status']=='pending' and not cb['current_review_record_id']);check('Clone five inspection structures preserved',len(clone['inspections'])==5);check('Clone all results cleared',all(not x.get('numeric_value') and not x.get('text_value') and not x.get('tested_on') for x in clone['inspections']));check('Clone no Passport or publishing',scalar('select count(*) from passport_revisions where batch_id=?',(cb['id'],))==0);check('Clone allowed override preserved',weight(cb['id'])=='20')
 draft=ok('passport-batches/'+cb['id']+'/clone',{'batch_code':'PF-T12-TEST-CLONE-DRAFT','expected_edit_version':cb['edit_version']},token='editor');check('Draft clone supported',bool(draft['id']))
 for role in ['reviewer','viewer']:check(role+' cannot clone Published',req(bp+'/clone',{'batch_code':'PF-T12-TEST-FORBIDDEN-'+role,'expected_edit_version':source['batch']['edit_version']},token=role)['code']==403)
finally:(rt/'test-artifacts/clone-checks.json').write_text(json.dumps(checks,indent=2))
