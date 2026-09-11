from verify_api import *
import helpers as h
h.admin=login(cred['admin_username'],cred['admin_password']);users.update(json.loads((rt/'test-artifacts/users.json').read_text()))
for role in ['editor','reviewer']:tokens[role]=login(users[role]['username'],cred['test_password'])
try:
 tr=[]
 for lang in ['en','fr','ar','es','zh-CN','de']:tr.append({'language_code':lang,'translation_status':'draft' if lang=='de' else 'approved','product_name':'PRIVATE GERMAN DRAFT' if lang=='de' else 'TEST '+lang+' 测试 العربية','raw_material_name':'TEST Ingredient','package_description':'BASE DO NOT FALL BACK','process_labels':{'mix':'TEST Mix '+lang,'pack':'TEST Pack '+lang}})
 p=ok('passport-products',{'product_code':'TEST-T9-RICH-'+runid,'content':{'source_language':'en','package_quantity':'25.000','package_unit':'kg','process_steps':[{'step_key':'mix'},{'step_key':'pack'}]},'translations':tr},token='editor')['id'];rev=ok('passport-products/'+p)['revisions'][0];ok(f'passport-products/{p}/revisions/{rev["id"]}/seal',{'expected_token':rev['token']},token='editor');ok(f'passport-products/{p}/default-revision',{'revision_id':rev['id'],'expected_current_revision_id':None},'PUT','editor')
 b=batch(p,'TEST-T9-RICH-'+runid);w=work(b);w['overrides']=[{'field_key':'package_description','operation':'clear'}];w['inspections']=[{'item_code':'TEST_NUMERIC','name':'TEST Weight','value_type':'decimal','numeric_value':'1.2500','unit':'kg','min_limit':'1.00','max_limit':'2.000','min_inclusive':True,'max_inclusive':True,'judgement':'pass','sort_order':1,'is_public':True,'tested_on':'2026-09-10'},{'item_code':'TEST_TEXT','name':'TEST Visual','value_type':'text','text_value':'TEST Acceptable','min_inclusive':True,'max_inclusive':True,'judgement':'informational','sort_order':2,'is_public':True}];ok('passport-batches/'+b,w,'PUT','editor')
 contents={'text':{'text':'TEST plain text'},'key_value':{'items':[{'key':'test','label':'TEST Label','value':'TEST Value'}]},'table':{'columns':[{'key':'test','label':'TEST Column'}],'rows':[{'cells':['TEST cell']}]}}
 for index,(kind,content) in enumerate(contents.items()):
  s=sample('rich_'+kind);s.update(section_type=kind,is_public=True,status='ready',sort_order=index);s['translations']=[{'language_code':lang,'translation_status':'approved','title':'TEST '+kind+' '+lang,'content':content} for lang in ['en','ar']];sp='passport-batches/'+b+'/sections';ok(sp,{'expected_token':ok(sp)['token'],'section':s},token='editor')
 s=sample('hidden');s.update(is_public=True,is_visible=False,status='ready');s['translations'][0]['translation_status']='approved';s['translations'][0]['content']={'text':'PRIVATE HIDDEN MODULE'};sp='passport-batches/'+b+'/sections';ok(sp,{'expected_token':ok(sp)['token'],'section':s},token='editor')
 submit(b);check('Rich reviewer approve',decision(b).get('code')==200);r=publish(b);check('Rich public publish succeeds',r.get('code')==200 and r['data']['record']['publish_status']=='published');raw=(rt/'publish'/r['data']['revision']['snapshot_path']).read_bytes();out=json.loads(raw)
 check('Exact numeric decimals normalized',out['inspection'][0]['numeric_value']=='1.25' and out['inspection'][0]['min_limit']=='1' and out['inspection'][0]['max_limit']=='2' and out['packaging']['quantity']=='25')
 check('Inspection source ordering stable',[x['code'] for x in out['inspection']]==['TEST_NUMERIC','TEST_TEXT'])
 check('Three structured public modules valid',[x['type'] for x in out['custom_sections']]==['text','key_value','table'])
 check('Hidden section omitted',b'PRIVATE HIDDEN MODULE' not in raw)
 check('Draft language excluded',b'PRIVATE GERMAN DRAFT' not in raw and out['localization']['available_languages']==['en','ar','es','fr','zh-CN'])
 check('Clear applies to all approved languages',out['packaging']['description'] is None and all(t['packaging']['description'] is None for t in out['localization']['translations']))
 check('Unicode preserved', 'العربية'.encode() in raw and '测试'.encode() in raw)
 check('Business JSON no UUID leakage',str(b).encode() not in raw and str(p).encode() not in raw)
 (rt/'test-artifacts/rich-fixture.json').write_text(json.dumps({'batch_id':b,'revision':r['data']['revision']},indent=2))
finally:(rt/'test-artifacts/rich.json').write_text(json.dumps(checks,indent=2))
