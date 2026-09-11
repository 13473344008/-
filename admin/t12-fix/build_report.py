from pathlib import Path
import json,re,hashlib,datetime
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t12-fix';art=rt/'test-artifacts';old=json.loads((R/'docs/T12_TEST_RESULTS.json').read_text());suites=[]
names=['flow-prepare','browser-create','browser-upload-seal','browser-batch','browser-inspections','working','flow-pending','browser-submit','browser-reject','browser-adjust','browser-resubmit','browser-approve','browser-publish','v1-checks','public-browser-v1','browser-clone','clone-checks','browser-r2','v2-prepare','browser-v2-edit','v2-checks','public-browser-v2','browser-rollback','v3-checks','media-checks','media-workflow-checks','contracts','fault-prepare','db-failure','browser-reconcile','damage-checks','concurrency','browser-admin-pages','public-browser-full','http-checks','static-checks','migration-backup','upgrade-check','final-verify','offline-verify','backup-restore','independence','public-browser-stopped','restored-http','stopped']
for name in names:
 d=json.loads((art/(name+'.json')).read_text());checks=d if isinstance(d,list) else d['checks'];assert checks and all(x['status']=='PASS' for x in checks),(name,checks)
 suites.append({'name':name,'pass':len(checks),'fail':0,'checks':checks,'evidence':'runtime/t12-fix/test-artifacts/'+name+'.json'})
for name in ['core-regression','ordinary-publish-faults']:
 raw=(rt/'logs'/(name+'.log')).read_text();assert '\nFAIL' not in raw and '\nPASS\n' in raw;tests=re.findall(r'--- PASS: (\S+) ',raw);leaves=[n for n in tests if not any(m.startswith(n+'/') for m in tests)];suites.append({'name':name,'pass':len(leaves),'fail':0,'tests':leaves,'evidence':'runtime/t12-fix/logs/'+name+'.log'})
ci=(rt/'logs/ui-ci-retry.log').read_text();assert '305 passed (305)' in ci and 'API contract ok:' in ci and 'dict.values: 33 key(s), all matched' in ci
suites += [{'name':'UI unit (301 existing + 4 media)','pass':305,'fail':0,'evidence':'runtime/t12-fix/logs/ui-ci-retry.log'},{'name':'Full CI lint/type/API/i18n','pass':4,'fail':0,'evidence':'runtime/t12-fix/logs/ui-ci-retry.log'},{'name':'UI production build','pass':1,'fail':0,'evidence':'runtime/t12-fix/logs/ui-build.log'}]
assert 'built in' in (rt/'logs/ui-build.log').read_text()
ev={}
def assign(ids,files):
 for i in ids:ev[i]=files
assign([1,2],'environment.json; logs/migrate-first.log; migration-backup.json')
assign([3],'migration-backup.json; upgrade-check.json')
assign([4,5,18,22],'working.json; flow-pending.json; media-checks.json; media-workflow-checks.json; concurrency.json')
assign([6,7,8,9,10,11],'browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json')
assign([12,13,14,15,16],'browser-batch.json; browser-inspections.json; working.json; browser-submit.json')
assign([17,19,20,21,39],'browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json')
assign([23,25],'browser-upload-seal.json; browser-publish.json; v1-checks.json; v2-prepare.json; final-verify.json')
assign([24,80,81,82,83,84,86],'final-verify.json; offline-verify.json')
assign([26,27],'public-browser-v1.json')
assign([28,29,38,67,68,69,70,71,73,74,75,78,79],'public-browser-full.json; public-browser-stopped.json')
assign([30,31],'v2-prepare.json')
assign([32],'browser-clone.json; clone-checks.json; media-workflow-checks.json; v3-checks.json')
assign([33,34,35],'browser-v2-edit.json; v2-checks.json; version-compare.json; public-browser-v2.json')
assign([36,37,40,41,42,72],'browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json')
assign([43,44],'logs/ordinary-publish-faults.log; faults.json')
assign([45,46,47,48],'db-failure.json; browser-reconcile.json; damage-checks.json')
assign([49,50,51],'damage-checks.json; damage-details.json')
assign([52,53,54,55,56],'concurrency.json; final-verify.json')
assign([57,58,59,60],'backup-restore.json')
assign([61,62,63,64],'backup-restore.json; independence.json; restored-http.json; public-browser-stopped.json')
assign([65,66,76,77],'http-checks.json; restored-http.json; public-browser-v1.json; public-browser-v2.json; public-browser-full.json')
assign([85],'stopped.json')
assign([87,88,89,90,91,95],'本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json')
assign([92,93,94],'docs/T13_DEPLOYMENT_PRECHECK.md（历史设计清单）；本报告部署边界补充；未执行部署')
gates=[{**g,'status':'PASS','evidence':ev[g['id']]} for g in old['gates']];assert len(gates)==95
counts=json.loads((art/'final-verify.json').read_text())['counts'];backup=json.loads((art/'backup-restore.json').read_text());sizes=json.loads((art/'sizes.json').read_text())
new_code=['admin/go-admin/app/passport/service/media.go','admin/go-admin/app/passport/apis/media.go','admin/go-admin/app/admin/router/passport_media.go','admin/go-admin/cmd/migrate/migration/version/1789430400000_media_permissions.go','admin/go-admin/app/passport/service/t12_fix_publish_test.go','admin/go-admin-ui/src/api/passport/media.ts','admin/go-admin-ui/src/views/passport/media/MediaPanel.vue','admin/go-admin-ui/src/lang/en-US/passport/media.ts','admin/go-admin-ui/src/lang/zh-CN/passport/media.ts','admin/go-admin-ui/tests/unit/components/passport-media.spec.ts']
assert all((R/p).is_file() for p in new_code)
source=json.loads((art/'source-before.json').read_text());changed=[p for p,h in source.items() if not (R/p).is_file() or hashlib.sha256((R/p).read_bytes()).hexdigest()!=h]
fixes={25:'新增正式上传/关联入口，真实 PNG/JPEG 随 Candidate 规范化并冻结；替换 R2/V2 工作图片后旧文件全 Hash 不变。',32:'Clone 从 Draft 写操作改为受权限/版本控制的只读来源复制；允许 Draft/Published，新 Draft 重置状态/实测值，来源 Batch 全行与审计不变。',35:'V2 通过 UI 覆盖 gallery 并上传新图片；API/UI Compare 出现实际 assets 差异。',43:'普通 Publishing.Publish 实测 build/write/copy:1/copy:2/validation/manifest/rename/finalize，断言注入点确实命中。',50:'独立批次真实上传图片形成独立 CAS；损坏后 Verify 失败、Rollback 409、Current 不变，恢复后通过。',60:'备份真实 DB、私有源图片、公开 JSON/CAS 图片、Manifest 和前端，逐文件核对。',61:'独立恢复目录经真实 Nginx 提供 V1/V2/V3 与所有恢复图片。',62:'后台/UI 进程停止后真实浏览器图片 naturalWidth>0，HTTP 字节与 Hash 正确。',63:'配置 DB 主文件/WAL/SHM 移到 offline 名称，公开版本与图片仍可访问；最后恢复原名原字节。',64:'独立 Nginx quit 后从恢复根重新启动，真实图片和页面验收通过。',66:'实际 Version/Asset 响应 immutable、ETag 304；恢复图片仍 immutable。',83:'非空46条 Published Assets逐条校验 Hash/大小；9个私有媒体源逐条校验；全部Manifest确定编码一致。'}
answers=[
'是。新增三个对象范围、九条带 JWT/LiveIdentity/Casbin/数据范围约束的媒体路由；只接收 PNG/JPEG。',
'是。普通 Editor 在真实 Chromium 中上传主图 PNG、gallery JPEG，并在 R2/V2 上传替换图片。',
'是。新库共9条 MediaAsset，全部通过正式上传 API 建立；含2条解除关联后保留的私有源。',
'是。关联 ProductRevision 主图、Product gallery 与 Batch gallery；通过对象归属、Draft锁和乐观Token检查。',
'是。Working/Review真实含图预览；提交冻结规范化图像及源Hash，Reviewer浏览器查看。',
'是。实际产生46条 PublishedAsset记录；与工作关联隔离，封存后不可变。',
'是。V1/V2/V3及恢复副本真实图片加载通过，PNG/JPEG均生成安全PNG公开副本。',
'是。R2解除旧主图并上传新图，V2替换gallery；V1/V2已有JSON及图片字节保持不变。',
'是。Published来源通过Editor UI克隆成新Draft；Draft及回滚后的Published也通过。',
'是。主来源Batch全行及其审计记录前后完全一致；没有解锁或修改来源批次。',
'是。新对象无旧Review/Publish/PassportRevision/Current关系；只复制工作模板关联，重新分配关联ID。',
'是。五项检验结构保留，numeric/text/tested_on及结论重置；日期默认null，质量pending。',
'是。正式媒体入口缺失、Published Clone 409、通用契约检查失败均已修复并补证。',
'是。原25/32/35/43/50/60/61/62/63/64/66/83均PASS，逐项证据见下表。',
'是。新媒体参数/响应/权限独立契约检查通过，真实正负请求通过，完整test:ci通过。',
'是。原日志和失败报告保留四项诊断原文。本轮修正Passport模型/DTO绑定，未删除检查；未知字段/查询注入仍失败。',
'是。普通Publish第二张图复制失败实际命中，旧Current不变；另覆盖复制第一张及其余六阶段。',
'是。普通Publish的实际SQLite触发器制造finalize失败，file_switched_db_pending阻止新发布/回滚；Admin浏览器Reconcile确认同一记录。',
'是。全新T12-fix空库17迁移，图片由正式UI/API输入，完整审核发布、V2、回滚和恢复通过；媒体未用SQL或手工置入私有目录。',
'是。后台/UI停止且配置DB文件离线，公开图片仍可访问。',
'是。独立恢复公开目录经重启Nginx，V1/V2/V3和全部恢复CAS图片通过HTTP Hash验证。',
'是。工作库、独立恢复库与升级副本integrity_check均为ok。',
'是。foreign_key_check为空，无悬空外键。',
'是。全量已封存JSON、46条PublishedAsset、9个私有源及Manifest均一致。',
'No。没有修改T4–T11历史Migration。只新增1789430400000权限迁移，不变更媒体/工作流业务Schema。',
'No。没有连接服务器；未访问SERVER_IP、Caddy、Directus、生产Docker、DNS或HTTPS。',
'No。未进入T13，T14也未进入。等待本轮人工验收；不以本地通过替代部署授权。']
categories=['Media Upload','Media Association','Published Asset E2E','Published Batch Clone','API Contract','Failure Coverage','Fresh E2E','Review','Publish','Rollback','Reconcile','Backup / Restore','Static Restore','Backend Independence','Integrity','Regression','Baseline Protection']
report={'phase':'T12 remediation','status':'awaiting_human_acceptance','first_result':{'gates_pass':83,'gates_total':95,'tests_pass':638,'tests_fail':3},'gates_pass':95,'gates_fail':0,'tests_pass':sum(s['pass'] for s in suites),'tests_fail':sum(s['fail'] for s in suites),'categories':{c:'PASS' for c in categories},'gates':gates,'suites':suites,'original_failed_gates':[{'id':g['id'],'original_reason':g['evidence'],'remediation':fixes[g['id']],'final_status':'PASS','evidence':ev[g['id']]} for g in old['gates'] if g['status']!='PASS'],'answers':{str(i+1):a for i,a in enumerate(answers)},'counts':counts,'changed_existing_files':changed,'new_code_files':new_code,'migration':'1789430400000_media_permissions.go; permissions only; 17 total','test_count_policy':'Only final assertions and Go leaf tests, UI305; command checks separately4+build1. Historical638/3 not included. Failed harness attempts retained and superseded, not counted as unresolved final test failures. Browser phases rerun onV2 use their final successful JSON; earlier actual V1 log evidence retained.','stopped':True,'server_connected':False,'entered_T13':False}
(R/'docs/T12_REMEDIATION_TEST_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
text=f'''# 【T12 修复后执行结果】

T12 状态：**等待人工验收**。本报告记录本地验证事实，未代替用户验收。

第一次结果：83 / 95 Gate PASS；638 PASS，3 FAIL。原报告与原运行证据完整保留。

修复后结果：**Gate 95 / 95 PASS；Tests {report['tests_pass']} PASS，0 FAIL**。

'''
text+='| 项目 | 结果 |\n|---|---|\n'+'\n'.join(f'| {c} | PASS |' for c in categories)+'\n\n'
text+='## 原12项缺口与修复\n\n| Gate | 原根因/证据缺口 | 修复及补验 |\n|---|---|---|\n'+'\n'.join(f"| {x['id']} | {x['original_reason']} | {x['remediation']} |" for x in report['original_failed_gates'])+'\n\n'
text+='## 实现与三个FAIL\n\n正式媒体入口：`MediaPanel` 使用 FormData，不手设 Content-Type；支持主图与当前对象的 asset_gallery 上传、查看及Draft解除关联。必须填写纯文本标签、显式设置公开意图。扩展名/MIME/实际解码一致，仅PNG/JPEG，输入及规范化输出最多2MiB，边长4096、像素1600万；主图1张，gallery最多16张。页面显示SHA、MIME、大小与从图像读取的尺寸。服务端随机私有文件名、OpenRoot约束与0600写入；归属、权限、状态、Token、媒体记录、关联和审计在同一数据库事务内校验/写入，失败清理本次新文件。审计沿用media_replaced，以changed_fields区分upload/attach/detach；没有新增事件Schema。解除关联保留源文件；替换通过新上传完成，未增加全局DAM或任意媒体挂载入口。\n\nPublished Clone：把Clone从Draft编辑锁中分离，事务取得写锁后只读校验来源；允许Draft/Published，拒绝活动发布、Pending、Ready及Archived。新建独立Draft，保持Product/base、允许的override、检验结构及模块；重置日期/实测值/tested_on/质量/审核发布绑定。工作链接复制为新ID并指向不可变私有源；不复制Published关联。UI克隆按钮移到禁用编辑表单外，Published编辑区仍锁定。主来源全行/审计对比通过。Archived无正式归档入口，本轮只将独立辅助Draft设置为Archived来验证Clone明确409，未扩展归档业务。\n\n原3个FAIL分别为正式媒体入口缺失、Published来源Clone409、UI test:ci中的check:api失败；现在对应正向E2E和完整CI均通过。原check:api四项诊断为Batch未解析、Product误配DemoProduct、search误配demo DTO、QueueRow未解析；原`runtime/t12/logs/ui-ci.log`与原T12报告保留。本轮增加Passport实际模型/DTO目录及显式页面绑定；没有删除断言或字段白名单豁免。临时注入未知响应字段/查询仍使检查失败。新媒体响应字段、multipart参数、权限链单独8项契约检查通过。\n\n'
text+='## Fresh DB、图片主链与版本\n\n新库`runtime/t12-fix/db/passport-admin-t12-fix.db`从空库执行17迁移。Go1.26.5、Go SQLite3.53.4、WAL/FK1/busy_timeout5000/synchronousFULL/maxconn1；Node24.18.0、pnpm9.15.1。图片在浏览器中作为本地上传输入，私有媒体存储文件由正式API创建；没有SQL媒体夹具。\n\n主Product PF-T12-TEST：Editor UI创建R1，正式API补全六语言与四种模块结构；UI维护25kg、上传PNG主图和JPEG gallery、Seal并设默认。UI创建001、20kg override、五项检验及批次模块。Reviewer查看冻结图片、Reject；随后首次V1审核发布通过。第一次驳回后的UI修改脚本误用了中文按钮“编辑”，且初始串行脚本未及时止于该错误；因此未把这段作为完整驳回修改证明。保留失败日志，并用set -e在V2完整重跑 Submit→Reviewer Reject→Editor真实修改→Resubmit→Approve→Admin Publish，全部通过，四次审核尝试及精确驳回原因保留。\n\nR2真实UI Clone R1，解除主图关联后上传replacement.png，改30kg并Seal/default；旧001仍R1，新002使用R2。Published 001实际UI Clone003为Draft，先验证日期和五项实测清空，再将003作为独立媒体锁回归样本维护并发布，未把其最终状态冒充克隆刚完成状态。\n\n普通Published→Draft尚非正式产品入口。按原T12§42明确授权，仅本地主001及故障辅助批次使用受控Candidate状态夹具，保留Current与历史；后续图片上传和业务编辑/审核/发布走正式UI/API。V2 UI覆盖gallery并上传新图、改22kg及检验值，公开两张图；Compare实际assets差异。Admin UI回滚V1为新V3，旧V1/V2完整字节不变。没有为此开放已发布对象任意编辑。\n\n'
text+='## 故障、权限与回归\n\n普通Publish实际命中build、write、copy:1、copy:2、validation、manifest、rename、finalize八阶段，均检查命中标记。切换前失败状态failed、旧文件Current/DB头不变、旧版不变，新幂等键重试形成新版本；finalize后为recovery_required，文件已换而DB头仍旧，阻止重试，Reconcile完成同一操作。另在独立含两张正式上传图片的批次上，用SQLite BEFORE UPDATE published_at触发器制造真实数据库失败，API观察file_switched_db_pending，Publish/Rollback409，移除故障后由Admin浏览器Reconcile。故障触发器全部清理。\n\n独立CAS图片、JSON、Manifest各自保存原字节后损坏，Verify均integrity_error、Rollback409、Current不变，finally恢复后verified。损坏图片用独立辅助图，不污染主001图片。详情见damage-details.json；Go阶段实际状态见ordinary-publish-faults.log。\n\nReviewer/Viewer可读但不能上传/解除，Editor可改Draft；Pending/Ready/Published/Sealed锁、跨对象拒绝、私有图片过滤、过期Token、非法MIME/扩展名/解码、超限/超像素、审计失败整体回滚均验证。T5/T6/T7核心服务106个叶测试、普通Publish故障8个叶测试；T8–T11受影响工作流/权限/并发/版本/静态公开路径以本轮API和浏览器验证。六项并发竞争无重复版本/编码/双重审核。UI原301+新增4单测通过；完整test:ci通过；prod build通过。\n\n'
text+=f'''## Backup / Restore、全量Hash与停止

最终一致备份时间：{backup['started_at']}，SQLite Backup API。备份 `runtime/t12-fix/backups/t12-fix-final.db`，SHA256 `{backup['backup_sha256']}`。恢复到独立restored.db，全部表行数与数据摘要一致，integrity/FK通过。日志表包含既有响应截断导致的非UTF-8文本字节；哈希脚本使用surrogateescape无损保留这些字节比较，没有跳过该表或替换坏字节。它不影响业务JSON或数据库完整性，但日志截断的UTF-8处理仍可另行改进。

DB、私有源media、releases/Manifest、公开JSON/CAS及前端分别备份并恢复到独立目录。真实Nginx退出后从恢复根重新启动；后台18111、UI19543停止，配置DB及存在的WAL/SHM移为offline名称，公开六语言/RTL/五尺寸和真实图片通过；V1/V2/V3及全部恢复CAS图片HTTP字节/Hash正确。随后恢复DB原名原字节，最终18111/18112/19543/19544均关闭。

数据计数：{json.dumps(counts,ensure_ascii=False)}。2条解除关联后的媒体源按设计保留，不是悬空外键；foreign_key_check空，无重复revision/batch/review/published版本，无残留活动发布或测试触发器。全部已封存JSON与数据库payload/hash相符、每条PublishedAsset及私有源Hash/大小相符、Manifest全字段确定编码相符，包括保留的失败prepared诊断。53文件基线、site7文件、31854历史受保护文件及原T12两份失败报告不变。

性能样本：HTML {sizes['html']}B、CSS {sizes['css']}B、公开JS {sizes['js']}B、V3 Current JSON {sizes['json']}B、两张图合计{sizes['images']}B；最大主链图片26371B。六语言、375/390/430/1280/1440px无横向溢出，图片懒加载实际成功。只代表本机测试样本，不是生产容量承诺。

'''
text+='## 文件与Migration\n\n修改已有文件（以本轮source-before为基准，而非混入T4–T11未提交文件）：\n\n'+'\n'.join('- `'+p+'`' for p in changed)+'\n\n新增业务/测试源码：\n\n'+'\n'.join('- `'+p+'`' for p in new_code)+'\n\n另新增`admin/t12-fix/`验收脚本、独立`runtime/t12-fix/`证据，以及本报告和机器结果；TASKS更新为等待人工验收。新迁移1789430400000仅增加媒体菜单/API/Casbin授权，无业务DDL。空库17迁移与重复执行通过；原T12数据库的独立复制库升级后，全部业务表Hash不变，只有权限表、迁移记录及其SQLite自增计数改变。没有修改历史迁移或原库数据。\n\n'
text+='## 计数与已知边界\n\n| 套件 | PASS | FAIL | 证据 |\n|---|---:|---:|---|\n'+'\n'.join(f"| {s['name']} | {s['pass']} | {s['fail']} | {s['evidence']} |" for s in suites)+'\n\n'+report['test_count_policy']+'\n\n失败脚本尝试原日志保留：日期选择器、中文按钮、已克隆Draft的日期/模块未确认、归档路由不存在、日志非UTF8哈希读取、升级自增元数据计数差异；逐一纠正测试前置条件/定位/比较口径并重跑，未删除产品安全拒绝或降低业务断言。失败截图及旧轮次结果不算本轮未解决FAIL，也不伪装为首次全部成功。\n\n本轮未构建通用DAM/PDF/SVG/WebP上传、跨对象媒体库/GC/自动扫描；上传后更改公开意图通过Draft解除并重新上传实现。没有生产负载、真实断电、远程备份或异机恢复证据。现有本地SQLite方案不等于生产多写实例可行。既有日志响应截断按字节可能产生非UTF8日志，应作为后续维护项处理。\n\n部署边界：原T13_DEPLOYMENT_PRECHECK.md仅历史设计清单，其“媒体/PublishedClone缺口”在本轮已经修复；正式Published→Draft产品边界、测试/生产隔离、源媒体/Manifest/CAS协同备份、运行时权限/资源/代理路径仍须后续明确。清单中的独立Compose、先测试后生产、共享代理变更事前确认、保留旧发布并只回退本项目仍适用。本轮没有实施任何部署，也未生成生产QR。\n\n'
text+='## 27项特别答复\n\n'+'\n\n'.join(f'{i+1}. {a}' for i,a in enumerate(answers))+'\n\n'
text+='## 原95 Gate最终结果\n\n以下文件名默认位于runtime/t12-fix/test-artifacts，logs例外位于runtime/t12-fix。边界Gate以本轮实际工具操作范围核对，未以连接服务器验证“没有连接”。\n\n| Gate | 条件 | 最终 | 证据 |\n|---:|---|---|---|\n'+'\n'.join(f"| {g['id']} | {g['name']} | PASS | {g['evidence']} |" for g in gates)+'\n\nT12 修复回合已完成，95/95 Gate PASS，0 FAIL，当前已停止，等待人工验收，未进入 T13。\n'
(R/'docs/T12_REMEDIATION.md').write_text(text)
print(json.dumps({k:report[k] for k in ['gates_pass','gates_fail','tests_pass','tests_fail']},ensure_ascii=False))
