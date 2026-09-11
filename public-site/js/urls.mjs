import {safeCode,safeVersion} from './schema.mjs';
export function publicURL(base,code,version=null,mode='production') {
 if(!['production','local'].includes(mode))throw Error('Invalid public URL mode');
 if(!safeCode(code)||version!==null&&!safeVersion(String(version)))throw Error('Invalid batch code or version');
 if(typeof base!=='string'||base!==base.trim()||!/^https?:\/\//.test(base))throw Error('Invalid public base URL');
 const u=new URL(base);if(u.username||u.password||u.search||u.hash||u.pathname!=='/')throw Error('Base must be an origin without credentials, path, query or fragment');
 const hostname=u.hostname.replace(/\.$/,'');
 const local=hostname==='localhost'||hostname.endsWith('.localhost')||/^127\./.test(hostname)||hostname==='[::1]';
 if(mode==='production'&&(u.protocol!=='https:'||local))throw Error('Production requires a non-local HTTPS origin');
 if(u.protocol==='http:'&&(mode!=='local'||!local))throw Error('HTTP is allowed only for explicit local testing');
 return u.origin+'/b/'+code+(version===null?'':'/v/'+version);
}
