const fs=require('fs'),path=require('path');const Ajv=require('../go-admin-ui/node_modules/.pnpm/ajv@6.15.0/node_modules/ajv');
const root=path.resolve(__dirname,'../..'),schema=JSON.parse(fs.readFileSync(root+'/runtime/t10/test-artifacts/public-schema-1.0.json'));
// The fixed contract uses keywords with the same semantics in Draft 7 and 2020-12.
// Ajv 6 is an independent supplemental validator, not our production 2020-12 implementation.
// Remove only the dialect marker; $defs references continue to resolve as local JSON pointers.
delete schema.$schema;const validate=new Ajv({allErrors:true,unknownFormats:'fail'}).compile(schema);const checks=[];
for(const dir of ['runtime/t10/publish/versions','runtime/t10/fresh/publish/versions']){
 for(const file of fs.readdirSync(root+'/'+dir,{recursive:true})){const full=root+'/'+dir+'/'+file;if(!full.endsWith('.json')||!fs.statSync(full).isFile())continue;const data=JSON.parse(fs.readFileSync(full));const ok=validate(data);checks.push({name:dir+'/'+file,status:ok?'PASS':'FAIL',errors:ok?undefined:validate.errors});if(!ok)console.error(file,validate.errors)}
}
fs.writeFileSync(root+'/runtime/t10/test-artifacts/independent-schema.json',JSON.stringify({validator:'Ajv 6.15.0; fixed keyword subset supplemental check',checks},null,2));if(checks.some(x=>x.status==='FAIL'))process.exitCode=1;console.log(checks.length+' snapshots checked');
