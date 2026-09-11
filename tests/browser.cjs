// Run with NODE_PATH pointing to an installed Playwright package. No production dependency.
const { chromium } = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const path = require('node:path');
const base = process.env.PDI_BASE_URL || 'http://127.0.0.1:8089';
const product = JSON.parse(fs.readFileSync(path.join(__dirname,'../site/products/PF-STD.json')));
const batch = JSON.parse(fs.readFileSync(path.join(__dirname,'../site/batches/PF-TEST-001.json')));
(async () => {
 const browser = await chromium.launch({headless:true, ...(process.env.PDI_CHROMIUM ? {executablePath:process.env.PDI_CHROMIUM} : {})});
 const results = [];
 const output = path.join(__dirname,'../.qa/product-id'); fs.mkdirSync(output,{recursive:true});
 async function test(name, fn) {
  const page = await browser.newPage({viewport:{width:390,height:844}});
  const errors=[]; page.on('pageerror',e=>errors.push(e.message));
  try { await fn(page); assert.deepEqual(errors,[]); results.push({name,status:'PASS'}); }
  catch(e){results.push({name,status:'FAIL',error:e.message});}
  finally{await page.close();}
 }
 async function visit(page,query='?batch=PF-TEST-001') { await page.goto(base+'/'+query); await page.locator('#app[aria-busy="false"]').waitFor(); }
 async function content(page,text){assert.ok((await page.locator('#app').innerText()).includes(text));}
 async function mock(page,kind,data){await page.route(`**/${kind}/*.json`,route=>route.fulfill({contentType:'application/json',body:typeof data==='string'?data:JSON.stringify(data)}));}
 await test('正常批次',async p=>{await visit(p);await content(p,'Potato Flakes');await content(p,'马铃薯雪花片');assert.equal(await p.locator('.section').count(),8);assert.equal(await p.locator('.certificate').count(),2);await content(p,'NOT_TESTED');assert.equal(await p.locator('meta[name="robots"]').getAttribute('content'),'noindex,nofollow');assert.match(await p.locator('.test-banner').innerText(),/TEST RECORD — NOT FOR COMMERCIAL USE/);assert.deepEqual(await p.locator('.process li').allTextContents(),product.manufacturing_process);});
 for(const [name,url,text] of [
 ['不存在批次','?batch=ABC-NOT-EXIST','This batch record could not be loaded.'],
 ['无 batch','','No batch number was provided.'],
 ['非法 batch','?batch=../../test','Invalid batch number.'],
 ['重复 batch','?batch=PF-TEST-001&batch=OTHER','Invalid batch number.'],
 ['换行 batch','?batch=PF-TEST-001%0A','Invalid batch number.'],
 ['编码路径穿越','?batch=..%2F..%2Ftest','Invalid batch number.']]){
 await test(name,async p=>{let count=0;p.on('request',r=>{if(r.url().includes('/batches/'))count++;});await visit(p,url);await content(p,text);if(name!=='不存在批次')assert.equal(count,0);});
 }
 await test('Product 不存在',async p=>{await p.route('**/products/*.json',r=>r.fulfill({status:404,body:'Not found'}));await visit(p);await content(p,'The product record for this batch could not be loaded.');});
 for(const kind of ['batches','products']) await test(`${kind} JSON 格式错误`,async p=>{await mock(p,kind,'{bad json');await visit(p);await content(p,kind==='batches'?'This batch record could not be loaded.':'The product record for this batch could not be loaded.');});
 await test('缺失非关键字段',async p=>{await mock(p,'products',{identity:{product_code:'PF-STD',product_name:'Potato Flakes'}});await mock(p,'batches',{product_code:'PF-STD',batch:'PF-TEST-001',record_type:'test'});await visit(p);await content(p,'Potato Flakes');assert.equal(await p.locator('.section').count(),8);assert.doesNotMatch(await p.locator('#app').innerText(),/undefined|null|NaN/);});
 await test('空值和错误非关键字段类型',async p=>{await mock(p,'products',{...product,raw_material:null,packaging:42,manufacturing_process:[null,{},'Cooking'],certifications:[null,{}]});await mock(p,'batches',{...batch,inspection:[null,{name:'Moisture',result:null,status:null}],raw_material_traceability:[]});await visit(p);await content(p,'Potato Flakes');assert.doesNotMatch(await p.locator('#app').innerText(),/undefined|null|NaN/);});
 await test('HTML 注入和不安全图片',async p=>{const evil='<img src=x onerror="window.injected=true">';await mock(p,'products',{...product,identity:{...product.identity,product_name:evil,product_image:'javascript:alert(1)'},certifications:[{name:evil,image:'https://example.com/tracker.png'}]});await mock(p,'batches',{...batch,inspection:[{name:evil,result:'<script>window.injected=true</script>'}]});await visit(p);await content(p,evil);assert.equal(await p.locator('#app img, #app script').count(),0);assert.equal(await p.evaluate(()=>window.injected),undefined);});
 await test('Product code 路径穿越',async p=>{let count=0;p.on('request',r=>{if(r.url().includes('/products/'))count++;});await mock(p,'batches',{...batch,product_code:'../../private'});await visit(p);await content(p,'This batch record could not be loaded.');assert.equal(count,0);});
 await test('批次身份不匹配',async p=>{await mock(p,'batches',{...batch,batch:'OTHER'});await visit(p);await content(p,'This batch record could not be loaded.');});
 await test('产品身份不匹配',async p=>{await mock(p,'products',{...product,identity:{...product.identity,product_code:'OTHER'}});await visit(p);await content(p,'The product record for this batch could not be loaded.');});
 await test('图片缺失回退',async p=>{await mock(p,'products',{...product,identity:{...product.identity,product_image:'assets/missing.png'}});await visit(p);await p.locator('.asset-fallback').waitFor();await content(p,'Image unavailable.');});
 await test('网络失败',async p=>{await p.route('**/batches/*.json',r=>r.abort());await visit(p);await content(p,'This batch record could not be loaded.');});
 await test('稳定路径前端解析',async p=>{await p.route('**/b/PF-TEST-001',r=>r.fulfill({contentType:'text/html',body:fs.readFileSync(path.join(__dirname,'../site/index.html'),'utf8')}));await visit(p,'b/PF-TEST-001');await content(p,'Potato Flakes');});
 for(const width of [320,390,768,1440])await test(`布局 ${width}px`,async p=>{await p.setViewportSize({width,height:900});await visit(p);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));if(width<600)assert.equal(await p.locator('td').first().evaluate(el=>getComputedStyle(el).display),'grid');await p.screenshot({path:path.join(output,`${width}.png`),fullPage:true});});
 await test('长文本手机布局',async p=>{await p.setViewportSize({width:320,height:800});await mock(p,'products',{...product,identity:{...product.identity,product_name:'LONG'.repeat(100)}});await mock(p,'batches',{...batch,inspection:[{name:'LONG'.repeat(100),result:'LONG'.repeat(100),status:'NOT_TESTED'}]});await visit(p);assert.ok(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));});
 await browser.close(); fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify(results,null,2)+'\n');console.log(JSON.stringify(results,null,2));if(results.some(r=>r.status==='FAIL'))process.exitCode=1;
})().catch(e=>{console.error(e);process.exitCode=1;});
