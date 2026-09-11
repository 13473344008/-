import {validatePayload,assetPath} from './schema.mjs';
import {languages,label} from './i18n.mjs';
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
 if(privatePreview)container.append(el('p',options.previewKind==='working'?'DRAFT / INTERNAL PREVIEW — NOT PUBLISHED':'REVIEW PREVIEW — NOT PUBLISHED','preview-notice'));
 if(p.notice)container.append(el('p',p.notice,'test-notice'));
 function image(a,eager=false){const f=el('figure'),box=el('div',null,'image-box'),im=el('img');
  let src=assetPath(a);
  if(privatePreview){const b64=options.privateAssets?.[a.key];if(typeof b64!=='string'||!/^[A-Za-z0-9+/]+={0,2}$/.test(b64)){box.append(el('span',t('missing_image'),'asset-unavailable'));f.append(box);return f;}src='data:image/png;base64,'+b64;}
  im.alt=a.label||t('assets');im.loading=eager?'eager':'lazy';im.decoding='async';im.width=640;im.height=480;
  im.addEventListener('error',()=>box.replaceChildren(el('span',t('missing_image'),'asset-unavailable')),{once:true});im.src=src;box.append(im);f.append(box,el('figcaption',a.label));return f;
 }
 const hero=el('section',null,'hero'),intro=el('div');intro.append(el('p','PRODUCT DIGITAL IDENTITY','eyebrow'),el('h1',p.product.name),el('span',p.batch.code,'badge technical'));hero.append(intro);
 const first=p.assets.find(a=>a.role==='product_image');if(first)hero.append(image(first,true));container.append(hero);
 const grid=el('div',null,'grid');container.append(grid);
 function card(title,key,wide=false){const n=el('section',null,'card'+(wide?' wide':''));n.dataset.module=key;n.append(el('h2',title));grid.append(n);return n;}
 function fields(parent,object,omit=[]){const dl=el('dl',null,'fields');for(const [k,v]of Object.entries(object)){if(omit.includes(k)||!present(v)||typeof v==='object'||typeof v==='boolean')continue;const f=el('div',null,'field');f.append(el('dt',t(k)),el('dd',typeof v==='string'&&['pass','fail','pending','not_tested','not_applicable','informational'].includes(v)?t(v):v,/(code|date|number|value|limit|hash|unit|size|weight|quantity|version)/.test(k)?'technical':undefined));dl.append(f);}if(dl.childNodes.length)parent.append(dl);}
 for(const k of ['product','batch','raw_material'])if(Object.values(p[k]).some(present)){const c=card(t(k),k);fields(c,p[k]);}
 if(p.process.length){const c=card(t('process'),'process',true),ol=el('ol',null,'process');for(const s of p.process)ol.append(el('li',s.label));c.append(ol);}
 if(p.inspection.length){const c=card(t('inspection'),'inspection',true),items=el('div',null,'inspection-grid');for(const i of p.inspection){const n=el('article',null,'inspection-item');n.append(el('h3',i.name),el('span',t(i.judgement),'status status-'+i.judgement));fields(n,i,['name','judgement','value_type','text_value']);if(present(i.result_display_text??i.text_value))n.append(el('p',Object.hasOwn(i,'result_display_text')?i.result_display_text:i.text_value));items.append(n);}c.append(items);}
 if(p.certifications.length){const c=card(t('certifications'),'certifications',true);for(const cert of p.certifications)fields(c,cert);}
 for(const k of ['packaging','storage','manufacturer'])if(Object.values(p[k]).some(present)){const c=card(t(k),k);fields(c,p[k]);}
 for(const s of p.custom_sections){const c=card(s.title,'custom-'+s.type,true);
  if(s.type==='text')c.append(el('p',s.content.text,'custom-text'));
  if(s.type==='key_value'){const dl=el('dl',null,'fields');for(const i of s.content.items){const d=el('div',null,'field');d.append(el('dt',i.label),el('dd',i.value));dl.append(d);}c.append(dl);}
  if(s.type==='table'){const wrap=el('div',null,'table-scroll');wrap.tabIndex=0;wrap.setAttribute('role','region');wrap.setAttribute('aria-label',s.title);const table=el('table'),head=el('thead'),tr=el('tr');table.append(el('caption',s.title));for(const col of s.content.columns){const th=el('th',col.label);th.scope='col';tr.append(th);}head.append(tr);table.append(head);const body=el('tbody');for(const row of s.content.rows){const r=el('tr');for(const val of row.cells)r.append(el('td',val));body.append(r);}table.append(body);wrap.append(table);c.append(wrap);}
  if(s.type==='asset_gallery'){c.append(el('p',s.content.caption));const gallery=el('div',null,'gallery');for(const key of s.asset_keys){const a=p.assets.find(x=>x.key===key);if(a)gallery.append(image(a));}c.append(gallery);}
 }
 if(p.assets.length){const c=card(t('assets'),'assets',true),gallery=el('div',null,'gallery');for(const a of p.assets)gallery.append(image(a));c.append(gallery);}
 return p;
}
export function renderError(container,code,retry){container.replaceChildren();container.removeAttribute('aria-busy');const n=el('section',null,'state');n.setAttribute('role','alert');n.append(el('h1',code==='not_found'?'Passport Not Found':code==='unsupported_schema'?'Unsupported passport version':'Passport temporarily unavailable'));n.append(el('p','Please try again later or contact the supplier.'));if(retry){const b=el('button','Retry');b.type='button';b.addEventListener('click',retry);n.append(b);}container.append(n);}
