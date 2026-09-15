import schema10 from './schema-1.0.mjs';
import schema11 from './schema-1.1.mjs';
export const CODE = /^[A-Za-z0-9_-]{1,64}$/;
export const VERSION = /^[1-9][0-9]{0,15}$/;
export function safeCode(code) { return typeof code === 'string' && CODE.test(code) && !/\s/.test(code); }
export function safeVersion(v) { return typeof v === 'string' && VERSION.test(v) && !/\s/.test(v) && Number.isSafeInteger(Number(v)); }
export function assetPath(a) {
 if (!a || typeof a.sha256 !== 'string' || !/^[a-f0-9]{64}$/.test(a.sha256) || a.mime_type !== 'image/png' || a.path !== `assets/sha256/${a.sha256.slice(0,2)}/${a.sha256}.png`) throw Error('unsafe_asset');
 return '/'+a.path;
}
function matches(s,v,root,depth=0) {
 if(depth>70) return false;
 const match=(q,x=v)=>matches(q,x,root,depth+1);
 if(s.$ref) return match(s.$ref.slice(2).split('/').reduce((o,k)=>o[k],root));
 if(s.const!==undefined && JSON.stringify(v)!==JSON.stringify(s.const)) return false;
 if(s.enum && !s.enum.some(x=>JSON.stringify(x)===JSON.stringify(v))) return false;
 if(s.type){const kind=v===null?'null':Array.isArray(v)?'array':typeof v;if(s.type==='integer'?!Number.isSafeInteger(v):kind!==s.type)return false;}
 if(s.allOf&&!s.allOf.every(x=>match(x)))return false;
 if(s.anyOf&&!s.anyOf.some(x=>match(x)))return false;
 if(s.oneOf&&s.oneOf.filter(x=>match(x)).length!==1)return false;
 if(s.if && !match(match(s.if)?s.then??{}:s.else??{}))return false;
 if(typeof v==='string'){
  const n=[...v].length;if(n<(s.minLength??0)||n>(s.maxLength??Infinity))return false;
  if(s.pattern&&!new RegExp(s.pattern,'u').test(v))return false;
  if(s.format==='date'&&(!/^\d{4}-\d{2}-\d{2}$/.test(v)||!Number.isFinite(Date.parse(v))||new Date(v).toISOString().slice(0,10)!==v))return false;
  if(s.format==='date-time'&&!Number.isFinite(Date.parse(v)))return false;
 }
 if(typeof v==='number'&&(v<(s.minimum??-Infinity)||v>(s.maximum??Infinity)))return false;
 if(Array.isArray(v)){
  if(v.length<(s.minItems??0)||v.length>(s.maxItems??Infinity))return false;
  if(s.uniqueItems&&new Set(v.map(x=>JSON.stringify(x))).size!==v.length)return false;
  if(s.items&&!v.every(x=>match(s.items,x)))return false;
 }else if(v&&typeof v==='object'){
  if(s.required?.some(k=>!Object.hasOwn(v,k)))return false;
  for(const [k,x]of Object.entries(v)){if(['__proto__','prototype','constructor'].includes(k))return false;if(s.properties?.[k]){if(!match(s.properties[k],x))return false;}else if(s.additionalProperties===false)return false;else if(typeof s.additionalProperties==='object'&&!match(s.additionalProperties,x))return false;}
 }
 return true;
}
const schemas=new Map([['1.0',schema10],['1.1',schema11]]); // Future dialects get independent validators/renderers, never a permissive fallback.
export function validatePayload(p) {
 const schema=schemas.get(p?.schema_version);if(!schema)throw Error('unsupported_schema');
 if(!matches(schema,p,schema)||!safeCode(p.batch.code))throw Error('invalid_payload');
 const keys=new Set();for(const a of p.assets){assetPath(a);if(keys.has(a.key))throw Error('invalid_payload');keys.add(a.key);}
 for(const a of p.assets){if(a.display_target&&a.role!=='section_image')throw Error('invalid_payload');if(a.display_target?.startsWith('process:')&&!p.process.some(s=>'process:'+s.step_key===a.display_target))throw Error('invalid_payload');}
 for(const s of [...p.custom_sections,...p.inspection,...p.certifications])for(const k of s.asset_keys??[])if(!keys.has(k))throw Error('invalid_payload');
 if(p.publication.kind==='rollback'&&!(p.publication.source_version_number<p.publication.version_number))throw Error('invalid_payload');
 if(p.record_type==='test'&&p.notice!=='TEST RECORD — NOT FOR COMMERCIAL USE')throw Error('invalid_payload');
 return p;
}
export function parseRoute(pathname) {
 const m=/^\/b\/([^/]+)(?:\/v\/([^/]+))?$/.exec(pathname);
 if(!m||!safeCode(m[1])||(m[2]&&!safeVersion(m[2])))throw Error('not_found');
 return {code:m[1],version:m[2]??null};
}
