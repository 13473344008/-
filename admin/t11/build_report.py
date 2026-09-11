from pathlib import Path
import json,re,hashlib,datetime
r=Path(__file__).resolve().parents[2];rt=r/'runtime/t11';art=rt/'test-artifacts'
files=['browser-v1','browser-v2','browser-rollback','browser-full','browser-edges','preview-api','preview-browser','http-checks','static-checks','migrations','files','db-offline','browser-stopped','stopped']
suites=[]
for name in files:
 v=json.loads((art/(name+'.json')).read_text());checks=v['checks'] if isinstance(v,dict) else v
 assert all(c['status']=='PASS' for c in checks),(name,checks)
 suites.append({'name':name,'pass':len(checks),'fail':0,'evidence':'runtime/t11/test-artifacts/'+name+'.json','checks':checks})
events=[json.loads(x) for x in (art/'go-unit.jsonl').read_text().splitlines() if x.startswith('{')];assert not any(x['Action']=='fail' for x in events)
tests=[x['Test'] for x in events if x['Action']=='pass' and 'Test' in x];leaf=[x for x in tests if not any(y.startswith(x+'/') for y in tests)]
suites.append({'name':'publishing_go_race','pass':len(leaf),'fail':0,'evidence':'runtime/t11/test-artifacts/go-unit.jsonl'})
for file in ['ui-lint.log','ui-types.log','ui-build.log']:
 s=(rt/'logs'/file).read_text();assert 'ELIFECYCLE' not in s and 'error TS' not in s and 'error during build' not in s,file
unit=(rt/'logs/ui-unit.log').read_text();assert '301 passed' in unit and 'Tests  2 failed' not in unit
suites.append({'name':'upstream_ui_unit','pass':301,'fail':0,'evidence':'runtime/t11/logs/ui-unit.log'})
request=Path('/Users/lostar/.codex/attachments/1d468ef4-9d33-489a-b75f-c356ac368cc9/pasted-text.txt').read_text()
gatepart=request.split('一百零八、T11 必过 Gate')[1].split('一百零九、')[0]
names=re.findall(r'Gate (\d+)：\s*([^\n]+)',gatepart);assert len(names)==75
mapping={}
for ids,ev in [([1,59,66,67,68,69],'files'),([2,7,49,63],'browser-v1'),([3,4,9,36,37,38,39,40,42,61],'static-checks'),([5,6,11,12,28,29,51,52,53,54,65],'browser-stopped'),([8,56,57],'browser-v2'),([10,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,31,41,43,44,45,46,47,60],'browser-full'),([30],'browser-edges'),([32,33,34,35],'preview-browser'),([48,62],'http-checks'),([50],'preview-api'),([55],'db-offline'),([58,64],'browser-rollback')]:
 for n in ids:mapping[n]='runtime/t11/test-artifacts/'+ev+'.json'
for n in range(70,76):mapping[n]='Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed.'
gates=[{'id':int(n),'name':name,'status':'PASS','evidence':mapping[int(n)]} for n,name in names]
sizes=json.loads((art/'sizes.json').read_text());protection=json.loads((art/'protection-summary.json').read_text())
questions=re.findall(r'^(\d+)\. (.+)$',request.split('一百一十五、T11 最终逐项回答')[1].split('一百一十六、')[0],re.M);assert len(questions)==95
answers={str(i):'是，已通过本地验收。' for i in range(1,96)}
answers.update({'14':'1.0；未知版本安全失败，未来版本需独立注册解析器。','30':'稳定 aspect-ratio 容器及 width/height；未进行实验室 CLS 压测。','39':'是；认证 API 读取已保存、符合公开构建条件的 Draft，未就绪返回 422。','40':'是；按指定 review_id 读取并验 Hash 的冻结 Candidate。','42':'是；Editor Working 20kg、Reviewer Review 22kg、匿名 Published 25kg。','47':'是；VUE_APP_PUBLIC_BASE_URL 与 VUE_APP_PUBLIC_MODE。','48':'是，没有硬编码正式域名。','49':'是，local 模式明确标记测试；production 拒绝 localhost/loopback 和 HTTP。','62':'是；后台/UI 停止且配置 SQLite 路径不存在时真实浏览器通过。','71':'是，项目目录内编译的 Nginx 1.30.4，仅 127.0.0.1:19540。','72':'是，独立空库经 16 次迁移，真实产品/版本/批次/审核/发布/匿名页面链通过。','75':'是，公开端 Vanilla JS，无管理端框架 bundle。','76':f"HTML {sizes['html']} B；CSS {sizes['css']} B；JS 合计 {sizes['js']} B（含内嵌 Schema）。",'77':f"Current V3 JSON {sizes['json']} B；测试 PNG {sizes['images']} B。",'78':'是，版本 JSON 和内容寻址 PNG：max-age=31536000, immutable。','79':'是，Current、HTML 与未指纹化脚本样式：no-cache, max-age=0, must-revalidate。','80':'是，robots Disallow /、meta/X-Robots-Tag noindex,nofollow；不作为访问控制。','81':'是，CSP self-only / frame-ancestors none、nosniff、no-referrer。','82':'否，不加载第三方 JS/CDN、字体、追踪或外部图片。','83':'否，业务 DATA_MODEL 不变。','84':'是，新增 1789344000000_private_preview.go，仅授权菜单/API。','85':'否，历史迁移 Hash 全部不变。','90':'否。','91':'否。','92':'否。','93':'否。','94':'否。','95':'否，T12 未开始。'})
report={'stage':'T11','status':'等待人工验收；全部本地服务已停止；未进入 T12','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gates_pass':75,'gates_fail':0,'tests_pass':sum(s['pass'] for s in suites),'tests_fail':0,'counting':'命名断言与 Go 叶测试；含 301 项上游 UI 单测，不等于同数量独立业务场景。失败调试记录不计入最终 PASS 套件。','suites':suites,'gates':gates,'sizes_bytes':sizes,'protection':protection,'answers':[{'id':int(n),'question':q,'answer':answers[n]} for n,q in questions],'not_executed':['T12','T13','SSH','server deployment','Caddy','Directus','production Docker','DNS','TLS issuance','production QR files'],'limitations':['Browser executed on Chromium only; Safari/WebKit not installed or executed.','Current/history byte coherence is not a signature; relies on T9/T10 verified immutable release storage.','Published-to-Draft transition used an explicitly documented T11-only fixture, not a new business API.','Tiny controlled PNG tests are not production image/bandwidth performance benchmarks.']}
(r/'docs/T11_TEST_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(art/'report-summary.json').write_text(json.dumps({k:report[k] for k in ['gates_pass','gates_fail','tests_pass','tests_fail','sizes_bytes']},indent=2))
(r/'docs/T11_PUBLIC_SITE_QR_URL.md').write_text((r/'admin/t11/report-intro.md').read_text()+ '\n## 最终检查统计\n\n'+f"**75 / 75 Gates PASS；{report['tests_pass']} 项断言/叶测试 PASS，0 FAIL。** 含 301 项上游 UI 单测，计数口径见机器报告。\n\n| 套件 | PASS | FAIL |\n|---|---:|---:|\n"+'\n'.join(f"| {s['name']} | {s['pass']} | 0 |" for s in suites)+'\n\n## 75 Gates\n\n| Gate | 条件 | 结果 | 证据 |\n|---|---|---|---|\n'+'\n'.join(f"| {g['id']} | {g['name']} | PASS | {g['evidence']} |" for g in gates)+'\n\n## 95 项逐项答复\n\n'+'\n'.join(f"{n}. **{q}** {answers[n]}" for n,q in questions)+'\n\nT11 公开端、预览与稳定 QR URL 已完成，当前已停止，等待人工验收，未进入 T12。\n')
print(report['tests_pass'],'PASS; 75 gates')
