"""Generate the T3 SQLite DDL, not application CRUD. Review generated SQL before use."""
from pathlib import Path
import re,json
R=Path(__file__).resolve().parents[2]
s=(R/'docs/DATA_MODEL.md').read_text();spl=re.split(r'### 2\.\d+ `([^`]+)`\n',s)[1:];tables={}
for i in range(0,len(spl),2):
 name,body=spl[i:i+2];fields=[]
 for l in body.split('## 3.')[0].splitlines():
  if l.startswith('| '):
   row=[v.strip() for v in l.split('|')[1:-1]]
   if len(row)==5 and row[0] not in ['字段','---']:fields.append(row)
 tables[name]=fields
assert len(tables)==19
q=lambda x:'"'+x+'"'
quote=lambda x:"'"+x.replace("'","''")+"'"
check=lambda x:'CHECK ('+x+')'
enums={
 ('products','lifecycle_status'):['active','disabled','archived'],('product_revisions','revision_status'):['draft','sealed','abandoned'],('batches','record_type'):['test','commercial'],('batches','quality_status'):['pending','released','hold','rejected'],('batches','workflow_status'):['draft','pending_review','published','archived'],('batch_overrides','value_kind'):['text','decimal','integer','json','asset'],('batch_overrides','operation'):['set','clear'],('inspection_items','value_type'):['decimal','integer','text','none'],('inspection_items','judgement'):['pass','fail','not_tested','not_applicable','pending','informational'],('certifications','status'):['unverified','valid','expired','suspended','revoked'],('certification_links','operation'):['include','exclude'],('media_assets','availability_status'):['ready','disabled','purged'],('custom_sections','operation'):['add','replace','hide','inherit'],('custom_sections','section_type'):['text','key_value','table','asset_gallery'],('custom_sections','status'):['draft','ready','disabled'],('publish_records','operation_type'):['publish','rollback'],('publish_records','publish_status'):['pending','building','validating','prepared','switching','published','failed','recovery_required']}
roles=['product_image','certificate','inspection_report','section_image','attachment'];mimes=['image/jpeg','image/png','image/webp','application/pdf'];langs=['en','zh-CN','es','ar','fr','de']
over={**{k:'text' for k in ['raw_material_name','raw_material_type','raw_material_origin','raw_material_description','package_description','inner_material','package_unit','package_type_code','storage_conditions','shelf_life_description']},'package_quantity':'decimal','shelf_life_days':'integer','process':'json','product_image_asset':'asset'}
events=['batch_created','batch_cloned','batch_edited','override_set','override_cleared','review_submitted','review_approved','review_rejected','publish_requested','publish_succeeded','publish_failed','rollback_requested','rollback_succeeded','archived','media_replaced','inspection_changed','certification_linked','product_revision_sealed']
# Explicit relations (not inferred from generic entity_id strings).
fk={
'products':{'current_revision_id':'product_revisions'},'product_revisions':{'product_id':'products','source_revision_id':'product_revisions'},
'product_revision_translations':{'product_revision_id':'product_revisions'},'batches':{'product_id':'products','base_product_revision_id':'product_revisions','current_passport_revision_id':'passport_revisions','active_publish_record_id':'publish_records','cloned_from_batch_id':'batches'},
'batch_overrides':{'batch_id':'batches','value_media_asset_id':'media_assets'},'batch_override_translations':{'batch_override_id':'batch_overrides'},'inspection_items':{'batch_id':'batches'},'inspection_item_translations':{'inspection_item_id':'inspection_items'},'certifications':{'supersedes_id':'certifications'},'certification_translations':{'certification_id':'certifications'},'certification_links':{'product_revision_id':'product_revisions','batch_id':'batches','certification_id':'certifications'},'media_assets':{'replaces_media_asset_id':'media_assets'},'asset_links':{'product_revision_id':'product_revisions','certification_id':'certifications','inspection_item_id':'inspection_items','custom_section_id':'custom_sections','media_asset_id':'media_assets'},'custom_sections':{'product_revision_id':'product_revisions','batch_id':'batches'},'custom_section_translations':{'custom_section_id':'custom_sections'},'passport_revisions':{'batch_id':'batches','base_product_revision_id':'product_revisions','source_revision_id':'passport_revisions','rollback_source_revision_id':'passport_revisions'},'published_assets':{'passport_revision_id':'passport_revisions','source_media_asset_id':'media_assets'},'publish_records':{'batch_id':'batches','passport_revision_id':'passport_revisions','expected_current_revision_id':'passport_revisions'},'passport_audit_events':{'batch_id':'batches','passport_revision_id':'passport_revisions'}}
extra={t:[] for t in tables};indexes=[]
def unique(t,*cols,where=None):
 indexes.append('CREATE UNIQUE INDEX '+q('uq_'+t+'_'+'_'.join(cols))+ ' ON '+q(t)+' ('+','.join(map(q,cols))+')'+(' WHERE '+where if where else '')+';')
def idx(t,*cols):indexes.append('CREATE INDEX '+q('ix_'+t+'_'+'_'.join(cols))+' ON '+q(t)+' ('+','.join(map(q,cols))+');')
def foreign(t,cols,target,targetcols):extra[t].append('FOREIGN KEY ('+','.join(map(q,cols))+') REFERENCES '+q(target)+' ('+','.join(map(q,targetcols))+') ON UPDATE RESTRICT ON DELETE RESTRICT')
for t,cols in [('products',['product_code']),('products',['id','product_code']),('product_revisions',['product_id','revision_number']),('product_revisions',['product_id','id']),('batches',['batch_code']),('batches',['id','product_id']),('batches',['id','base_product_revision_id']),('batch_overrides',['batch_id','field_key']),('inspection_items',['batch_id','item_code']),('certifications',['family_key','revision_number']),('media_assets',['storage_key']),('passport_revisions',['batch_id','version_number']),('passport_revisions',['batch_id','id']),('passport_revisions',['release_identifier']),('passport_revisions',['id','release_identifier']),('published_assets',['passport_revision_id','asset_key']),('publish_records',['passport_revision_id']),('publish_records',['batch_id','id']),('publish_records',['batch_id','idempotency_key']),('publish_records',['release_identifier'])]:unique(t,*cols)
for t in tables:
 if t.endswith('_translations'):
  parent=[f[0] for f in tables[t] if f[0].endswith('_id')][0];unique(t,parent,'language_code')
for t in ['custom_sections','certification_links']:
 for owner in ['product_revision_id','batch_id']:unique(t,owner,'section_key' if t=='custom_sections' else 'link_key',where=q(owner)+' IS NOT NULL')
 extra[t].append(check('(product_revision_id IS NOT NULL)+(batch_id IS NOT NULL)=1'))
for owner in ['product_revision_id','certification_id','inspection_item_id','custom_section_id']:unique('asset_links',owner,'asset_key',where=q(owner)+' IS NOT NULL')
unique('asset_links','product_revision_id','asset_role',where="product_revision_id IS NOT NULL AND asset_role='product_image'")
extra['asset_links'].append(check('(product_revision_id IS NOT NULL)+(certification_id IS NOT NULL)+(inspection_item_id IS NOT NULL)+(custom_section_id IS NOT NULL)=1'))
unique('publish_records','batch_id',where="publish_status IN ('pending','building','validating','prepared','switching','recovery_required')")
foreign('products',['id','current_revision_id'],'product_revisions',['product_id','id'])
foreign('batches',['product_id','base_product_revision_id'],'product_revisions',['product_id','id'])
for col,target in [('current_passport_revision_id','passport_revisions'),('active_publish_record_id','publish_records')]:foreign('batches',['id',col],target,['batch_id','id'])
foreign('passport_revisions',['batch_id','base_product_revision_id'],'batches',['id','base_product_revision_id'])
for col in ['source_revision_id','rollback_source_revision_id']:foreign('passport_revisions',['batch_id',col],'passport_revisions',['batch_id','id'])
foreign('publish_records',['batch_id','passport_revision_id'],'passport_revisions',['batch_id','id'])
foreign('publish_records',['batch_id','expected_current_revision_id'],'passport_revisions',['batch_id','id'])
foreign('publish_records',['passport_revision_id','release_identifier'],'passport_revisions',['id','release_identifier'])
foreign('passport_audit_events',['batch_id','passport_revision_id'],'passport_revisions',['batch_id','id'])
extra['passport_audit_events'].append(check('passport_revision_id IS NULL OR batch_id IS NOT NULL'))
extra['batch_overrides'] += [check(' OR '.join('(field_key='+quote(k)+' AND value_kind='+quote(v)+')' for k,v in over.items())),check("(operation='clear' AND value_text IS NULL AND value_integer IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (operation='set' AND ((value_kind IN ('text','decimal') AND value_text IS NOT NULL AND value_integer IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='integer' AND value_integer IS NOT NULL AND value_text IS NULL AND value_json IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='json' AND value_json IS NOT NULL AND value_text IS NULL AND value_integer IS NULL AND value_media_asset_id IS NULL AND public_asset_label IS NULL) OR (value_kind='asset' AND value_media_asset_id IS NOT NULL AND public_asset_label IS NOT NULL AND value_text IS NULL AND value_integer IS NULL AND value_json IS NULL)))")]
extra['batch_override_translations'].append(check('(translated_value IS NOT NULL)+(translated_process IS NOT NULL)=1'))
extra['inspection_items'] += [check("(value_type IN ('decimal','integer') AND text_value IS NULL) OR (value_type='text' AND numeric_value IS NULL) OR (value_type='none' AND numeric_value IS NULL AND text_value IS NULL)"),check("judgement NOT IN ('not_tested','not_applicable') OR (numeric_value IS NULL AND text_value IS NULL)"),check("judgement NOT IN ('pass','fail','informational') OR numeric_value IS NOT NULL OR COALESCE(length(text_value),0)>0")]
extra['certification_links'].append(check("(operation='include' AND certification_id IS NOT NULL) OR (operation='exclude' AND batch_id IS NOT NULL AND certification_id IS NULL)"))
extra['custom_sections'] += [check("product_revision_id IS NULL OR operation='add'"),check("operation NOT IN ('add','replace') OR sort_order IS NOT NULL"),check("operation!='hide' OR is_visible=0")]
extra['batches'] += [check('expiry_date IS NULL OR production_date IS NULL OR expiry_date>=production_date'),check("workflow_status!='published' OR current_passport_revision_id IS NOT NULL")]
extra['certifications'].append(check('valid_from IS NULL OR valid_until IS NULL OR valid_from<=valid_until'))
extra['product_revisions'].append(check("revision_status!='sealed' OR (sealed_at IS NOT NULL AND sealed_by IS NOT NULL AND content_hash IS NOT NULL)"))
extra['passport_revisions'] += [check('sealed_at IS NULL OR (payload IS NOT NULL AND payload_hash IS NOT NULL AND content_hash IS NOT NULL AND snapshot_path IS NOT NULL AND asset_manifest_hash IS NOT NULL)'),check('published_at IS NULL OR sealed_at IS NOT NULL')]
extra['publish_records'].append(check("publish_status NOT IN ('published','failed') OR completed_at IS NOT NULL"))
out=['-- T4 minimal business schema, generated from approved T3 field dictionary.\n-- No seed data, CRUD, or publish engine. Run via versioned Go Admin migration.\n']
for t,fields in tables.items():
 defs=[]
 for name,typ,nullable,default,meaning in fields:
  sqltype='INTEGER' if typ in ['INT','BOOL','USER'] else 'TEXT'
  col=q(name);d=col+' '+sqltype+(' NOT NULL' if nullable=='否' else '')+(' PRIMARY KEY' if name=='id' else '')
  if default in ['0','1']:d+=' DEFAULT '+default
  elif default in ['true','false']:d+=' DEFAULT '+('1' if default=='true' else '0')
  elif default in ['[]','{}']:d+=' DEFAULT '+quote(default)
  elif default not in ['无','NULL'] and re.fullmatch('[a-z][a-z_-]*|OTHER',default):d+=' DEFAULT '+quote(default)
  if typ=='BOOL':d+=' '+check(col+' IN(0,1)')
  if typ=='INT':d+=' '+check(col+('>0' if name in ['version_number','revision_number','next_version_number','edit_version','state_version','file_size'] else '>=0'))
  if typ=='HASH':d+=' '+check('length('+col+')=64 AND '+col+" NOT GLOB '*[^0-9a-f]*'")
  if typ=='ID':d+=' '+check('length('+col+")=36 AND substr("+col+",15,1)='4' AND substr("+col+",20,1) IN ('8','9','a','b') AND "+col+" NOT GLOB '*[^0-9a-f-]*'")
  if typ=='CODE':d+=' '+check('length('+col+') BETWEEN 1 AND 64 AND '+col+" NOT GLOB '*[^A-Za-z0-9_-]*'")
  if name in ['product_code','batch_code']:d+=' '+check(col+'=upper('+col+')')
  if typ.startswith('TEXT('):d+=' '+check('length('+col+')<='+typ[5:-1])
  if typ=='JSON' or name=='payload':d+=' '+check('json_valid('+col+')')
  if typ=='DATE':d+=' '+check('length('+col+")=10 AND "+col+" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date("+col+") IS "+col)
  if typ=='UTC':d+=' '+check(col+' IS NULL OR (length('+col+")=24 AND substr("+col+",24,1)='Z' AND julianday("+col+') IS NOT NULL)')
  if typ=='PATH':d+=' '+check("length("+col+")>0 AND substr("+col+",1,1)!='/' AND instr("+col+",'..')=0 AND instr("+col+",char(92))=0 AND instr("+col+",':')=0")
  enumvals=enums.get((t,name))
  if typ=='LANG':enumvals=langs
  if name=='translation_status':enumvals=['draft','approved']
  if name=='mime_type':enumvals=mimes
  if name=='asset_role':enumvals=roles
  if name=='event_type':enumvals=events
  if name=='entity_type':enumvals=list(tables)
  if enumvals:d+=' '+check(col+' IN ('+','.join(map(quote,enumvals))+')')
  if typ=='USER':fk[t][name]='sys_user'
  defs.append(d)
 for col,target in fk[t].items():foreign(t,[col],target,['user_id' if target=='sys_user' else 'id']);idx(t,col)
 defs+=extra[t];out.append('CREATE TABLE '+q(t)+' (\n  '+',\n  '.join(defs)+'\n);')
for t,cols in [('products',['lifecycle_status','updated_at']),('product_revisions',['product_id','revision_status','revision_number']),('batches',['product_id','created_at']),('batches',['workflow_status','submitted_at']),('inspection_items',['batch_id','sort_order','item_code']),('passport_revisions',['published_at']),('publish_records',['publish_status','updated_at']),('passport_audit_events',['batch_id','created_at','id']),('passport_audit_events',['entity_type','entity_id','created_at']),('published_assets',['published_path']),('published_assets',['sha256'])]:idx(t,*cols)
out+=list(dict.fromkeys(indexes))
# Freeze and relationship triggers. All reject Raw SQL, independently of ORM hooks.
triggers=[]
def trig(name,t,op,condition,msg):triggers.append(f'CREATE TRIGGER "{name}" BEFORE {op} ON "{t}" WHEN {condition} BEGIN SELECT RAISE(ABORT,{quote(msg)}); END;')
def frozen(t,cond):
 for op in ['UPDATE','DELETE']:trig('freeze_'+t+'_'+op.lower(),t,op,cond,t+' frozen')
frozen('product_revisions',"OLD.revision_status IN ('sealed','abandoned')")
frozen('certifications','OLD.sealed_at IS NOT NULL')
frozen('passport_audit_events','1')
frozen('publish_records',"OLD.publish_status IN ('published','failed')")
# Immutable columns, allowing only narrowly defined publication confirmation.
prcols=[f[0] for f in tables['passport_revisions'] if f[0]!='published_at']
trig('passport_sealed_update','passport_revisions','UPDATE','OLD.published_at IS NOT NULL OR (OLD.sealed_at IS NOT NULL AND ('+' OR '.join('NEW.'+q(c)+' IS NOT OLD.'+q(c) for c in prcols)+'))','passport revision frozen')
trig('passport_no_delete','passport_revisions','DELETE','OLD.sealed_at IS NOT NULL OR OLD.published_at IS NOT NULL','passport revision frozen')
trig('passport_publish_once','passport_revisions','UPDATE',"NEW.published_at IS NOT OLD.published_at AND (OLD.published_at IS NOT NULL OR NEW.published_at IS NULL OR NOT EXISTS(SELECT 1 FROM publish_records r JOIN batches b ON b.active_publish_record_id=r.id WHERE r.passport_revision_id=OLD.id AND r.publish_status IN ('switching','recovery_required')))",'publication requires active switching record')
trig('passport_insert_unpublished','passport_revisions','INSERT','NEW.published_at IS NOT NULL','prepare before publish')
for t,cols in [('products',['id','product_code']),('batches',['id','batch_code','product_id','base_product_revision_id','record_type']),('product_revisions',['id','product_id','revision_number']),('media_assets',[f[0] for f in tables['media_assets'] if f[0] not in ['availability_status','purged_at']])]:
 trig(t+'_identity',t,'UPDATE',' OR '.join('NEW.'+q(c)+' IS NOT OLD.'+q(c) for c in cols),'identity or bytes immutable')
for op in ['INSERT','UPDATE']:
 trig('batch_sealed_base_'+op,'batches',op,"NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.base_product_revision_id AND p.product_id=NEW.product_id AND p.revision_status='sealed')",'batch requires sealed matching template')
 trig('product_current_'+op,'products',op,"NEW.current_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM product_revisions p WHERE p.id=NEW.current_revision_id AND p.product_id=NEW.id AND p.revision_status='sealed')",'current template must be sealed')
 trig('batch_current_'+op,'batches',op,'NEW.current_passport_revision_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id=NEW.current_passport_revision_id AND p.batch_id=NEW.id AND p.published_at IS NOT NULL)','current passport must be published')
 trig('cert_link_sealed_'+op,'certification_links',op,"NEW.operation='include' AND NOT EXISTS(SELECT 1 FROM certifications c WHERE c.id=NEW.certification_id AND c.sealed_at IS NOT NULL)",'certification must be sealed')
 for t,source,scope,no,published in [('product_revisions','source_revision_id','product_id','revision_number',False),('certifications','supersedes_id','family_key','revision_number',False),('passport_revisions','source_revision_id','batch_id','version_number',True),('passport_revisions','rollback_source_revision_id','batch_id','version_number',True)]:
  cond='NEW.'+source+' IS NOT NULL AND NOT EXISTS(SELECT 1 FROM '+t+' s WHERE s.id=NEW.'+source+' AND s.'+scope+'=NEW.'+scope+' AND s.'+no+'<NEW.'+no+(' AND s.published_at IS NOT NULL' if published else '')+')'
  trig(t+'_'+source+'_'+op,t,op,cond,'invalid revision source')
# Parent resolver queries for freezing and aggregate edit tracking.
batch_queries={
'batch_overrides':'SELECT batch_id FROM batches_dummy', # replaced below
'inspection_items':'SELECT {r}.batch_id',
'certification_links':'SELECT {r}.batch_id',
'custom_sections':'SELECT {r}.batch_id',
'batch_override_translations':'SELECT batch_id FROM batch_overrides WHERE id={r}.batch_override_id',
'inspection_item_translations':'SELECT batch_id FROM inspection_items WHERE id={r}.inspection_item_id',
'custom_section_translations':'SELECT batch_id FROM custom_sections WHERE id={r}.custom_section_id',
'asset_links':'SELECT batch_id FROM inspection_items WHERE id={r}.inspection_item_id UNION SELECT batch_id FROM custom_sections WHERE id={r}.custom_section_id'}
batch_queries['batch_overrides']='SELECT {r}.batch_id'
prod_queries={'product_revision_translations':'SELECT {r}.product_revision_id','custom_sections':'SELECT {r}.product_revision_id','certification_links':'SELECT {r}.product_revision_id','custom_section_translations':'SELECT product_revision_id FROM custom_sections WHERE id={r}.custom_section_id','asset_links':'SELECT {r}.product_revision_id UNION SELECT product_revision_id FROM custom_sections WHERE id={r}.custom_section_id'}
cert_queries={'certification_translations':'SELECT {r}.certification_id','asset_links':'SELECT {r}.certification_id'}
for t in sorted(set(batch_queries)|set(prod_queries)|set(cert_queries)|{'published_assets'}):
 for op in ['INSERT','UPDATE','DELETE']:
  refs=['NEW'] if op=='INSERT' else ['OLD'] if op=='DELETE' else ['OLD','NEW'];conditions=[]
  for row in refs:
   if t in batch_queries:conditions.append("EXISTS(SELECT 1 FROM batches b WHERE b.id IN ("+batch_queries[t].format(r=row)+") AND (b.workflow_status!='draft' OR b.active_publish_record_id IS NOT NULL))")
   if t in prod_queries:conditions.append("EXISTS(SELECT 1 FROM product_revisions p WHERE p.id IN ("+prod_queries[t].format(r=row)+") AND p.revision_status!='draft')")
   if t in cert_queries:conditions.append('EXISTS(SELECT 1 FROM certifications c WHERE c.id IN ('+cert_queries[t].format(r=row)+') AND c.sealed_at IS NOT NULL)')
   if t=='published_assets':conditions.append('EXISTS(SELECT 1 FROM passport_revisions p WHERE p.id='+row+'.passport_revision_id AND p.sealed_at IS NOT NULL)')
  trig('parent_freeze_'+t+'_'+op,t,op,' OR '.join(conditions),'parent frozen')
  if t in batch_queries:
   row='OLD' if op=='DELETE' else 'NEW';triggers.append('CREATE TRIGGER "bump_'+t+'_'+op+'" AFTER '+op+' ON '+q(t)+' BEGIN UPDATE batches SET edit_version=edit_version+1 WHERE id IN ('+batch_queries[t].format(r=row)+'); END;')
 # owner cannot change even while draft; copy explicitly.
 owners=[c for c in fk[t] if c in ['batch_id','product_revision_id','certification_id','inspection_item_id','custom_section_id','batch_override_id','passport_revision_id']]
 if owners:trig('owner_fixed_'+t,t,'UPDATE',' OR '.join('NEW.'+q(c)+' IS NOT OLD.'+q(c) for c in owners),'owner immutable')
# Batch working fields freeze; control/confirmation metadata remain system-controlled.
working=['production_date','expiry_date','quality_status','internal_note']
trig('batch_work_freeze','batches','UPDATE',"(OLD.workflow_status!='draft' OR OLD.active_publish_record_id IS NOT NULL) AND ("+' OR '.join('NEW.'+c+' IS NOT OLD.'+c for c in working)+')','batch working data frozen')
trig('batch_active_workflow','batches','UPDATE',"OLD.active_publish_record_id IS NOT NULL AND NEW.workflow_status IS NOT OLD.workflow_status AND NOT (NEW.workflow_status='published' AND EXISTS(SELECT 1 FROM publish_records r WHERE r.id=OLD.active_publish_record_id AND r.publish_status='published'))",'unresolved publish')
trig('product_seal_translation','product_revisions','UPDATE',"NEW.revision_status='sealed' AND OLD.revision_status='draft' AND NOT EXISTS(SELECT 1 FROM product_revision_translations t WHERE t.product_revision_id=NEW.id AND t.language_code=NEW.source_language AND t.translation_status='approved' AND length(t.product_name)>0)",'approved source translation required')
# Prevent deleting any history of a Batch. Draft children may be deleted explicitly.
trig('batch_history_delete','batches','DELETE','EXISTS(SELECT 1 FROM passport_revisions p WHERE p.batch_id=OLD.id)','batch history retained')
# Complete SQL and reviewable metadata.
out+=triggers
path=R/'runtime/t4/schema-candidate.sql';path.write_text('\n\n'.join(out)+'\n')
(R/'admin/t4/schema_catalog.json').write_text(json.dumps({'tables':{t:[f[0] for f in fs] for t,fs in tables.items()},'enums':{t+'.'+c:v for (t,c),v in enums.items()},'override_fields':over,'version':'1788739201000'},indent=2))
print('Generated',len(tables),'tables and',len(triggers),'triggers')
