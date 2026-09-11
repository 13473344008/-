from pathlib import Path
import json,re,hashlib,sqlite3
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t9';e=rt/'test-artifacts';suites={}
for name,file in [('api','api-initial.json'),('fresh_api','../fresh/test-artifacts/api-fresh.json'),('edges','edges.json'),('rich','rich.json'),('migrations','migrations.json'),('contracts','contracts.json'),('persistence','persistence.json'),('post_restart','post-restart.json'),('browser','browser-tests.json'),('ui_smoke','ui-smoke.json'),('files','files.json'),('independent_schema','independent-schema.json'),('static_backend_off','static-independent.json'),('stopped','stopped.json')]:
 p=(rt/'fresh/test-artifacts/api-fresh.json') if name=='fresh_api' else e/file
 d=json.loads(p.read_text());checks=d if isinstance(d,list) else d['checks'];suites[name]={'evidence':str(p.relative_to(R)),'checks':checks,'pass':sum(x['status']=='PASS' for x in checks),'fail':sum(x['status']!='PASS' for x in checks)}
for name,file in [('publishing_unit_race','unit-tests.jsonl'),('faults','fault-tests.jsonl'),('fresh_faults','fresh-fault-tests.jsonl'),('t5_t6_t7_regression','regression-tests.jsonl')]:
 rows=[json.loads(l) for l in (e/file).read_text().splitlines()];terminal={x['Test']:x['Action'] for x in rows if x.get('Test') and x['Action'] in ('pass','fail','skip')};leaves={k:v for k,v in terminal.items() if not any(other.startswith(k+'/') for other in terminal)};checks=[{'name':k,'status':v.upper()} for k,v in leaves.items()];suites[name]={'evidence':str((e/file).relative_to(R)),'checks':checks,'pass':sum(v=='pass' for v in leaves.values()),'fail':sum(v!='pass' for v in leaves.values())};assert any(x['Action']=='pass' and 'Test' not in x for x in rows),name
assert 'Tests  301 passed' in (rt/'logs/ui-unit.log').read_text();suites['ui_upstream_unit']={'evidence':'runtime/t9/logs/ui-unit.log','pass':301,'fail':0,'checks':[]}
assert all(v['fail']==0 for v in suites.values()),suites
request=Path('/Users/lostar/.codex/attachments/b5263e7a-0cd0-40c0-82b1-85e86051d53f/pasted-text.txt').read_text();part=request.split('九十一、T9 必过 Gate')[1].split('必须：')[0];names=re.findall(r'Gate (\d+)：\s*([^\n]+)',part);assert len(names)==60
mapping={**{i:['api'] for i in [1,2,3,4,5,7,8,9,11,12,13,15,16,17,19,20,21,26,27,33,34,35,36,37,38,39,40,41,42,43,44,45]},6:['publishing_unit_race','contracts'],10:['publishing_unit_race','files'],14:['faults','fresh_faults'],18:['publishing_unit_race','edges'],22:['rich','publishing_unit_race'],23:['files'],24:['files'],25:['publishing_unit_race','faults','independent_schema'],28:['faults','files'],29:['faults','edges'],30:['faults'],31:['faults'],32:['faults'],46:['publishing_unit_race','static_backend_off'],47:['publishing_unit_race','edges'],48:['persistence','post_restart'],49:['fresh_api','fresh_faults'],50:['migrations'],51:['files'],52:['files'],53:['files'],54:['files'],55:['files'],56:['files'],57:['files'],58:['files'],59:['local_scope'],60:['local_scope']}
gates=[{'gate':int(n),'requirement':title,'status':'PASS','evidence_suites':mapping[int(n)]} for n,title in names]
before=json.loads((e/'source-before.json').read_text());candidates=set(before)
for folder in ['admin/go-admin/app/passport','admin/go-admin/app/admin/router','admin/go-admin-ui/src/api/passport','admin/go-admin-ui/src/views/passport','admin/go-admin-ui/src/lang/en-US/passport','admin/go-admin-ui/src/lang/zh-CN/passport']:
 candidates.update(str(p.relative_to(R)) for p in (R/folder).rglob('*') if p.is_file())
candidates.update(['admin/go-admin/cmd/migrate/migration/version/1789171200000_publish_engine.go','admin/go-admin/cmd/migrate/migration/version/1789171200000_publish_engine.sql'])
changed=[p for p,h in before.items() if (R/p).exists() and hashlib.sha256((R/p).read_bytes()).hexdigest()!=h];new=[p for p in candidates if p not in before and (R/p).is_file()]
# Before inventory intentionally covers all existing business router files, but not unrelated upstream routes.
new=[p for p in new if '/app/admin/router/' not in p or p.endswith('/passport_publication.go')]
counts=json.loads((e/'files.json').read_text())['counts'];total=sum(v['pass'] for v in suites.values());out={'stage':'T9','status':'awaiting_human_acceptance','date':'2026-09-10','gates_pass':60,'gates_fail':0,'tests_pass':total,'tests_fail':0,'counting':'Named assertions and leaf Go tests; UI unit test count separate; container Go tests excluded. Repeated byte checks are reported as file assertions.','suites':suites,'gates':gates,'counts':counts,'changed_source_files':sorted(changed),'new_source_files':sorted(new),'local_scope':{'server_connection':False,'caddy_changed':False,'directus_changed':False,'production_docker_changed':False,'production_qr_generated':False,'t10_started':False,'t11_started':False,'method':'Reviewed task execution scope; all service endpoints bound to localhost.'},'known_tooling_limitations':[{'check':'upstream pnpm check:api','status':'KNOWN_BASELINE_LIMITATION','errors':4,'reason':'Upstream heuristic does not resolve app/passport and its custom DTOs; same four T8 findings. T9 business-specific contracts pass.','evidence':'runtime/t9/logs/upstream-api-contract.log'},{'check':'pnpm lint','errors':0,'warnings':30,'reason':'Existing upstream component-name warnings'}],'implementation_limits':['PNG/JPEG normalized to PNG only; WebP/PDF/certification management not opened','Local runtime only; no production resource/durability certification','Explicit reconcile and manual retained-tmp cleanup; no automatic orphan deletion','switched_at is confirmation observation, audit marks reconstructed','Manifest version is encoded in snapshot_path; newer local test manifests also have explicit version_number','Full T10 Published-to-Draft/version compare/rollback and T11 public pages/QR are excluded'],'all_local_services_stopped':True}
(R/'docs/T9_TEST_RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('Gates 60/60; named checks',total,'PASS, 0 FAIL; new',len(new),'changed',len(changed));print(json.dumps(counts));
answers=[
'是，仅当前已批准、未锁定的 ready_for_publish；服务端重验全部关联。','是，409。','是，409。','是，只读冻结 Approved Candidate；不读最新工作数据生成内容。','是，重算候选原字节 SHA-256 并比较所有提交元数据。','是，独立 publishing.Build。','是，公开字段显式映射，ORM 模型不直接序列化到公开 JSON。','是，闭合 DTO 映射及 additionalProperties:false 校验。','是，内部备注、ID、存储键及未公开数据通过字节扫描验证无泄漏。','是。','1.0；未改变公开结构。','是，固定编码和排序，含 Unicode/转义测试向量。','是，重读实际落盘字节计算。','是，SHA-256。','是，真实创建并由 DB/文件/UI 验证。','是，既有 batch_id + version_number UNIQUE 保留。','是，发布后修订、关联资产、成功记录由 DB 触发器冻结。','是，V2/V3 使用新路径，V1 原字节保留。','是，规范化后的 PNG 内容寻址副本，不链接私有原图。','是，替换/删除私有源图不改变已发布副本。','是，PublishedAsset.sha256。','是，规范化输出冻结前后相同；另记录原图 source_asset_sha256。','是，当前 PNG/JPEG 源图；输出 PNG，其他类型 fail closed。','是，单源/输出 2 MiB，16 关联，宽高 4096/1600 万像素，候选总计 4 MiB。','是，双重公开资格和公开所有者过滤。','是。','是。','是。','是，私有 releases/manifests 下。','是，版本由 snapshot_path 的 vN 表达，新构建同时有 version_number；清单含三个 Hash 及完整关联。','是，私有 tmp/<record_id> 写入并 fsync。','是，Schema、语义、文件、资产及 Manifest 校验后切换。','是，同文件系统完整文件 Rename 原子替换唯一 Current。','是，切换前故障旧 Current 字节不变。','是，含第 1/第 2 张图片故障与旧版本验证。','是。','是，rename 前故障旧 Current 不变；rename 后故障进入待对账，不能笼统称旧 Current 不变。','是，终态失败记录不可删除。','是，关联审核、修订、资产、Hash、发布人、时间、审计完整。','是，最终 DB 事务确认成功才设置 Published/current。','是，切换前失败保留原批准。','是，切换前失败可重试；待对账必须先恢复原操作。','是，新幂等键创建新尝试并分配新版本号；旧号不复用。','是，新增成功修订部分唯一索引。','是，OS 每批次锁 + DB 活动记录/唯一约束。','是，跨批次并发构建，SQLite 短事务写入仍串行。','是，前端 busy、幂等键、后端互斥同时保护。','是。','是，403。','是，当前 Reviewer 策略为 403。','是，403。','是，401。','是，编码白名单、固定生成路径及 os.Root 限定访问。','是，根与组件符号链接拒绝；真实越界源图验证失败。','是，本地根由验收用户控制，私有目录/文件受限，公开文件 0644，无任意上传或执行入口。','是，显式 Admin reconcile，持锁根据新/旧/未知 Current Hash 对账。','是，保留私有 tmp；仅经 DB 状态/引用/锁和保留期核对后手动清理，不删除历史成功版本或共享 CAS。','是，实际停止并重启后的业务行及文件逐项一致。','是，空库迁移后角色、产品、版本、模块、批次、检测、审核、发布全链路通过。','是。','是，无异常。','是，所有已封版 JSON 共 50 份（其中成功 48 份）实际字节复验一致。','是，PublishedAsset 表中全部 45 行所指字节复验一致（含 2 个失败 prepared 修订的诊断资产行）。','是，DB、清单、JSON 引用和落盘文件一致。','是，增加两列审核来源关联及约束。','是，仅新增 1789171200000_publish_engine.go/.sql。','No；T4–T8 历史迁移未修改。','是，追加 T9 实施、原子切换、恢复与清理边界。','公开 Schema JSON 未改；补充固定编码、校验器和本轮资产子集说明。','是，仅既有的两个 UI locale 总入口；后端 tracked 文件无改动。','admin/go-admin-ui/src/lang/en-US/index.ts 与 src/lang/zh-CN/index.ts；本轮增加 publication 导入和注册。','是，53/53 一致。','是，7/7 未变。','No。','No。','No。','No。','No。','No；也未进入 T11。']
assert len(answers)==79
out['answers']=[{'number':i+1,'answer':a} for i,a in enumerate(answers)];(R/'docs/T9_TEST_RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
newlist='\n'.join('- `'+p+'`' for p in out['new_source_files']);changes='\n'.join('- `'+p+'`' for p in out['changed_source_files']);suite_table='\n'.join('| '+k+' | '+str(v['pass'])+' | '+str(v['fail'])+' | `'+v['evidence']+'` |' for k,v in suites.items());gate_table='\n'.join(f'| {g["gate"]} | {g["requirement"]} | PASS | '+', '.join(g['evidence_suites'])+' |' for g in gates)
report=f'''# T9 静态 Published JSON 与 Published Assets 发布引擎

日期：2026-09-10。状态：**等待人工验收；已停止，未进入 T10/T11。** 用户已明确验收 T0–T8。本轮只操作独立本地 T9 目录，没有连接业务服务器。

## T9 执行结果

**60/60 Gate PASS；{total} 个命名断言/叶测试 PASS，0 FAIL。** 包含逐文件字节断言与 301 个既有 UI 单测；Go 父级测试容器不重复计数。不是 {total} 个独立业务场景。明细及证据位置见 [T9_TEST_RESULTS.json](T9_TEST_RESULTS.json)。

| 项目 | 结果 |
|---|---|
| Publish Preconditions / Approved Candidate Source | PASS |
| Public Payload Builder / Whitelist | PASS |
| Canonical JSON / Payload Hash | PASS |
| Passport Revision / Published Assets | PASS |
| Release Manifest / Release Validation | PASS |
| Atomic Publish / Failure Recovery | PASS |
| Concurrency / Idempotency / Permissions | PASS |
| UI / Browser E2E | PASS |
| Persistence / Fresh DB / Integrity | PASS |
| Baseline Protection | PASS |

**事实边界：**“任何一步失败，旧 Current 都不变”过于绝对。rename 前失败保留旧 Current；rename 已成功而 DB 确认失败时，静态 Current 可能已是完整新快照，旧历史快照仍可用，DB 进入 recovery_required，必须对账原操作。验收包含真实 SQLite 最终事务失败和这条恢复路径。

上游通用 `pnpm check:api` 仍报 T8 已存在的 4 条匹配错误（扫描器不识别 app/passport/自定义 DTO，甚至匹配到 demo_product.go）；不是全部检查命令均零失败。本轮新增 API 使用专门 TS→Go 契约检查，4/4 PASS。Lint 0 error、30 条既有上游组件命名 warning；type-check、UI 301 单测、i18n 检查和生产构建成功。没有屏蔽或篡改上游检查器。

## 实际运行结果

主验收库：28 个成功 PassportRevision、39 条 PublishRecord（11 failed）；Fresh 库：20 个成功修订、27 条 PublishRecord（7 failed）。合计 **48 个成功修订**；另有 2 个已封版但切换前失败的 prepared 诊断修订，故逐文件扫描 50 份不可变版本 JSON。PublishedAsset 表共 45 行，包括这两个未成功修订的资产行；全部字节/元数据复验一致，没有悬空外键或未决发布。

每库业务结构均为 20 表、329 列、113 触发器、14 次迁移。版本号允许因失败出现间隔；成功记录不因后来被新版本替代而改状态。

## 代码与边界

Handler 只绑定请求与返回结果；Service 从本次请求的 Orm 验证权限、事务、冻结关联并协调发布；独立 `publishing` 包不接收 Orm 或 Gin。公开 Builder 只输入审核冻结 JSON、签发时间和分配的版本号。

新建审核为 `review-v2 / internal-review-v2`；旧 `review-v1` 冻结记录不改，资产为空时仍兼容。公开 `schema_version` 仍为 `1.0`，Builder 为 `public-json-v1.0.0`。没有开放上传/媒体管理或认证管理；测试图通过既有 MediaAsset/AssetLink 在 Draft 阶段作为受控 fixture 挂接，Submit/Approve 仍是真实流程。

### 新增业务源文件

{newlist}

### 修改已有业务源文件

{changes}

另新增 `admin/t9/` 的独立 setup/env、API/浏览器/故障/迁移/回归/文件/静态验收脚本和报告生成器；运行数据全部在 `runtime/t9/`。新增本文和 `T9_TEST_RESULTS.json`，更新 `TASKS.md`、`PUBLISH_MODEL.md`、`DATA_MODEL.md`、`DATA_MODEL_ERD.md`、`PUBLIC_PAYLOAD_SCHEMA.md`。没有重写 T4–T8 历史报告/数据库/迁移。

### Migration / Schema

新迁移 `1789171200000_publish_engine` 为 PassportRevision/PublishRecord 各加 `source_review_record_id` 外键，固定已批准来源；新增部分唯一索引保证每个审核最多一个成功修订，4 个触发器固定关联与记录身份。历史 NULL 兼容，新插入必须满足审核关联。T8 升级保留全部原有业务字段值，重复迁移安全；Fresh 从零迁移与升级库完整约束一致。上游 GORM 的外键声明顺序会变，测试规范化声明顺序后比较，未删除外键比较。

## Public Payload 实际结构

```text
schema_version, record_type, notice
product {{code,name,category_code,country_of_origin}}
batch {{code,production_date,expiry_date,quality_status}}
raw_material {{name,type,origin,description}}
process[], inspection[], certifications[]
packaging, storage, manufacturer
custom_sections[] {{key,type,title,content,asset_keys}}
assets[] {{key,role,label,path,mime_type,file_size,sha256}}
localization {{source_language,available_languages,translations}}
publication {{version_number,issued_at,kind,source_version_number}}
```

TEST 记录明确使用 TEST 编码和醒目 notice。未伪造真实认证。私有备注、用户/内部 UUID、私有路径、工作状态和未确认译文不进入公开 DTO。已确认语言缺失字段按源语言回退；override clear 在每种语言均保持 null/空集合，不回退模板。已验证精确检测小数、稳定排序、text/key_value/table、图片模块、私有/隐藏过滤及中文/阿拉伯文。

公开 Schema 本体不改。生产校验器实现该固定契约用到的全部关键字并有闭合词汇测试，外加跨字段语义校验；不接受外部 Schema。独立补充校验使用已有 Ajv 6.15.0 的共同关键字子集，只去掉校验副本的 dialect 标记，保留全部字段约束，并非声称 Ajv 6 支持通用 Draft 2020-12。

## Canonical / Hash

固定 UTF-8、无 BOM、无尾换行、对象键按 Unicode 码点排序、无多余空白；保留已验证数组顺序。小数使用规范字符串，去前导/末尾零及负零；整数限制 JS 安全范围。字符串使用固定 Go 转义（U+2028/U+2029 转义），另对业务文字做纯文本校验。不是通用 RFC 8785 实现。

`payload_hash = SHA256(实际最终 JSON bytes)`；`content_hash = SHA256(去掉 publication 后的相同规范编码)`；`asset_manifest_hash = SHA256(按 key 排序的公开 assets 清单规范字节)`。不在 Payload 内自引用其自身 Hash。Hash 证明内容一致，**不是数字签名或来源真实性认证**。

## Published Assets

```text
assets/sha256/<hash前2位>/<完整SHA256>.png
```

审核前读取受限私有原图，校验原字节大小/Hash，解码 PNG/JPEG 后重编码为去元数据 PNG；冻结规范化字节、预览和摘要。发布再次验证原文件、当前可用/公开资格、转换版本和已批准规范化字节，落盘后重读复核。规范化 Hash 前后相同；原图因去元数据可与输出 Hash 不同，另存 `source_asset_sha256`，不混淆这两个域。

当前单源/输出 2 MiB、16 关联、宽高各 4096、总像素不超过 1600 万，审核总 4 MiB，公开 JSON 1 MiB。PNG/JPEG 转 PNG；WebP/PDF 尚无安全转换器，拒绝发布而不假装已支持。原始文件名只留私有记录，恶意 `../../...` 名称不影响公开路径。源图替换、删除、越界 symlink 均不改变历史公开字节。

本地公开根由验收用户控制（0700），公开文件 0644；私有根 0700、私有文件 0600。正式部署需按独立服务用户/只读静态挂载确认权限，不将本地权限数字直接宣称为生产配置。

## Publish State Machine / Atomic Switch

```text
pending → building → validating → prepared → switching → published
切换前错误 → failed → 使用新键创建新尝试
切换后或未知结果 → recovery_required → 原操作 reconcile
```

每批次实际 OS flock + DB 活动记录/唯一约束；不同批次在短 SQLite 事务之外并发构建。先 Prepare 事务分配身份/版本并绑定审核，随后写私有临时 release、验证资产与完整 JSON，再封版。不可变文件用 Write→Sync→Close→无覆盖 Link→目录 Sync，已存在路径必须字节匹配。

私有 Manifest 包含 release/record/revision/review、snapshot_path、Payload/Content/Asset Manifest Hash、资产数、Schema/Builder。版本编码在 `snapshot_path` 的 `/vN.json`；后续本地构建也有显式 version_number。旧测试清单没有被事后改写。

Switch 前重读清单、快照及每张资产，并与 DB/JSON 引用复核，确认静态 Current 等于 expected_current；先落 DB switching，再在稳定 Current 同目录写完整临时文件、fsync、Rename 原子替换、目录 fsync。读者压力测试只读到完整旧/新文件。

最后一个 DB 事务按约束要求依次完成 Revision.published_at、Record.published、Batch.current/workflow、清 active 和成功审计。`switched_at` 是确认时观测值，审计带 reconstructed 标记，不编造精确替换时刻。

### Crash Recovery / Retry

Admin 的 reconcile 先取得同批次 OS 锁：Current 为新 Hash 则复验并完成原记录；为旧 Hash 且 prepared 完整则继续原切换；未封版且证实 Current 仍旧则失败；未知/损坏则保留待对账。拒绝超时抢占仍持锁的进程。失败重试保留原失败记录并分配新号；同键完全同请求返回原结果，不同审核/Hash/expected_current 冲突；同审核最多一个成功版本。

### Tmp Cleanup

本轮采用明确手动保留策略，无自动删除。建议至少保留 7 天，先扫描 DB 非终态与 tmp/Manifest 的对应关系；只有已 failed、非 active、无 Current 引用且在同批次锁内确认的**私有 tmp** 才可按精确记录目录清理。孤立清单/快照先出诊断报告，不删除成功历史或共享 CAS，不凭 mtime 判定无引用。完成校验的版本文件可在切换前就位，失败 prepared 文件仍保留但不成为 Current；versions 不是访问控制边界，其内容仍只含已批准公开字段。

## API / 页面 / 权限

| 方法 | 路径 | 权限 |
|---|---|---|
| GET | `/api/v1/passport-batches/:id/publication` | 现有读取角色 + 数据权限 |
| POST | 同上 | 仅当前有效 Super Admin |
| POST | `.../publication/reconcile` | 仅当前有效 Super Admin |

请求绑定严格拒绝未知字段/客户端自带 Payload。继承 JWT、LiveIdentity、Casbin、PermissionAction，服务另查当前用户/角色有效性；Editor/Reviewer/Viewer 403、匿名 401。

Batch/Review Detail 内新增 PublishPanel：候选 Hash、确认、Publishing、成功版本/Hash/资产数/发布人/时间、发布尝试表、失败重试和待对账入口。审核面板显示已冻结规范化图片；无公开页面、正式 URL 或 QR 按钮。截图：[最终发布面板](../runtime/t9/test-artifacts/publication-panel-final.png)。

## 自动、浏览器、故障及并发证据

| 套件 | PASS | FAIL | 证据 |
|---|---:|---:|---|
{suite_table}

真实浏览器明确点击退出并切换角色：Editor 建模板/封版/批次、提交含已冻结图片的候选；Reviewer 查看图片并批准；Editor/Reviewer 通过浏览器请求发布得 403；Admin 确认、观察 Publishing、V1/Hash/资产数并刷新。缺失资产的下一尝试显示失败、旧 V1 不变，可修复后明确重试成为 V3。无未捕获 JS 错误，修复并核对已发布译文，无页面横向溢出。

故障含 build、write、copy:1、copy:2、validation、rename、finalize；主库和 Fresh 均验证旧 V1 不被覆盖。另通过真实 SQLite 触发器使最后事务失败，确认静态已新/DB 仍旧→recovery_required→同记录完成，无重复成功修订。同批次 5 请求只一次成功，不同 3 批次并行成功。

实际停止并重启两个后端核对持久化；最终所有后端/UI 停止，仅启动无 DB/后端逻辑的本地静态服务器，95 项 HTTP 检查复核全部主库公开文件、引用图片、MIME 与缺失/越界 404。最后静态服务器也停止，18103/18104/19534/19535/19536 均 ECONNREFUSED。

## 60 Gate

| Gate | 要求 | 结果 | 证据套件 |
|---:|---|---|---|
{gate_table}

`local_scope` 是本次操作范围核对：没有 SSH/服务器连接，没有 Caddy、Directus、生产 Docker、DNS、正式 QR 操作，也未进入 T10/T11；不将其包装成探测生产服务器的自动测试。

## 已知风险与未验证项

- 仅在本地 macOS 文件系统/SQLite 做了真实验证；Linux 部署、断电/磁盘控制器持久性、容量/并发负载仍需部署阶段实测，不承诺绝对故障隔离。
- SQLite 写事务仍串行；每张图片虽有上限，跨批次并行总内存/CPU 仍需生产资源预算，当前不声称已有生产限额。
- 无完整媒体上传管理、PDF/WebP 安全转换、认证编辑；这些输入继续 fail closed。公开 Hash 不等于真实性背书。
- 恢复依赖显式 reconcile；清理采用手动保留策略，没有自动删除历史资源。错误或未知 Current 需人工对账，不能强行覆盖。
- T10 的正式 Published→Draft、版本比较/回滚、T11 的公开页面/预览/QR 均未实现。本轮 V2 fixture 仅用于验收发布引擎，不是正式业务入口。

## 79 项逐项答复

'''+ '\n'.join(f'{i+1}. {a}' for i,a in enumerate(answers))+'''

T9 静态 Published JSON 与 Published Assets 发布引擎已完成，当前已停止，等待人工验收，未进入 T10。
'''
(R/'docs/T9_PUBLISH_ENGINE.md').write_text(report)
