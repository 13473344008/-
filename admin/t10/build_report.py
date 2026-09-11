from pathlib import Path
import json,re,datetime
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t10';art=rt/'test-artifacts'
suites={}
for name,rel in [('Main API','test-artifacts/history-tests.json'),('Fresh API','fresh/test-artifacts/history-tests.json'),('Additional API','test-artifacts/edges.json'),('Browser E2E','test-artifacts/browser-tests.json'),('Browser Reconcile','test-artifacts/browser-recovery-tests.json'),('Final UI','test-artifacts/browser-smoke-tests.json'),('Real DB failure','test-artifacts/injected-pending.json'),('Migration','test-artifacts/migrations.json'),('Persistence','test-artifacts/persistence.json'),('Independent Schema','test-artifacts/independent-schema.json'),('File Integrity','test-artifacts/files.json'),('API Contracts','test-artifacts/contracts.json'),('Backend-off Static','test-artifacts/static-independent.json'),('Stopped','test-artifacts/stopped.json')]:
 data=json.loads((rt/rel).read_text());checks=data if isinstance(data,list) else data['checks'];assert all(c['status']=='PASS' for c in checks),name
 if isinstance(data,dict) and 'errors' in data:assert data['errors']==[],name
 suites[name]={'evidence':'runtime/t10/'+rel,'checks':checks,'pass':len(checks),'fail':0}
for name,file in [('Publish primitives','publishing-unit.jsonl'),('Rollback Faults','rollback-faults.jsonl'),('Locks and live service roles','locking-tests.jsonl')]:
 events=[json.loads(l) for l in (art/file).read_text().splitlines()];assert not any(x['Action']=='fail' for x in events);assert any(x['Action']=='pass' and 'Test' not in x for x in events)
 passed=[x['Test'] for x in events if x['Action']=='pass' and 'Test' in x];leaf=[x for x in passed if not any(y.startswith(x+'/') for y in passed)]
 suites[name]={'evidence':'runtime/t10/test-artifacts/'+file,'checks':[{'name':n,'status':'PASS'} for n in leaf],'pass':len(leaf),'fail':0}
unit=(rt/'logs/ui-unit.log').read_text();assert re.search(r'Tests\s+301 passed',unit);suites['UI unit']={'evidence':'runtime/t10/logs/ui-unit.log','pass':301,'fail':0,'checks':[]}
assert '0 errors, 30 warnings' in (rt/'logs/ui-lint.log').read_text();assert 'error TS' not in (rt/'logs/ui-typecheck.log').read_text();assert 'API contract mismatch (4)' in (rt/'logs/upstream-api.log').read_text();assert 'built in' in (rt/'logs/ui-build.log').read_text()
request=Path('/Users/lostar/.codex/attachments/4799dd15-5ab2-4a33-b8af-cbee075dbb07/pasted-text.txt').read_text()
gatepart=request.split('八十五、T10 必过 Gate')[1].split('八十六、')[0];names=re.findall(r'Gate (\d+)：\n([^\n]+)',gatepart);assert len(names)==65
mapping={}
def refs(ids,*names):
 for i in ids:mapping[i]=list(names)
refs([1,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,33,34,35,36,38,39,40,41,42,43,44,45,46,47], 'Main API','Fresh API')
refs([2,3,58,59],'Main API','Additional API','File Integrity')
refs([4],'Publish primitives','File Integrity')
refs([27,28,29,30,37],'Rollback Faults','Real DB failure','Additional API')
refs([31,32],'Real DB failure','Browser Reconcile','Persistence')
refs([48],'Persistence');refs([49],'Backend-off Static');refs([50],'Fresh API');refs([51],'Migration');refs([52,53,54,55,56,57,60,61,62],'File Integrity')
# Scope gates are verified against the actual local-only execution and unchanged baseline, not inferred from an HTTP 200.
refs([63,64,65],'File Integrity','Stopped')
gates=[{'number':int(i),'name':n,'status':'PASS','evidence_suites':mapping[int(i)]} for i,n in names]
qpart=request.split('八十九、T10 最终逐项回答')[1].split('九十、最终报告格式')[0];questions=re.findall(r'^(\d+)\. (.+)$',qpart,re.M);assert len(questions)==93
answers={i:'是；已由对应 API、数据库/文件或浏览器验收验证，详见 Gate 与证据套件。' for i in range(1,94)}
answers.update({
1:'是；完整 Version History 与统一 History API/面板。',2:'是；历史接口返回全部成功 Published 版本，不受旧 publication 最近 100 条限制。',3:'是；无编辑 API，Published/Sealed DB 触发器保护。',4:'是；历史逻辑资产冻结，物理文件写入禁止覆盖。',5:'是；Immutable 写入禁止不同字节覆盖，每次验证原文与完整字段。',6:'是；只读 JSON、来源、Manifest、资产和审计详情。',7:'是；列表展开行和详情显示。',8:'是；资产详情显示 SHA-256。',9:'是；按实际原文字节复验。',10:'是；逐个实际资产 Hash/size 复验。',11:'是；全字段及确定原文字节校验。',12:'是；篡改 T10 测试 JSON 被检测。',13:'是；篡改 T10 测试资产被检测。',14:'是；Manifest 追加空格也被检测。',15:'是；无管理员强制忽略开关。',16:'是；路由权限加 Service 当前真实角色检查。',17:'是，403。',18:'是，403。',19:'是，403。',20:'是，401。',21:'是；1–1000 字纯文本，拒绝空白/HTML/危险控制字符。',22:'是；新 Revision、Record、Release、资产关系。',23:'是；保留原行、Manifest、JSON、资产。',24:'是；API 与浏览器均实际生成 V4。',25:'是；原行与字节精确比较未变。',26:'是；rollback_source_revision_id=V1，source_revision_id=V3。',27:'是；Current 指向新 V4。',28:'是；V4/V5/V6 及失败后的跳号均验证。',29:'是；共用 sealBuilt、verifyPrepared、switchAndFinalize、finalize/fail。',30:'是；operation_type=rollback、独立原因和幂等键。',31:'是；rollback_requested、failed/reconcile_required、succeeded 追加记录。',32:'是；Prepare 前及 Build/切换前验证。',33:'是；不需要私有源图，逐行复制逻辑关系并验证共享 CAS。',34:'是；注入 build 故障验证。',35:'是；注入 validation/manifest/asset 故障验证。',36:'是；rename 前故障保留旧 Current。',37:'是；新文件可能已公开，记录 recovery_required，保留 active。',38:'是；明确区分切换前与切换后失败。',39:'是；持久化 publication_health 加活动作业状态。',40:'是；DB/静态文件版本、Hash、Manifest、资产和 active 一起核对。',41:'是；其他角色 403，匿名 401。',42:'是；每次原因必填，started/completed/failed 审计。',43:'是；持相同 OS 锁重新验证，不信任状态缓存。',44:'是；同上。',45:'是；实际重启后浏览器完成原记录，Current V5 一致。',46:'是；失败/成功/待恢复 Attempt 均保留。',47:'是；驳回与多次批准记录均保留。',48:'是；业务审计按时间显示，七分类过滤及详情。',49:'是；业务分组与资产按 key 的差异。',50:'是；读取并验证不可变 Published JSON 文件。',51:'是；inspection 分组。',52:'是；custom_sections 分组。',53:'是；role、公开 filename、hash、size 及增删改。',54:'是；不从 Working Data 重算历史。',55:'是；UI busy 防重与服务端完整意图幂等。',56:'是；同批两请求只一个成功、版本唯一。',57:'是；flock/CAS 互斥；冲突允许零个成功，Current 保持一致。',58:'是；共用 OS 锁，直接持锁测试全部写操作拒绝。',59:'是；本地受控 Draft fixture 后真实提交、独立审核、正常发布 V6；正式 Published→Draft UI 未增加。',60:'是；分配后永不复用，允许失败跳号。',61:'是；Published Batch 归档保留全部历史。',62:'是；Product 归档后历史和 release 完整性仍通过。',63:'是；仅动态引用统计，不自动删除任何历史资产。',64:'是；主库和 Fresh DB 的历史/审计/资产/头/文件重启前后精确一致。',65:'是；后台/UI 全停时 140 项静态访问断言通过。',66:'是；空库正常 Publish V1/V2、Rollback V3、History/Verify/Compare 全链路。',67:'是；T9 升级、空库与重复迁移一致，原数据保留。',68:'是，ok。',69:'是，无异常。',70:'是；56 个成功、57 个 sealed JSON 全扫描。',71:'是；73 条 sealed 资产关系全部校验实际字节。',72:'是；所有 sealed Manifest 复验。',73:'是；回滚与正常发布一同全量复验。',74:'是；没有普通删除接口，实际 DELETE 请求失败。',75:'是；没有普通删除接口，冻结资产 DB 保护。',76:'是；UPDATE/DELETE 触发器拒绝，API 无修改入口。',77:'是；1 列、1 张四列表、事件 enum 与部分唯一索引调整。',78:'是；新增 1789257600000_version_history，不改既有迁移。',79:'No；T4–T9 历史 Migration 原文 Hash 不变。',80:'是；补齐实际回滚批准来源、共用链及安全恢复边界。',81:'是；T10_VERSION_AUDIT_ROLLBACK.md 和 T10_TEST_RESULTS.json。',82:'是；8 项专用 TS→Go 契约检查通过。',83:'是；上游通用 check:api 的 4 条既有问题单独记录，不计为业务 Gate 失败或伪称全绿。',84:'是；后端 upstream tracked files 未改；UI 两个原已修改的语言入口继续添加 T10 模块注册。',85:'admin/go-admin-ui/src/lang/en-US/index.ts；admin/go-admin-ui/src/lang/zh-CN/index.ts。其余新增/修改业务文件见完整清单。',86:'是；53/53 SHA-256 一致。',87:'是；7/7 未变。',88:'No；未连接业务服务器，只有 loopback 本地服务。',89:'No。',90:'No。',91:'No。',92:'No。',93:'No；T11 未开始。'})
answerrows=[{'number':int(i),'question':q,'answer':answers[int(i)]} for i,q in questions]
new=['admin/go-admin/app/passport/apis/history.go','admin/go-admin/app/passport/service/history.go','admin/go-admin/app/passport/service/history_test.go','admin/go-admin/cmd/migrate/migration/version/1789257600000_version_history.go','admin/go-admin/cmd/migrate/migration/version/1789257600000_version_history.sql','admin/go-admin-ui/src/api/passport/history.ts','admin/go-admin-ui/src/views/passport/history/HistoryPanel.vue','admin/go-admin-ui/src/lang/en-US/passport/history.ts','admin/go-admin-ui/src/lang/zh-CN/passport/history.ts']
changed=['admin/go-admin/app/admin/router/passport_publication.go','admin/go-admin/app/passport/apis/publish.go','admin/go-admin/app/passport/models/publish.go','admin/go-admin/app/passport/service/publish.go','admin/go-admin/app/passport/service/review.go','admin/go-admin-ui/src/api/passport/publication.ts','admin/go-admin-ui/src/views/passport/publication/PublishPanel.vue','admin/go-admin-ui/src/lang/en-US/index.ts','admin/go-admin-ui/src/lang/zh-CN/index.ts']
report={'stage':'T10','status':'awaiting_human_acceptance','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gates_pass':65,'gates_fail':0,'tests_pass':sum(s['pass'] for s in suites.values()),'tests_fail':0,'counting':'Named assertions and leaf Go tests, including 301 existing UI unit tests; repeated file assertions and fresh runs count separately. Not a count of unique business scenarios. Upstream generic diagnostics excluded and reported separately.','suites':suites,'gates':gates,'counts':json.loads((art/'files.json').read_text())['counts'],'new_source_files':new,'changed_source_files':changed,'answers':answerrows,'known_tooling_limitations':['Upstream check:api: 4 pre-existing T8 model-matching diagnostics; exit nonzero.','ESLint 0 errors and 30 pre-existing upstream component name warnings.','Ajv 6.15.0 supplements the fixed shared keyword subset; not a claim of full Draft 2020-12 support.'],'scope':{'server_connected':False,'caddy_changed':False,'directus_changed':False,'production_docker_changed':False,'qr_generated':False,'t11_started':False,'all_t10_services_stopped':True,'protected_historical_files':36748}}
(R/'docs/T10_TEST_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
body='''# 【T10 执行结果】

T10 状态：**等待人工验收；本地服务已停止，未进入 T11。** T0–T9 已由用户人工验收。仅在 runtime/t10 使用独立本地 SQLite、发布目录和日志，没有连接业务服务器。

**65/65 Gate PASS；TOTAL 项命名断言/叶测试 PASS，0 FAIL。** 含 301 项既有前端单测；不是 TOTAL 个独立业务场景。主库 API 75 项、Fresh API 73 项，另有真实浏览器、故障、互斥、持久化、文件/Schema 和静态访问验收。精确明细见 [T10_TEST_RESULTS.json](T10_TEST_RESULTS.json)。上游通用 check:api 仍非零退出，4 条既有诊断单独记录，不伪称所有检查命令全绿。

| 验收类别 | 结果 |
|---|---|
| Version History / Version Detail / Version Integrity | PASS |
| Audit Timeline / Review History / Publish History | PASS |
| Version Compare / Rollback / Rollback Immutability | PASS |
| Rollback Assets / Rollback Failure Safety / Reconcile | PASS |
| Concurrency / Idempotency / Permissions | PASS |
| UI / Browser E2E / Persistence / Fresh DB | PASS |
| Integrity / Baseline Protection | PASS |

## Version History 与只读详情

History API 返回全部成功 PassportRevision 及全部 PublishAttempt、ReviewAttempt、业务 Audit，不使用旧 publication Status 的最近 100 条作为完整历史。API 明确 version_type=normal_publish/rollback、current/historical。恢复沿用原操作类型与版本，在 SystemRecovery 审计中明确说明，不把已成功记录原地改名为 recovery。

列表含版本、类型/回滚源、Current、发布时间、资产数；展开行显示发布者、审核来源/Hash、Payload Hash、Release ID、Record、状态。详情显示只读 Published JSON、Manifest、完整来源、资产角色/文件名/Hash/size/引用数及关联审计。Verify 检查原始 JSON 字节、DB payload/hash、Schema、业务 Hash、整个 Manifest、资产清单/数量、逐资产 bytes/hash/size，失败返回 integrity_error，无自动历史修复或 override。

Published/Sealed Revision、PublishedAsset、Review 终态与 Audit 保持原 DB 保护。普通后台不存在 Edit/Delete Revision、Asset 或 Record API；归档不删除历史。Immutable 物理写入不覆盖冲突文件。默认永久保留，不实现 GC；引用数动态 COUNT DISTINCT Published Revision，不是容易过期的持久化计数器。

## Rollback as New Version / Source 设计

只有真实启用的 Super Admin 可以回滚。JWT → LiveIdentity → Casbin → PermissionAction → Service 再查当前 sys_user/sys_role；Editor/Reviewer/Viewer 403，匿名 401，不能只隐藏按钮。只允许同 Batch 已成功 Published 目标，Batch 本身必须 Published、无活动作业且 expected_current 相符。原因必填 1–1000 字纯文本，空白、HTML 和危险控制字符拒绝。

Prepare 在事务内创建新 PassportRevision、PublishRecord、Release UUID、逻辑身份，分配 next_version_number 并递增，设置 active，追加 rollback_requested。V3 回 V1 生成 V4：source_revision_id=V3，rollback_source_revision_id=V1。保留目标原 Review ID、FrozenInput、SourceEditVersion、SourceContentHash、ReviewedBy/At 用作批准来源链；它们不表示对当前工作集的新批准。新操作者在 PublishedBy/CreatedBy，原因在固定的 PublishRecord.rollback_reason。

实际 Build 只读目标经验证的 Published Payload 与 PublishedAsset，不从 FrozenInput、最新模板或私有原图重算。新逻辑资产行归 V4，允许复用已复验的不可变 CAS 字节；删除私有源图后回滚仍成功。publication.version_number/issued_at/kind/source_version_number 更新为新信封，因此 V4 content_hash=V1、payload_hash≠V1。V1/V2/V3 的数据库行与字节均精确不变。再次回 V2 生成 V5，受控测试 Candidate 正常发布生成 V6；失败占号保留，不为连续编号复用。

## 共用发布状态机与故障边界

```text
Prepare → building → validating → prepared → switching → published
切换前可证明失败 → failed，保留旧 Current，重试新键/新版本
已切换或未知结果 → recovery_required，保留 active，恢复原操作
```

Rollback 与正常 Publish 共用 sealBuilt、verifyPrepared、switchAndFinalize、finalize/fail。Build 分支仅负责选择批准输入或已发布源快照；两者后续同等 Schema、Hash、Immutable、fsync、Atomic Rename 与数据库确认保护。不同内容不得覆盖历史 Manifest/JSON/Asset。

“任何故障旧 Current 都不变”不成立。实际 SQLite published_at 更新失败测试证明：静态文件已成为新完整版本，DB 仍旧版本，必须 reconcile。没有将这种情况误标为安全 failed。switched_at 仍为确认观测时间，成功审计明确 reconstructed，不伪造精确切换时刻。

## Reconcile / Current Verification

publication_health 持久化最近观测，新的 Publish/Rollback 无条件在同批 flock 下重验真实 Current/DB/Manifest/资产，不只信任缓存。API 与页面对照 DB version、静态文件 version/Revision/Hash、Manifest version 和 active record。

| 分类 | 含义与处理 |
|---|---|
| failed_old_current_safe | A：失败已确认、Current 仍旧，使用新键重试 |
| file_switched_db_pending | B：新文件完整、DB 未确认；复验后 Finalize 原 Record |
| db_published_current_old | C：DB 成功但静态 head 是较旧成功版本，阻止普通写入 |
| integrity_failure | D：JSON/Manifest/资产损坏；禁止自动修复历史 |
| missing_current | 丢失 head；必须验证 DB 成功版本后显式恢复 |
| unknown_current / database_inconsistent | 无法证明安全，保持 reconciliation_required 并拒绝猜测 |
| pending/building/validating/prepared/switching/recovery_required | 根据 active Record、封版与实际文件对账，不能并行新发布 |

Reconcile 仅 admin，每次必须 reason，追加 started/completed/failed。B 恢复原 Record 与版本；未封版且确认仍旧 Current 可结束为安全失败，已封版且旧 Current 可继续原切换。C 仅在文件为经验证的更旧成功版本或缺失时，从完整有效 DB Current 恢复稳定文件；未知、比 DB 更新或已损坏文件拒绝覆盖。无自动历史修复、无强制忽略校验、无全局清理。

## Compare / Timeline

比较读取并验证不可变快照文件，按 product/batch/raw_material/process/inspection/certifications/packaging/storage/manufacturer/custom_sections/localization/publication 分组，Hash 单列；资产按 key 比较角色、公开文件名、路径、Hash、size。返回 added/removed/changed/unchanged，UI 默认折叠业务组，点击才展开两侧值。不会读取当前 Working Data 伪造旧值。

业务时间线包含批次相关审计与产品/模板/译文来源审计，按时间与 ID 排序；Product/Batch/Review/Publish/Rollback/Asset/SystemRecovery 七类过滤。Audit 详情含 entity、batch/revision、actor/time、summary、metadata、before/after 摘要与有限操作明细，不默认展示巨大内部 JSON。它不是 Go Admin HTTP 操作日志。Review 多轮与失败/成功/待恢复发布尝试完整保留。

## API / 页面 / 权限

共用前缀 `/api/v1/passport-batches/:id/publication`：

| 方法 / 路径 | 用途 | 权限 |
|---|---|---|
| GET /history?category= | 全部版本/审核/尝试/审计 | 既有可读角色与数据范围 |
| GET /versions/:rid | 只读快照/资产/Manifest/来源 | 同上 |
| GET /versions/:rid/integrity | 完整性验证，不修复 | 同上 |
| GET /compare?left=&right= | 已发布快照比较 | 同上 |
| GET /health | 真实一致性观测 | 同上 |
| POST /rollback | 带目标/预期头/幂等键/原因的新版本 | Super Admin |
| POST /reconcile | 必填 reason，恢复原操作或已知 head | Super Admin，复用 T9 权限 |

批次详情既有 PageContainer 内增加 HistoryPanel，列表用 useTable/ProTable/DateCell，中英语言包齐全。管理员回滚需选择目标、输入原因、确认；busy 与固定幂等键防重复。Viewer 无回滚操作，Editor/Reviewer 强制直接 API 同样拒绝。严重不一致时普通 Publish/Rollback 不可执行，提供状态解释和管理员 Reconcile。

新增功能菜单 PassportRollback / passport:history:rollback，API ID 9601–9606；没有增加公开网站路由、另建身份系统或放宽原 T8 角色。

## Migration / Schema

新增 `1789257600000_version_history.go/.sql`，15 次迁移；21 业务表、334 列、115 触发器。PublishRecord 增加固定 rollback_reason；新增四列 publication_health；扩展五个审计事件并原样保留旧行；Review 成功发布唯一索引限定正常发布，使保留原 Review 来源的回滚可新增。详细字段与 ERD 已更新 DATA_MODEL / DATA_MODEL_ERD。公开 Schema 仍 1.0，JSON Schema 本体未改。

T9 数据副本升级保留所有原业务字段值；空库与升级约束结构一致；重复迁移稳定。比较结构时只规范化 GORM 不稳定的外键声明顺序，不删除约束比较。所有 T4–T9 历史迁移/报告/运行证据 Hash 不变。

## 验收证据

- 主库 43 个成功 Revision、48 个 Record（5 failed）；Fresh 13 个成功 Revision/Record。共 56 成功、57 sealed JSON，73 条 sealed 资产关系（含未成功 prepared 诊断）。全部重新扫描，522 项文件/DB/基线断言 PASS。
- Rollback 注入 build、validation、manifest、asset、rename、finalize 六类故障；前五类保留旧头，最后一类进入恢复。失败后新键新版本，原历史不变。
- 并发两回滚只有一个安全成功；Publish/Rollback 争锁只允许最多一个成功。因为工作流前置条件不同，竞争中可能双方 409，属于可刷新重试的冲突，不保证每次竞争必有成功。额外持实际 OS 锁测试 Publish/Rollback/Reconcile 全部拒绝；Service 伪造 Admin 标志但真实 Editor/Reviewer/Viewer 仍 403。
- 真实 Chromium 完成 Viewer/Editor/Reviewer 历史、详情、V1/V3 比较和直接写 API 拒绝；Admin Verify、V3→V1 新 V4、回滚来源、V3/V4 比较、刷新。随后真实 SQLite Finalize 故障、停止/重启后台，再浏览器 Reconcile 成为 V5。最终 UI 1280 宽度无页面横向溢出，无未捕获 JS 异常。已修复权限指令与条件渲染在同节点造成的 Vue 更新问题。
- 实际重启前后主库/Fresh 的历史、审核、审计、PublishedAssets、Current、版本序列、JSON/Manifest 精确一致。恢复执行本身当然会追加必要审计并确认原记录。
- 后端/UI 全停后，临时 loopback 静态服务器读取全部主库生成文件/引用图片与缺失路径，140 项通过；之后也已停止。18105/18106/19536/19538 均拒绝连接。
- 53 基线文件、site 7 文件及 36,748 历史受保护文件未变。所有 orphan/invalid rollback source/duplicate version/duplicate successful transition=0，current 均指向成功 Published。integrity_check=ok、foreign_key_check 为空。

## Known Risks / 未实现边界

- Hash 是完整性证明，不是数字签名；本地同机 flock/SQLite/文件系统验收不等于生产多机、断电、磁盘耗尽或绝对隔离保证。
- 未新增正式 Published→Draft 编辑入口，后续版本链通过清楚标注的 T10-only fixture 打开工作轮次，再走真实审核与发布。Rollback 不改 Working Data；历史公开内容与原工作数据可能不同。
- History API 当前一次返回完整元数据，未做大规模历史的服务端分页/性能压测；普通 Payload 与 Audit 大内容默认折叠。未来数据量增大应加分页，不能截断不可变历史。
- 历史源的原 Review 链保留。回滚授权与原批准者不同，通过新 actor/reason/audit 明确区分；不宣称管理员重新审核了最新工作集。
- 仅 PNG/JPEG→安全 PNG；PDF/WebP 完整转换未实现，未扩大媒体项目。无 GC、无历史批量删除。
- 最早 T9 Manifest 缺少显式 version_number，仍严格匹配 snapshot_path 的版本和原有完整字节，不回写旧证据。
- 上游 check:api 保留四条 T8 既有匹配问题；本轮 8 项专用契约检查通过。ESLint 0 errors/30 既有 warnings；type-check、301 UI tests、构建通过。Ajv 6 补充固定共同关键字子集验证，并非通用 Draft 2020-12 合规宣称。

## T11 Boundary / 停止点

未改公开 site，未开发正式 /b 页面、预览/扫码 UI 或 QR；未连接 SERVER_IP，未 SSH、未改 Caddy/Directus/生产 Docker/DNS/HTTPS，未部署。T10 到此停止，等待人工验收，T11/T12 未开始。

## 新增源文件

NEW_FILES

另新增 `admin/t10/` 独立环境、测试和报告脚本；运行数据仅 `runtime/t10/`。新增本文和 T10_TEST_RESULTS.json。

## 修改文件

CHANGED_FILES

文档更新：DATA_MODEL.md、DATA_MODEL_ERD.md、PUBLISH_MODEL.md、TASKS.md。上游 tracked diff 仅两个已在前序阶段修改的 UI 语言入口，其余业务文件属于先前/本轮独立模块；未修改上游后端 tracked 文件、框架 API 检查器或锁定版本。

## 65 Gates

GATE_TABLE

## 93 项逐项回答

ANSWERS

T10 版本、审计与回滚已完成，当前已停止，等待人工验收，未进入 T11。
'''
body=body.replace('TOTAL',str(report['tests_pass'])).replace('NEW_FILES','\n'.join('- `'+p+'`' for p in new)).replace('CHANGED_FILES','\n'.join('- `'+p+'`' for p in changed)).replace('GATE_TABLE','| # | Gate | 结果 | 证据套件 |\n|---|---|---|---|\n'+'\n'.join(f"| {g['number']} | {g['name']} | PASS | {', '.join(g['evidence_suites'])} |" for g in gates)).replace('ANSWERS','\n\n'.join(f"{a['number']}. **{a['question']}** {a['answer']}" for a in answerrows))
(R/'docs/T10_VERSION_AUDIT_ROLLBACK.md').write_text(body)
print(report['tests_pass'],'PASS; 65 Gates; 93 answers')
