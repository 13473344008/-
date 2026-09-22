import {validatePayload,assetPath} from './schema.mjs';
import {languages,label,displayValue} from './i18n.mjs';
const inlineFieldLabels={raw_material_origin:['原料来源说明','Raw material origin'],raw_material_description:['原料描述','Raw material description'],package_description:['包装说明','Packaging description'],storage_conditions:['储存条件','Storage conditions']};
const present=v=>v!==null&&v!==undefined&&v!=='';
export function localized(payload,language){
 const p=JSON.parse(JSON.stringify(payload));
 const tr=p.localization.translations.find(t=>t.language_code===language);if(!tr)return p;
 for(const group of ['product','raw_material','packaging','storage','manufacturer'])if(tr[group])Object.assign(p[group],tr[group]);
 for(const [group,key] of [['process','step_key'],['inspection','code'],['certifications','key'],['custom_sections','key']]){
  for(const item of p[group]){const t=tr[group]?.find(x=>x[key]===item[key]);if(t){if(group==='custom_sections'&&t.type!==item.type)throw Error('invalid_payload');Object.assign(item,t);}}
 }
 return p; // Own null is a deliberate clear. Only absent translation fields fall back.
}
function el(tag,text,cls){const n=document.createElement(tag);if(present(text))n.textContent=String(text);if(cls)n.className=cls;return n;}
export function renderPassport(container,payload,options={}){
 validatePayload(payload);const language=languages.includes(options.language)?options.language:'en';const p=localized(payload,language),t=k=>label(k,language);
 container.replaceChildren();container.classList.add('passport');container.lang=language;container.dir=language==='ar'?'rtl':'ltr';container.removeAttribute('aria-busy');
 const privatePreview=['working','review'].includes(options.previewKind);
 if(privatePreview)container.append(el('p',t(options.previewKind==='working'?'working_notice':'review_notice'),'preview-notice'));
 if(p.notice)container.append(el('p',p.record_type==='test'?t('test_notice'):p.notice,'test-notice'));
 function image(a,eager=false){const f=el('figure'),box=el('div',null,'image-box'),im=el('img');
  let src=assetPath(a);
  if(privatePreview){const b64=options.privateAssets?.[a.key];if(typeof b64!=='string'||!/^[A-Za-z0-9+/]+={0,2}$/.test(b64)){box.append(el('span',t('missing_image'),'asset-unavailable'));f.append(box);return f;}const mime=options.privateAssetMimeTypes?.[a.key]??'image/png';if(!['image/png','image/jpeg'].includes(mime))throw Error('invalid_preview_image');src='data:'+mime+';base64,'+b64;}
  im.alt=a.label||t('assets');im.loading=eager?'eager':'lazy';im.decoding='async';im.width=640;im.height=480;
  im.addEventListener('error',()=>box.replaceChildren(el('span',t('missing_image'),'asset-unavailable')),{once:true});im.src=src;box.append(im);f.append(box);if(present(a.label)&&!inlineFieldLabels[a.display_target]?.includes(a.label.trim()))f.append(el('figcaption',a.label));return f;
 }
 const shown=new Set();
 function pictures(target){return p.assets.filter(a=>a.display_target===target);}
 function appendPictures(parent,target){for(const a of pictures(target)){parent.append(image(a));shown.add(a.key);}}
 const hero=el('section',null,'hero'),intro=el('div');intro.append(el('p',t('identity'),'eyebrow'),el('h1',p.product.name),el('span',p.batch.code,'badge technical'));hero.append(intro);
 const first=p.assets.find(a=>a.role==='product_image'&&!a.display_target);if(first){hero.append(image(first,true));shown.add(first.key);}container.append(hero);
 const grid=el('div',null,'grid');container.append(grid);
 function card(title,key,wide=false){const n=el('section',null,'card'+(wide?' wide':''));n.dataset.module=key;const heading=el('h2',title);n.append(heading);grid.append(n);return n;}
 function fields(parent,object,omit=[],group=''){const dl=el('dl',null,'fields');const order=({product:['name','code','category_code','country_of_origin'],batch:['code','quality_status','production_date','expiry_date'],raw_material:['name','type','origin','description'],packaging:['quantity','type_code','unit','description','inner_material'],manufacturer:['name','address']})[group]??Object.keys(object);for(const [k,v]of Object.entries(object).sort((a,b)=>order.indexOf(a[0])-order.indexOf(b[0]))){const target=({raw_material:{origin:'raw_material_origin',description:'raw_material_description'},packaging:{description:'package_description'},storage:{conditions:'storage_conditions'}})[group]?.[k];if(omit.includes(k)||((!present(v)||typeof v==='object'||typeof v==='boolean')&&(!target||!pictures(target).length)))continue;const f=el('div',null,'field');f.dataset.field=k;if(k==='quality_status')f.dataset.status=v;f.append(el('dt',t(group==='raw_material'?'raw_material_'+k:k)),el('dd',typeof v==='string'&&['pass','fail','pending','not_tested','not_applicable','informational'].includes(v)?t(v):displayValue(k,v,language),/(code|date|number|value|limit|hash|unit|size|weight|quantity|version)/.test(k)?'technical':undefined));if(['description','origin','conditions','inner_material','shelf_life_description','address'].includes(k))f.classList.add('field-long');if(target&&pictures(target).length){f.classList.add('field-long','field-with-images');const photos=el('div',null,'field-pictures');appendPictures(photos,target);f.append(photos);}dl.append(f);}if(dl.childNodes.length)parent.append(dl);}
 for(const k of ['product','batch','raw_material'])if(Object.values(p[k]).some(present)||p.assets.some(a=>({raw_material:['raw_material_origin','raw_material_description'],packaging:['package_description'],storage:['storage_conditions']})[k]?.includes(a.display_target))){const c=card(t(k),k,['raw_material','packaging','storage','manufacturer'].includes(k));fields(c,p[k],k==='product'?['category_code','code']:[],k);}
 if(p.process.length){
  const c=card(t('process'),'process',true),fold=el('details',null,'process-fold'),summary=el('summary');
  summary.append(el('span',t('process_expand')),el('span',p.process.length+' '+t('steps'),'step-count'));fold.append(summary);
  const ol=el('ol',null,'process');
  for(const s of p.process){const item=el('li'),photos=pictures('process:'+s.step_key);if(photos.length){const detail=el('details',null,'step-detail'),head=el('summary',s.label),body=el('div',null,'process-body');detail.append(head);appendPictures(body,'process:'+s.step_key);detail.append(body);item.append(detail);}else item.append(el('span',s.label));ol.append(item);}
  fold.append(ol);c.append(fold);
 }

 if(p.inspection.length){const c=card(t('inspection'),'inspection',true),items=el('div',null,'inspection-grid');for(const i of p.inspection){const n=el('article',null,'inspection-item');n.append(el('h3',i.name),el('span',t(i.judgement),'status status-'+i.judgement));fields(n,i,['name','judgement','value_type','text_value']);if(present(i.result_display_text??i.text_value))n.append(el('p',Object.hasOwn(i,'result_display_text')?i.result_display_text:i.text_value));items.append(n);}c.append(items);}
 if(p.certifications.length){const c=card(t('certifications'),'certifications',true);for(const cert of p.certifications)fields(c,cert);}
 for(const k of ['packaging','storage','manufacturer'])if(Object.values(p[k]).some(present)||p.assets.some(a=>({raw_material:['raw_material_origin','raw_material_description'],packaging:['package_description'],storage:['storage_conditions']})[k]?.includes(a.display_target))){const c=card(t(k),k,['raw_material','packaging','storage','manufacturer'].includes(k));fields(c,p[k],k==='product'?['category_code','code']:[],k);}
 for(const s of p.custom_sections){const c=card(s.title,'custom-'+s.type,true);
  if(s.type==='text')c.append(el('p',s.content.text,'custom-text'));
  if(s.type==='key_value'){const dl=el('dl',null,'fields');for(const i of s.content.items){const d=el('div',null,'field');d.append(el('dt',i.label),el('dd',i.value));dl.append(d);}c.append(dl);}
  if(s.type==='table'){c.dataset.columns=String(s.content.columns.length);const wrap=el('div',null,'table-scroll');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',s.title);const table=el('table'),head=el('thead'),tr=el('tr');table.append(el('caption',s.title));for(const col of s.content.columns){const th=el('th',col.label);th.scope='col';tr.append(th);}head.append(tr);table.append(head);const body=el('tbody');for(const row of s.content.rows){const r=el('tr');for(const val of row.cells)r.append(el('td',val));body.append(r);}table.append(body);wrap.append(table);c.append(wrap);}
  if(s.type==='asset_gallery'){c.append(el('p',s.content.caption));const gallery=el('div',null,'gallery');for(const key of s.asset_keys){const a=p.assets.find(x=>x.key===key);if(a){gallery.append(image(a));shown.add(a.key);}}c.append(gallery);}
 }
 if(p.assets.some(a=>!shown.has(a.key))){const c=card(t('assets'),'assets',true),gallery=el('div',null,'gallery');for(const a of p.assets)if(!shown.has(a.key))gallery.append(image(a));c.append(gallery);}
 return p;
}
export function renderError(container,code,retry,language='en'){const t=k=>label(k,language);container.replaceChildren();container.removeAttribute('aria-busy');const n=el('section',null,'state');n.setAttribute('role','alert');n.append(el('h1',t(code==='not_found'?'not_found':code==='unsupported_schema'?'unsupported_schema':'unavailable')));n.append(el('p',t('error_help')));if(retry){const b=el('button',t('retry'));b.type='button';b.addEventListener('click',retry);n.append(b);}container.append(n);}
