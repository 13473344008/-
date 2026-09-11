from flow import *
auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b
try:
 check('Fresh Batch binds sealed R1',ok(bp)['batch']['base_product_revision_id']==f['r1']);check('UI created five inspections',len(ok(bp)['inspections'])==5)
 edit(b);check('20kg override',weight(b)=='20');w=work(b);w['inspections']=[];ok(bp,w,'PUT','editor');check('Override reset restores25',weight(b)=='25');edit(b)
 path=bp+'/sections';s=section('traceability');s['operation']='replace';putsection(path,s);s=section('optional');s.update(operation='hide',is_visible=False,translations=[]);putsection(path,s)
 v=ok(path);f['batch_section_id']=next(x['id'] for x in v['sections'] if x['section_key']=='batch_statement');save(f)
 check('Inheritance override hide batch-only',all(any(x['source']==source for x in v['effective']) for source in ['inherited','overridden','batch-only']) and any(x['section_key']=='optional' for x in v['hidden']))
 for role in ['reviewer','viewer']:
  check(role+' cannot change Batch',req(bp,work(b),'PUT',role)['code']==403)
 for role in ['editor','reviewer','viewer']:check(role+' cannot publish',req(bp+'/publication',{},token=role)['code']==403)
 for path in [bp,bp+'/preview?kind=working',bp+'/publication/history']:check('Anonymous denied '+path,req(path,token=None)['code']==401)
 check('Working preview contains actual image assets',len(ok(bp+'/preview?kind=working',token='editor')['payload']['assets'])==2)
finally:(rt/'test-artifacts/working.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
