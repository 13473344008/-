from verify_api import *
import helpers as h
statefile=rt/'test-artifacts/flow-state.json'
def save(f):statefile.write_text(json.dumps(f,ensure_ascii=False,indent=2))
def auth():
 h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
 for role,u in users.items():tokens[role]=login(u['username'],cred['test_password'])
def section(key,kind='text',title=None,hide=False):
 content={'text':'T12 TEST ONLY — not a commercial statement.'} if kind=='text' else {'items':[{'key':'application','label':'Application TEST','value':'Controlled test example'}]} if kind=='key_value' else {'columns':[{'key':'item','label':'Item TEST'},{'key':'value','label':'Value TEST'}],'rows':[{'cells':['Fixture','TEST ONLY']}]} if kind=='table' else {'caption':'T12 test image gallery'}
 return {'section_key':key,'operation':'add','section_type':kind,'sort_order':10,'is_visible':True,'is_public':True,'allow_hide':hide,'status':'ready','translations':[{'language_code':'en','translation_status':'approved','title':title or key,'content':content}]}
def putsection(path,s,sid=None):return ok(path+('/'+sid if sid else ''),{'expected_token':ok(path)['token'],'section':s},'PUT' if sid else 'POST','editor')['id']
def edit(b,weight='20',stage=1):
 w=work(b);w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':weight}]
 w['inspections']=[{'item_code':code,'name':name,'value_type':'decimal' if i<4 else 'integer','numeric_value':str(i+stage),'unit':['%','%','mPa.s','g/L','count'][i],'judgement':'informational','min_inclusive':True,'max_inclusive':True,'sort_order':i,'is_public':True,'specification':'T12 TEST — not a commercial specification'} for i,(code,name) in enumerate([('MOISTURE','Moisture'),('SUGAR','Reducing Sugar'),('VISCOSITY','Viscosity'),('DENSITY','Bulk Density'),('SPECKS','Black Specks')])]
 ok('passport-batches/'+b,w,'PUT','editor')
def weight(b):return next(x['value'] for x in ok('passport-batches/'+b)['effective'] if x['field_key']=='package_quantity')
def prepare():
 init();check('Four roles login anew',all(x in tokens for x in ['editor','reviewer','viewer']) and bool(h.admin))
 names={'en':'Potato Flakes T12 Test','zh-CN':'马铃薯雪花粉 T12 测试','es':'Copos de patata T12 Prueba','ar':'رقائق البطاطس T12 اختبار','fr':'Flocons de pomme de terre T12 Test','de':'Kartoffelflocken T12 Test'}
 steps=['Raw Potato Receiving','Washing','Peeling','Cooking','Mashing','Drum Drying','Flaking','Inspection','Packaging']
 content={'source_language':'en','package_quantity':'25','package_unit':'kg','package_type_code':'bag','shelf_life_days':365,'process_steps':[{'step_key':'s'+str(i+1)} for i in range(9)],'internal_note':'T12 private template note'}
 def translation(lang):return {'language_code':lang,'translation_status':'approved','product_name':names[lang],'raw_material_name':'Potato TEST','raw_material_type':'T12 TEST raw material','raw_material_origin':'Controlled TEST source','raw_material_description':'T12 raw material traceability fixture','package_description':'25kg/bag TEST packaging','inner_material':'TEST liner','storage_conditions':'TEST storage instructions','shelf_life_description':'T12 test period only','manufacturer_name':'T12 TEST ORGANIZATION','manufacturer_address':'TEST address — not a business location','process_labels':{'s'+str(i+1):s for i,s in enumerate(steps)}}
 pid=ok('passport-products',{'product_code':'PF-T12-TEST','content':content,'translations':[translation('en')]},token='editor')['id'];p='passport-products/'+pid;rev=ok(p)['revisions'][0];rid=rev['id'];rp=p+'/revisions/'+rid
 check('Product and real R1 draft created',rev['revision_status']=='draft' and rev['revision_number']==1)
 for lang in ['zh-CN','es','ar','fr','de']:
  ok(rp+'/translations',{'expected_token':ok(rp)['token'],'translation':translation(lang)},'PUT','editor')
 check('Six real translations coexist',len(ok(rp)['translations'])==6)
 sp=rp+'/sections';ids={}
 for key,kind,title,hide in [('traceability','text','Raw Material Traceability',False),('allergens','text','Allergen Statement',False),('application','key_value','Application Information',False),('test_table','table','T12 Test Table',False),('gallery','asset_gallery','T12 Gallery',False),('optional','text','Optional TEST note',True)]:ids[key]=putsection(sp,section(key,kind,title,hide))
 check('Four section types stored',len({s['section_type'] for s in ok(sp)['sections']})==4)
 ok(rp+'/seal',{'expected_token':ok(rp)['token']},token='editor');check('R1 sealed',ok(rp)['revision_status']=='sealed')
 check('Sealed core rejects changes',req(rp,{'expected_token':ok(rp)['token'],'content':content},'PUT','editor')['code']==409)
 check('Sealed translations reject changes',req(rp+'/translations',{'expected_token':ok(rp)['token'],'translation':translation('en')},'PUT','editor')['code']==409)
 check('Sealed sections reject changes',req(sp+'/'+ids['traceability'],{'expected_token':ok(sp)['token'],'section':section('traceability')},'PUT','editor')['code']==409)
 ok(p+'/default-revision',{'revision_id':rid,'expected_current_revision_id':None},'PUT','editor');check('Default R1 set',ok(p)['product']['current_revision_id']==rid)
 b=batch(pid,'PF-T12-TEST-001');bp='passport-batches/'+b;check('Batch fixed to R1',ok(bp)['batch']['base_product_revision_id']==rid)
 edit(b);check('Override set 20',weight(b)=='20');w=work(b);ok(bp,w,'PUT','editor');check('Override reset 25',weight(b)=='25');edit(b);check('Override final20 and five inspections',weight(b)=='20' and len(ok(bp)['inspections'])==5)
 bs=bp+'/sections';s=section('traceability');s['operation']='replace';s['translations'][0]['content']['text']='T12 batch traceability override';override=putsection(bs,s)
 s=section('optional');s.update(operation='hide',is_visible=False,translations=[]);hidden=putsection(bs,s)
 own=putsection(bs,section('batch_statement',title='T12 Batch Packaging Statement'))
 v=ok(bs);check('Batch section inheritance',any(x['source']=='inherited' for x in v['effective']));check('Batch override',any(x['section_key']=='traceability' and x['source']=='overridden' for x in v['effective']));check('Batch hide',any(x['section_key']=='optional' for x in v['hidden']));check('Batch-only section',any(x['section_key']=='batch_statement' and x['source']=='batch-only' for x in v['effective']))
 f={'product_id':pid,'r1':rid,'batch_id':b,'section_ids':ids,'batch_section_id':own,'content':content,'translations':{lang:translation(lang) for lang in names},'versions':[]};save(f)
 for role in ['reviewer','viewer']:
  check(role+' cannot edit batch',req(bp,work(b),'PUT',role)['code']==403)
  check(role+' cannot create product',req('passport-products',{},token=role)['code']==403)
 for path in [bp,bp+'/preview?kind=working',p,'passport-reviews']:check('Anonymous401 '+path,req(path,token=None)['code']==401)
 for role in ['editor','reviewer','viewer']:
  check(role+' cannot publish',req(bp+'/publication',{},token=role)['code']==403)
  check(role+' cannot rollback',req(bp+'/publication/rollback',{},token=role)['code']==403)
 check('Working preview20',ok(bp+'/preview?kind=working',token='editor')['payload']['packaging']['quantity']=='20')
 print('Main Draft ready; no media fixture or Published data written')
def resume_prepare():
 auth();pid=scalar("select id from products where product_code='PF-T12-TEST'");b=scalar("select id from batches where batch_code='PF-T12-TEST-001'");p='passport-products/'+pid;rid=ok(p)['revisions'][0]['id'];rp=p+'/revisions/'+rid;bp='passport-batches/'+b;bs=bp+'/sections'
 s=section('optional');s.update(operation='hide',is_visible=False,translations=[]);putsection(bs,s)
 own=putsection(bs,section('batch_statement',title='T12 Batch Packaging Statement'))
 v=ok(bs);check('Batch section inheritance',any(x['source']=='inherited' for x in v['effective']));check('Batch override',any(x['section_key']=='traceability' and x['source']=='overridden' for x in v['effective']));check('Batch hide',any(x['section_key']=='optional' for x in v['hidden']));check('Batch-only section',any(x['section_key']=='batch_statement' and x['source']=='batch-only' for x in v['effective']))
 rev=ok(rp);save({'product_id':pid,'r1':rid,'batch_id':b,'batch_section_id':own,'section_ids':{x['section_key']:x['id'] for x in ok(rp+'/sections')['sections']},'versions':[]})
 for role in ['reviewer','viewer']:
  check(role+' cannot edit batch',req(bp,work(b),'PUT',role)['code']==403);check(role+' cannot create product',req('passport-products',{},token=role)['code']==403)
 for path in [bp,bp+'/preview?kind=working',p,'passport-reviews']:check('Anonymous401 '+path,req(path,token=None)['code']==401)
 for role in ['editor','reviewer','viewer']:
  check(role+' cannot publish',req(bp+'/publication',{},token=role)['code']==403);check(role+' cannot rollback',req(bp+'/publication/rollback',{},token=role)['code']==403)
 check('Working preview20',ok(bp+'/preview?kind=working',token='editor')['payload']['packaging']['quantity']=='20')
 print('Main Draft ready; no media fixture or Published data written')
def pending():
 auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b;v=ok(bp+'/review');f['first_review']=v['current']['id'];f['first_candidate_hash']=v['current']['candidate_hash'];save(f)
 check('Submitted state pending_review',v['state']=='pending_review')
 check('Pending batch rejects edit',req(bp,work(b),'PUT','editor')['code']==409)
 check('Pending section rejects edit',req(bp+'/sections/'+f['batch_section_id'],{'expected_token':ok(bp+'/sections')['token'],'section':section('batch_statement')},'PUT','editor')['code']==409)
 check('Editor cannot approve',decision(b,token='editor')['code']==403)
 check('Viewer cannot decide',decision(b,token='viewer')['code']==403)
 check('Reject requires reason',decision(b,'reject')['code'] in (400,422))
 check('No Passport allocated by Submit',scalar('select count(*) from passport_revisions where batch_id=?',(b,))==0)
 check('Frozen review preview20',ok(bp+'/preview?kind=review&review_id='+f['first_review'],token='reviewer')['payload']['packaging']['quantity']=='20')
def rejected():
 auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b;v=ok(bp+'/review');check('Rejected returns Draft',v['state']=='draft')
 old=next(x for x in v['history'] if x['id']==f['first_review']);check('Exact rejection reason persisted',old['rejection_reason']=='T12 TEST — please adjust packaging statement.')
 s=section('batch_statement',title='T12 Batch Packaging Statement');s['translations'][0]['content']['text']='T12 TEST — packaging statement adjusted after rejection.';putsection(bp+'/sections',s,f['batch_section_id'])
 check('Editor adjusts statement after rejection',True)
 check('Old frozen candidate remains unchanged',next(x for x in ok(bp+'/review')['history'] if x['id']==f['first_review'])['candidate_hash']==f['first_candidate_hash'])
def v1():
 auth();f=json.loads(statefile.read_text());b=f['batch_id'];bp='passport-batches/'+b
 rid=submit(b);check('Second submit creates new attempt',rid!=f['first_review'] and len(ok(bp+'/review')['history'])==2)
 check('Reviewer approves',decision(b)['code']==200);check('Approve only Ready for Publish',ok(bp+'/review')['state']=='ready_for_publish' and scalar('select count(*) from passport_revisions where batch_id=?',(b,))==0)
 result=publish(b);check('Admin V1 text-only publish succeeds',result['code']==200 and result['data']['record']['publish_status']=='published');f['versions']=[result['data']['revision']['id']];save(f)
 check('V1 schema1.0',json.loads((rt/'publish/published/PF-T12-TEST-001.json').read_text())['schema_version']=='1.0')
 (rt/'test-artifacts/v1-publish.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
def revisions():
 auth();f=json.loads(statefile.read_text());p='passport-products/'+f['product_id'];b=f['batch_id'];r2=next(x['id'] for x in ok(p)['revisions'] if x['revision_number']==2);rp=p+'/revisions/'+r2;rev=ok(rp)
 fields=['source_language','category_code','origin_country_code','package_quantity','package_unit','package_type_code','shelf_life_days','process_steps','internal_note'];content={k:rev.get(k) for k in fields};content['package_quantity']='30';ok(rp,{'expected_token':rev['token'],'content':content},'PUT','editor');tr=next(x for x in ok(rp)['translations'] if x['language_code']=='en');tr={k:v for k,v in tr.items() if k not in ['id','product_revision_id','created_at','created_by','updated_at','updated_by']};tr['translation_status']='approved';ok(rp+'/translations',{'expected_token':ok(rp)['token'],'translation':tr},'PUT','editor');ok(rp+'/seal',{'expected_token':ok(rp)['token']},token='editor');ok(p+'/default-revision',{'revision_id':r2,'expected_current_revision_id':f['r1']},'PUT','editor')
 check('R2 default leaves old Batch at R1',ok('passport-batches/'+b)['batch']['base_product_revision_id']==f['r1']);b2=batch(f['product_id'],'PF-T12-TEST-002');check('New Batch binds R2',ok('passport-batches/'+b2)['batch']['base_product_revision_id']==r2)
 response=req('passport-batches/'+b+'/clone',{'batch_code':'PF-T12-TEST-003','production_date':'2026-09-10','expiry_date':'2027-09-10','expected_edit_version':ok('passport-batches/'+b)['batch']['edit_version']},token='editor')
 f.update(r2=r2,batch2=b2,clone_response=response);save(f)
 checks.append({'name':'Required Clone Published main Batch','status':'PASS' if response['code']==200 else 'FAIL','actual':response});print(checks[-1],flush=True)
if __name__=='__main__':
 phase=sys.argv[1] if len(sys.argv)>1 else 'prepare'
 try:globals()[phase]()
 finally:(rt/'test-artifacts'/('flow-'+phase+'.json')).write_text(json.dumps(checks,ensure_ascii=False,indent=2))
