from verify_api import *
import helpers as h

def reopen(b):
 # T11-only controlled fixture transition; immutable history is never altered.
 with db() as c:c.execute("UPDATE batches SET workflow_status='draft',current_review_record_id=NULL,submitted_input=NULL,submitted_content_hash=NULL,submitted_preview_hash=NULL,submitted_edit_version=NULL,submitted_schema_version=NULL,submitted_builder_version=NULL,submitted_by=NULL,submitted_at=NULL,reviewed_by=NULL,reviewed_at=NULL WHERE id=?",(b,))
def edit(b,weight):
 w=work(b);w['overrides']=[{'field_key':'package_quantity','operation':'set','value_text':str(weight)},{'field_key':'package_unit','operation':'set','value_text':'kg'}]
 w['inspections']=[{'item_code':'TEST_'+str(i),'name':name,'value_type':'text' if status in ['pass','fail','informational'] else 'none','text_value':'Controlled TEST result' if status in ['pass','fail','informational'] else None,'judgement':status,'min_inclusive':True,'max_inclusive':True,'sort_order':i,'is_public':True} for i,(name,status) in enumerate(zip(['Moisture TEST','Color TEST','Viscosity TEST','Density TEST','Microbiology TEST','Particle TEST'],['pass','fail','informational','not_tested','not_applicable','pending']))]
 ok('passport-batches/'+b,w,'PUT','editor')
def sealpub(b):
 submit(b);assert decision(b).get('code')==200
 r=publish(b);assert r.get('code')==200 and r['data']['record']['publish_status']=='published',r
 return r['data']
def auth():
 h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
 for role,u in users.items():tokens[role]=login(u['username'],cred['test_password'])
def create():
 init()
 names={'en':'Potato Flakes — TEST','zh-CN':'马铃薯雪花粉 — 测试','es':'Copos de patata — PRUEBA','ar':'رقائق البطاطس — اختبار','fr':'Flocons de pomme de terre — TEST','de':'Kartoffelflocken — TEST'}
 steps=['Raw Potato Receiving','Washing','Peeling','Cooking','Mashing','Drum Drying','Flaking','Inspection','Packaging']
 trs=[{'language_code':lang,'translation_status':'approved','product_name':name,'raw_material_name':'Potato — TEST','raw_material_origin':'TEST source only','package_description':'Controlled test packaging','storage_conditions':'TEST storage instructions','manufacturer_name':'T11 TEST organization — not a commercial claim','process_labels':{f's{i+1}':step for i,step in enumerate(steps)}} for lang,name in names.items()]
 pid=ok('passport-products',{'product_code':'PF-T11-TEST','content':{'source_language':'en','package_quantity':'25','package_unit':'kg','process_steps':[{'step_key':f's{i+1}'} for i in range(9)]},'translations':trs},token='editor')['id']
 rev=ok('passport-products/'+pid)['revisions'][0];ok(f'passport-products/{pid}/revisions/{rev["id"]}/seal',{'expected_token':rev['token']},token='editor');ok(f'passport-products/{pid}/default-revision',{'revision_id':rev['id'],'expected_current_revision_id':None},'PUT','editor')
 out={'product':pid,'revisions':{}}
 for key,code in [('chain','PF-T11-TEST-001'),('preview','PF-T11-TEST-PREVIEW')]:
  b=batch(pid,code);edit(b,25);asset(b)
  for i,(kind,content) in enumerate([('text',{'text':'T11 controlled plain text. This is not a commercial shipment.'}),('key_value',{'items':[{'key':'note','label':'Handling TEST','value':'Example only'}]}),('table',{'columns':[{'key':'item','label':'Item TEST'},{'key':'result','label':'Result TEST'}],'rows':[{'cells':['Fixture','Not a commercial claim']}]} )]):
   section=sample('custom'+str(i));section.update(section_type=kind,is_public=True,status='ready');section['translations'][0].update(translation_status='approved',title='T11 '+kind,content=content);sp='passport-batches/'+b+'/sections';ok(sp,{'expected_token':ok(sp)['token'],'section':section},token='editor')
  out[key]={'id':b,'code':code};out['revisions'][key]=[sealpub(b)]
 out['unpublished']=batch(pid,'PF-T11-TEST-DRAFT')
 b=out['preview']['id'];reopen(b);edit(b,22);rid=submit(b);assert decision(b).get('code')==200;out['review_id']=rid
 ok('passport-batches/'+b+'/review/return',{'review_id':rid,'reason':'T11 controlled three-source isolation fixture'},token='editor');edit(b,20)
 (rt/'test-artifacts/fixtures.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
 print('Fresh DB real Product/Revision/Batch/Review/Publish V1 fixtures created')
def advance():
 auth();p=rt/'test-artifacts/fixtures.json';f=json.loads(p.read_text());b=f['chain']['id'];reopen(b);edit(b,20);f['revisions']['chain'].append(sealpub(b));p.write_text(json.dumps(f,ensure_ascii=False,indent=2));print('V2 published')
def rollback():
 auth();p=rt/'test-artifacts/fixtures.json';f=json.loads(p.read_text());b=f['chain']['id'];vs=f['revisions']['chain'];r=ok('passport-batches/'+b+'/publication/rollback',{'target_revision_id':vs[0]['revision']['id'],'expected_current_revision_id':vs[-1]['revision']['id'],'idempotency_key':str(uuid.uuid4()),'rollback_reason':'T11 restore verified test V1'});assert r['record']['publish_status']=='published',r;vs.append(r);p.write_text(json.dumps(f,ensure_ascii=False,indent=2));print('Rollback V3 published')
if __name__=='__main__':globals()[sys.argv[1] if len(sys.argv)>1 else 'create']()
