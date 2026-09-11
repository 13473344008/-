const {chromium,expect}=require('../go-admin-ui/node_modules/@playwright/test');
const fs=require('fs'),path=require('path');const rt=path.resolve(__dirname,'../../runtime/t11'),base='http://127.0.0.1:19540',ui='http://127.0.0.1:19539',phase=process.argv[2]||'v1';
(async()=>{const browser=await chromium.launch({executablePath:'/Users/lostar/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',headless:true});const checks=[],errors=[],network=[];let page;
const check=(name,ok=true)=>{checks.push({name,status:ok?'PASS':'FAIL'});console.log(name,ok);if(!ok)throw Error(name)};
const ctx=await browser.newContext({viewport:{width:1280,height:1000}});page=await ctx.newPage();page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>network.push({url:r.url(),authorization:!!r.headers().authorization}));
async function passport(url=base+'/b/PF-T11-TEST-001'){await page.goto(url);await expect(page.locator('[data-module=publication]')).toBeVisible();}
async function version(n){await expect(page.locator('[data-module=publication]')).toContainText(String(n));check('Public '+phase+' version '+n,await page.locator('[data-module=publication] dd').first().textContent()===String(n));}
try{
 await passport();await version(phase==='v1'?1:phase==='v2'?2:3);check('TEST notice visible',await page.locator('.test-notice').textContent()==='TEST RECORD — NOT FOR COMMERCIAL USE');
 if(['v1','v2','rollback','stopped'].includes(phase)){
  await passport(base+'/b/PF-T11-TEST-001/v/1');await version(1);await passport();
 }
 if(phase==='full'||phase==='stopped'){
  for(const [lang,name]of Object.entries({en:'Potato Flakes','zh-CN':'马铃薯雪花粉',es:'Copos de patata',ar:'رقائق البطاطس',fr:'Flocons de pomme de terre',de:'Kartoffelflocken'})){await page.selectOption('#language',lang);await expect(page.locator('h1')).toContainText(name);check('Language '+lang,await page.locator('html').getAttribute('dir')===(lang==='ar'?'rtl':'ltr'));}
  await page.selectOption('#language','en');
  for(const module of ['product','batch','raw_material','process','inspection','packaging','storage','manufacturer','custom-text','custom-key_value','custom-table','custom-asset_gallery','assets'])check('Rendered '+module,await page.locator('[data-module="'+module+'"]').count()===1);
  check('Nine process steps',await page.locator('.process li').allTextContents().then(x=>JSON.stringify(x)===JSON.stringify(['Raw Potato Receiving','Washing','Peeling','Cooking','Mashing','Drum Drying','Flaking','Inspection','Packaging'])));
  check('Six dynamic inspections',await page.locator('.inspection-item').count()===6);check('All judgement text',await page.locator('.status').allTextContents().then(x=>x.length===6&&x.includes('Not applicable')&&x.includes('Not tested')));
  for(const width of [375,390,430,1280,1440]){await page.setViewportSize({width,height:1000});check('No page overflow '+width,await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.screenshot({path:rt+'/test-artifacts/public-'+phase+'-'+width+'.png',fullPage:true});}
  await page.locator('[data-module=assets]').scrollIntoViewIfNeeded();await expect(page.locator('[data-module=assets] img').first()).toBeVisible();await page.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));check('Frozen images load');check('Below-fold images lazy',await page.locator('[data-module=assets] img').first().getAttribute('loading')==='lazy');
 }
 if(phase==='full'){
  const current=fs.readFileSync(rt+'/publish/published/PF-T11-TEST-001.json','utf8');
  async function bad(name,body,expected='Passport temporarily unavailable') {await page.route('**/published/PF-T11-TEST-001.json',r=>r.fulfill({contentType:'application/json',body}));await page.goto(base+'/b/PF-T11-TEST-001');await expect(page.locator('h1')).toHaveText(expected);check(name);await page.unroute('**/published/PF-T11-TEST-001.json');}
  await bad('Malformed JSON','{');let p=JSON.parse(current);p.schema_version='99.0';await bad('Unsupported schema',JSON.stringify(p),'Unsupported passport version');
  p=JSON.parse(current);p.product.name='Changed current';await bad('Current differs from immutable version',JSON.stringify(p));
  p=JSON.parse(current);p.assets[0].path='javascript:alert(1)';await bad('Dangerous asset rejected',JSON.stringify(p));
  await page.route('**/published/PF-T11-TEST-001.json',r=>r.abort());await page.goto(base+'/b/PF-T11-TEST-001');await expect(page.locator('h1')).toHaveText('Passport temporarily unavailable');check('Network failure finite error');await page.unroute('**/published/PF-T11-TEST-001.json');await page.getByText('Retry',{exact:true}).click();await expect(page.locator('[data-module=publication]')).toBeVisible();check('Retry recovers');
  await page.route('**/assets/**',r=>r.abort());await passport();await page.locator('[data-module=assets]').scrollIntoViewIfNeeded();await expect(page.locator('[data-module=assets] .asset-unavailable').first()).toBeVisible();check('Missing asset placeholder');await page.unroute('**/assets/**');
  // Safe text and fallback are tested on a structurally valid isolated fixture in memory, never a release mutation.
  const safety=await page.evaluate(async raw=>{const {renderPassport,localized}=await import('/js/render.mjs');const p=JSON.parse(raw);p.custom_sections.find(s=>s.type==='text').content.text='<img src=x onerror="window.XSS=1">';const root=document.createElement('div');renderPassport(root,p);p.localization.translations.find(t=>t.language_code==='zh-CN').storage={conditions:null};return {safe:root.textContent.includes('<img')&&!root.querySelector('img[src=x]')&&!window.XSS,fallback:localized(p,'zh-CN').packaging.quantity===p.packaging.quantity,clear:localized(p,'zh-CN').storage.conditions===null};},current);for(const [k,v]of Object.entries(safety))check('DOM '+k,v);
  for(const [path,status]of [['/b/NO-SUCH-TEST',404],['/b/PF-T11-TEST-DRAFT',404],['/b/PF-T11-TEST-001/v/99',404],['/runtime/t11/credentials.json',404]]){const r=await page.goto(base+path);check('Nginx '+path,r.status()===status);}
  await passport();const perf=await page.evaluate(()=>({navigation:performance.getEntriesByType('navigation').map(n=>({duration:n.duration,domContentLoaded:n.domContentLoadedEventEnd})),resources:performance.getEntriesByType('resource').map(r=>({url:r.name,bytes:r.transferSize,duration:r.duration}))}));fs.writeFileSync(rt+'/test-artifacts/performance.json',JSON.stringify(perf,null,2));
 }
 check('Anonymous network only static origin',network.every(r=>r.url.startsWith(base+'/')&&!r.authorization&&!/\/api\/v1\/|\/products\/|\/batches\//.test(r.url)));check('No uncaught JS errors',errors.length===0);
}catch(e){checks.push({name:'Completed '+phase,status:'FAIL',error:e.message});console.error(e);process.exitCode=1;if(page)await page.screenshot({path:rt+'/test-artifacts/failure-'+phase+'.png',fullPage:true});}finally{fs.writeFileSync(rt+'/test-artifacts/browser-'+phase+'.json',JSON.stringify({checks,errors,network},null,2));await browser.close();}})();
