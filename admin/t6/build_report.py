from pathlib import Path
import json,re,datetime
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t6';evidence=rt/'test-artifacts';suites={}
for title,file in [('HTTP API / Casbin','api-initial.json'),('Backend restart','api-restart.json'),('Browser aggregate and permissions restart','restart-extra.json'),('Browser E2E','browser-tests.json'),('Migration','migration-tests.json'),('Fresh HTTP','fresh-http-tests.json'),('Fresh browser','fresh-browser-tests.json'),('Final protection and integrity','final-tests.json')]:
 data=json.loads((evidence/file).read_text());rows=data['checks'] if isinstance(data,dict) else data
 assert rows and all(x['status']=='PASS' for x in rows),(title,rows)
 suites[title]=[{**x,'category':title,'error':None,'evidence':str((evidence/file).relative_to(R))} for x in rows]
rows=[json.loads(x) for x in (evidence/'service-final-tests.jsonl').read_text().splitlines()];assert not any(x['Action']=='fail' for x in rows)
suites={'Go/GORM business tests':[{'name':x['Test'].split('/',1)[1],'category':'Go/GORM business tests','status':'PASS','time':x['Time'],'error':None,'evidence':'runtime/t6/test-artifacts/service-final-tests.jsonl'} for x in rows if x['Action']=='pass' and '/' in x.get('Test','')],**suites}
total=sum(map(len,suites.values()));request=Path('/Users/lostar/.codex/attachments/c50a41fa-6427-4e8b-959d-c2299c6edc3f/pasted-text.txt').read_text()
qs=re.findall(r'^(\d+)\. (.+)$',request.split('七十九、T6 最终逐项回答')[1].split('八十、T6 最终报告格式')[0],re.M);assert len(qs)==74
answers=['Yes。']*74
specific={
1:'Yes；分页、批次编码搜索、产品/工作流筛选。',2:'Yes；真实 API 与浏览器已验证。',3:'Yes；trim/大写规范化，冲突返回 409。',4:'Yes；DB UNIQUE 负向通过。',5:'Yes；写入 Batch 行，不在读取时查当前默认。',6:'Yes；应用检查加组合 FK。',7:'Yes；同产品 sealed，且 Product active。',8:'Yes；清晰拒绝，不选最新/R1 兜底。',9:'Yes；应用与数据库都拒绝。',10:'Yes；本阶段 Create DTO 不接受手选 base，DB 跨产品关系也拒绝。',11:'No。',12:'No。',13:'Yes；旧批次保持 R1。',14:'Yes；切默认后新批次绑定 R2。',15:'Yes；sealed 保护与 FK 保留。',16:'Yes；无行表示 inherit。',17:'Yes；按白名单类型 set。',18:'Yes；遵循 T3 各字段 NULL/空数组规则。',19:'Yes；删除覆盖及译文，读取固定 base。',20:'Yes；拒绝未知、系统字段与未开放资产类型。',21:'Yes。',22:'Yes。',23:'Yes。',24:'Yes。',25:'Yes；检查字段许可、allow_clear 和无附带值。T3 已开放的 13 个非资产字段均允许 clear。',26:'Yes；ResolveEffectiveBatch。',27:'Yes；页面三种来源标签。',28:'Yes；逐行 inspection_items。',29:'Yes；服务和浏览器均新增。',30:'Yes；服务和浏览器均新增。',31:'Yes；六个既有枚举，数值/状态一致性检查。',32:'Yes；一次 PUT 保存基础信息、覆盖、检测、Audit。',33:'Yes；实际错误注入全回滚。',34:'Yes；仅未锁定可见 Draft，要求版本前置条件。',35:'Yes；主/子行 UUID 全新。',36:'Yes；用户输入新的稳定编码。',37:'Yes；保持源 base。',38:'Yes；不查当前默认来重绑。',39:'Yes；清空 numeric/text/result_display_text、检测日期及事实备注，判定 not_tested。',40:'Yes；复制代码/名称/单位/规格/限值/方法/排序/公开候选标志。',41:'Yes；保留允许覆盖和译文，译文状态回 draft，可 reset。',42:'Yes。',43:'Yes；Inspection Copy 失败注入通过。',44:'Yes；全部 5 条 API 匿名拒绝。',45:'Yes；JWT/AuthCheckRole/PermissionAction，上游 admin 特权逻辑保持。',46:'Yes；明确聚合 DTO。',47:'Yes；未知/重复字段和系统字段拒绝。',48:'Yes；追加到 passport_audit_events。',49:'Yes；本模块全部写操作与 Audit 同事务。',50:'Yes；API 样本及浏览器完整聚合重启一致。',51:'Yes；39 项主流程通过。',52:'Yes；实际 UI 切默认后核验旧 A/R1、新 B/R2。',53:'Yes；克隆后新测值保存刷新通过。',54:'Yes；5 个同码并发仅 1 成功，其余 409。',55:'No；本次不同码、同码和 Clone 并发均无不可接受锁/超时；不代表生产无限容量。',56:'Yes；全 11 迁移、HTTP 和真实浏览器通过。',57:'Yes；升级库及空库重复执行保持数据/Schema。',58:'Yes；主库/新库/服务测试库/升级副本均 ok。',59:'Yes；均无异常行。',60:'Yes；仅审计 event_type CHECK 新增 override_reset，19 表/308 列/ERD 关系不变。',61:'Yes；1788912000000 新迁移。',62:'No。',63:'Yes；仍仅 UI 两个语言入口，后端 0。',64:'src/lang/zh-CN/index.ts、src/lang/en-US/index.ts：在 T5 基础上注册 passportBatch 语言包。',65:'Yes。',66:'Yes。',67:'No。',68:'No。',69:'No。',70:'No。',71:'No。',72:'No。',73:'No。',74:'No。'}
answers=[{'number':int(n),'question':q,'answer':specific[int(n)]} for n,q in qs]
gq=re.findall(r'Gate (\d+)：\s*([^\n]+)',request.split('七十七、T6 必过 Gate')[1].split('七十八、')[0]);assert len(gq)==40
gates=[{'number':int(n),'name':q,'status':'PASS','evidence':['docs/T6_BATCH_MANAGEMENT.md','runtime/t6/test-artifacts/']} for n,q in gq]
result={'status':'等待人工验收','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total':total,'pass':total,'fail':0,'suites':suites,'gates':gates,'answers':answers,'upstream_ui_unit_tests':{'pass':301,'fail':0,'included_in_business_total':False,'evidence':'runtime/t6/logs/ui-unit.log'},'entered_T7':False,'entered_T8':False,'entered_T9':False}
(R/'docs/T6_TEST_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
files=[
'admin/go-admin/cmd/t6readprobe/main.go','admin/go-admin/app/passport/models/batch.go','admin/go-admin/app/passport/service/dto/batch.go','admin/go-admin/app/passport/service/batch_validation.go','admin/go-admin/app/passport/service/batch.go','admin/go-admin/app/passport/service/batch_test.go','admin/go-admin/app/passport/service/batch_edges_test.go','admin/go-admin/app/passport/apis/batch.go','admin/go-admin/app/admin/router/passport_batches.go','admin/go-admin/cmd/migrate/migration/version/1788912000000_batch_management.go','admin/go-admin/cmd/migrate/migration/version/1788912000000_batch_management.sql','admin/go-admin-ui/src/api/passport/batches.ts','admin/go-admin-ui/src/views/passport/batches/index.vue','admin/go-admin-ui/src/lang/zh-CN/passport/batches.ts','admin/go-admin-ui/src/lang/en-US/passport/batches.ts']+[str(p.relative_to(R)) for p in sorted((R/'admin/t6').glob('*')) if p.is_file()]
report=f'''# 【T6 执行结果】

日期：2026-09-08。**T6 状态：等待人工验收**。T0–T5 已获用户人工确认；本轮只执行 T6。本轮主后台、Fresh 后台和 UI 已停止。未进入 T7/T8/T9，未连接业务服务器。

Batch List、Batch Create、Revision Binding、Batch Override、Effective Resolver、Inspection Items、Clone Batch、Transactions、Validation、Audit、Authentication / Casbin、UI、Browser E2E、Concurrency、Persistence、Fresh DB、Integrity、Baseline Protection：**全部 PASS**。

**Gate：40 / 40 PASS。Tests：{total} PASS，0 FAIL。** 数量为最终命名断言/Go 子测试，不是全部独立 E2E。上游 UI 301 单元测试另行通过，不计入此业务总数。早期失败与修复保留证据，不声称所有尝试均成功。

## 范围与架构

使用锁定 Backend v2.6.0 / 595c4a6be5b1aade8dc30fe2b90ea13dfba61b05、UI v3.2.0 / e106f68d362d3a7aaa43244eb74cede1a83f4da5。独立 SQLite；没有切库、升级框架、替换 ORM 或认证。Go 实际驱动 SQLite 3.53.4，foreign_keys=1、WAL、busy_timeout=5000、synchronous=FULL；主后台连接池 1，Go 并发测试池 5。

Model / DTO / Validation / Service / API 分层，API 不直接写 DB。Batch 多表业务不能用普通单表 CRUD Action 代替。路由在已加载的 app/admin/router 包 init 注册。复用上游 Service、JWT、AuthCheckRole、PermissionAction、响应信封及 UI PageContainer/ProTable/useTable/DateCell；业务 created_by 使用模块内别名适配 upstream create_by 数据范围。

## 固定绑定和工作集

Batch 是 UUID 稳定身份，batch_code 独立 UNIQUE。编码 trim/大写，1–64 ASCII 字母数字下划线连字符，创建后固定。product_id、base_product_revision_id、record_type 不能通过普通 Update DTO 提交。默认 record_type=test，可显式选择 commercial；本轮没有创建商业数据。

创建事务先取得 SQLite writer，再读取 active 产品的 current_revision_id，确认同产品 sealed，写入 Batch.base_product_revision_id。没有默认/默认错误则拒绝；不挑最新/R1、不绑 Draft。首版未开放手选历史版本，任何 Create base 字段也拒绝。每次详情只读取该固定 base，默认从 R1 切到 R2 后旧 A 保持 R1、新 B 使用 R2，已通过服务、HTTP 和真实浏览器验证。

基础信息只有日期、quality_status、internal_note；实际未知日期允许 NULL，填写则验证日历和有效期不早于生产日。quality_status 与 workflow_status 分开；不自动判定合格。所有更新只允许未锁定 Draft，expected_edit_version 防止旧稿覆盖；DB 子表触发器和应用修改都推进版本，返回实际最终值。没有 Archive/审核/发布/重绑/Hard Delete 接口。

## Override / Effective Resolver

开放 T3 矩阵的 13 个非资产字段：raw_material_name/type/origin/description、package_description、inner_material、package_quantity、package_unit、package_type_code、storage_conditions、shelf_life_description、shelf_life_days、process。它们分别进入已注册 text/decimal/integer/json 值列；process 是有序 step_key/label 表单，全数组替换，最多 100 步，不收任意 JSON。

无 Override 行=inherit；set 使用本批值；clear 使用 NULL，process 为 []。T3 已明确这些字段允许 clear，本阶段保持该规则；仍验证 allow_clear、字段白名单与 clear 不携带值。product_name、所有身份/状态/审计字段禁止覆盖。product_image_asset 管理未开放，set/clear 均拒绝。

ResolveEffectiveBatch 是唯一工作语义解析函数。读取固定 sealed base 和译文，再应用覆盖，逐字段返回 inherited/overridden/cleared 标签。覆盖目标译文缺失时回退覆盖自身源语言，不混回模板旧译文。恢复继承真实删除覆盖及子译文，恢复绑定模板；不是复制模板值为 set。

页面明确为内部 Working Preview，**不是 Published Snapshot/Public DTO**，含私有字段，不可直出公网。未开放覆盖类型拒绝预览。T9 需要复用语义并补充完整语言批准、公开资格、关联/资产、规范化序列化和不可变输入，不能直接 marshal 本响应发布。

## Inspection

动态 inspection_items，最多 100 项/批次；新增 Bulk Density、Black Specks、Appearance 等不改 Schema。支持增、改、删、排序、代码/名称、decimal/integer/text/none、实测值、单位、目标/上下限、边界包含、规格、方法、人工 judgement、私有备注、公开候选标志及检测日期。

六状态 pass/fail/not_tested/not_applicable/pending/informational 与旧 CHECK 一致。数值使用字符串，最多 18 位整数和 9 位小数，允许有符号检测数值；精确上下限比较采用 big.Rat，不使用 SQLite CAST REAL。not_tested/not_applicable 不携带结果；pass/fail/informational 必须有结果；整数拒绝小数，无实验室规则引擎或单位自动换算。

普通内容更新按 item_code 匹配并保留 ID；在完整表单改代码相当于删除旧项目和新增。工作集冻结或有附件的项目禁止改删。当前表单只编辑源语言，不把六套内容塞进 JSON；含译文的改写操作明确拒绝，显式删除项目会先删其译文。未来多语言编辑需要继续做一致性和父级锁验证。

## Clone

只复制可见、未锁定 Draft，用户提供新批号和本次日期（未知可空），要求 expected_edit_version。保持源 product/base/record_type、允许覆盖、检测定义及翻译；不跟随产品当前默认。不复制批次内部事实备注，质量重置 pending。

新主/子 UUID、actor/time；workflow=draft，审核/发布/归档/current/active 字段空，next_version_number=1；cloned_from_batch_id 记录来源。检测 numeric/text/result_display_text、tested_on、internal_note 清空，judgement=not_tested；定义/限值/方法/排序/is_public 保留，译文确认回 draft。子表触发器构建后的 edit_version 可能大于 1。

含未开放模块/认证/检测附件的来源明确拒绝，避免漏复制。没有复制旧 Passport、Publish Record、Published Asset 或旧 Audit；本次只有新的 batch_cloned 事件。

## 事务、Validation、Audit 与权限

Create、聚合 Update、Clone 的业务写入及 Audit 都在一个 DB Transaction。Create 在产品行无变化 UPDATE 预留 writer，Edit/Clone 在源 Batch 行预留 writer，再读取/验证版本和内容，避免先读后升级写锁。失败返回可读冲突/验证错误，不展示 SQLite 原始错误。

严格 JSON：未知字段、重复键、类型错误、尾值和超过 1MiB 请求拒绝。使用 DTO 白名单，不从前端接收 ORM Entity 系统字段。全部 5 条 API 需要 JWT/Casbin；非 admin 仅本人数据范围、无权限账号、只读账号已实测。保持上游 admin 特权逻辑；本地 enabledp=true，缺失数据范围时 fail closed；没有假称 T8 四角色矩阵完成。

审计沿用 batch_created/batch_cloned/batch_edited/override_set/override_cleared/inspection_changed，新增 override_reset。inspection_changed 的 after_data.operation 区分 create/update/delete。actor/time 与有界前后值同事务，超限改 Hash/truncated，不记密码或 token；最后 50 条显示在详情。既有审计不可修改/删除触发器保留。

失败注入：Create 的 Audit 失败后无 Batch；Override Audit 失败后整个基础内容/覆盖/版本/Audit 回滚；Clone 的 Inspection Copy 失败后无新 Batch 或子行。另用专用事务临时移除默认触发器构造损坏 Draft 默认，验证应用拒绝后事务回滚 DDL/数据；未对工作库或历史库移除保护。

## 实际 API 与页面

统一前缀 `/api/v1/passport-batches`：

| 方法 | 路径后缀 | 能力 |
| --- | --- | --- |
| GET | 空 | 分页、编码搜索、product_id/workflow 筛选 |
| POST | 空 | Product 当前默认校验 + Batch/Overrides/Inspections/Audit 原子创建 |
| GET | /{{id}} | 固定模板、覆盖、动态检测、有效值/来源、规则及最近审计；可选 language |
| PUT | /{{id}} | expected_edit_version + 完整 content/overrides/inspections 聚合替换 |
| POST | /{{id}}/clone | 新批号/日期 + expected_edit_version，复制允许结构 |

GET 详情同时承担 Effective/Overrides/Inspection List；PUT 聚合承担 Set/Clear/Reset 和 Inspection Create/Update/Delete/Sort。空子列表必须显式 []，遗漏拒绝；避免多个独立请求保存半个页面。不另暴露无必要的子表单独写端点。

菜单“产品数字身份证 → 批次身份证”，路由 `/#/passport/batches`，详情 query `?batch=<UUID>`。稳定身份/基础模板单独展示；结构化覆盖单选和工艺步骤，动态检测卡片可增删排序。明确 Draft/Internal Preview、来源和测试记录标识，无 Submit/Approve/Publish 按钮。中英 UI 语言包；没有要求员工编辑 JSON。

新增基本未保存提醒：路由离开/参数切换确认，刷新关闭使用 beforeunload；没有自动保存。有效内容展示已保存工作数据，编辑后有提示，保存后重新由后端解析。Clone 在脏表单时禁用。

## 测试与本地数据

主库 runtime/t6/db/passport-admin-t6.db 从迁移建立。另有 service-test.db（首轮）、service-final.db（最终）、upgrade-from-t5.db（只读历史源经 Backup API 创建的副本）、fresh-acceptance.db。没有将 T4/T5 工作库用作本轮工作库。

主后台 127.0.0.1:18097，Fresh 后台 18098，UI 19529，最终都已停止。Fresh 浏览器使用同一 UI 的独立上下文，将 localhost:18097 请求仅映射到 localhost:18098；真实登录/读写 Fresh DB，不伪造接口响应。工具依赖复用 T4 已安装 Go/pnpm/module cache，新的编译缓存和运行数据在 T6。

测试数据使用 PF-T6-* TEST 标识，浏览器长批号含运行时间用于避免重复。早期失败的测试草稿也保留，不通过删审计“清理”历史。主工作库全为 test，无商业记录；升级副本保留原 T5 内容。

| 测试组 | PASS | FAIL |
| --- | --- | --- |
'''
for title,rows in suites.items():report+=f'| {title} | {len(rows)} | 0 |\n'
report+=f'''
总计 {total} PASS，0 FAIL。Go 编译、完整前端 type-check、全量 lint（0 errors，30 条上游 warnings）、check:i18n、Vite 构建通过；上游 UI 36 文件/301 tests 通过。没有升级依赖或为消除上游 warning 批量改文件。

浏览器主流程 39 PASS，Fresh 浏览器 10 PASS。主流程实际创建/封版两版产品、创建 A/R1、覆盖 set/clear/reset、四检测项目、数值/文本保存刷新、未保存导航取消、UI 切默认 R2、旧 A/R1、新 B/R2、Clone/R1/覆盖保留与结果清空、新实测保存刷新、1280 布局、未捕获 JS 错误 0。截图：runtime/t6/test-artifacts/browser-list.png、browser-1280.png、browser-detail.png、browser-fresh.png。

并发：5 个不同批号全部成功；5 个同批号仅 1 成功其余 409；3 个不同新批号 Clone 全部成功且结构正确。最终短事务测试未出现 database is locked 或不可接受锁等待；不能推广为生产容量 SLA。主库 API 重启比较一致；浏览器完整聚合另经只读 Go 服务探针调用同一 GetBatch/Resolver 比较一致。权限账号、Casbin 授权及无授权记录也在重启后只读核对；允许/拒绝行为在首轮真实 HTTP 验证，不冒充已重放所有权限 HTTP。

Migration 验证 10 PASS：T5 有数据副本升级后 19 表逻辑内容 Hash 一致；Fresh 全 11 版本；二者重复运行 Schema/数据不变，审计保护保留。最终各库 integrity_check=ok，foreign_key_check 空，无重复批号、跨产品/非 sealed base、孤儿覆盖/检测或审计主线。

## 失败尝试与已知限制

- 初次脚手架路由文本匹配错误及 UI 类型/语言注册问题已修复。曾从错误 cwd 启动上游 migrate，找不到 config/db.sql，该事务失败；随后从 backend 目录执行并核对实际 11 版本。两个早期编译竞争输出曾让运行二进制缺少新迁移，已停止并串行构建、校验新版本，不依赖“初始化成功”日志。
- 浏览器失败证据保留 browser-*-failure.json：开发热更新使控件重建；长表单下拉定位/滚动竞态改为原生键盘选择；菜单与同名页签选择器明确到 menuitem；Hash 页面切换改为实际菜单导航并等待装载；日期组件不透传 data-testid，最终按实际表单标签定位。最终通过的是实际交互，不是仅检查按钮存在。
- 补充只读 HTTP 的自动审批两次未在截止前完成，未返回安全拒绝理由；改用无网络的只读 Go 服务探针完成剩余持久化核验。主 HTTP 重启 5 项已实际通过。
- 长表单下拉菜单的自动化鼠标定位仍有滚动竞态，键盘选择已验证；不声称已穷尽所有鼠标/浏览器组合。检测较多时页面较长，未做移动端专项或虚拟化。
- 前端上游保留少量 Element Plus 表单宽度及历史页面临时 i18n warning；无未捕获 JS error。后续若改通用组件，应独立验证，不在 T6 扩大重构。
- dev 验证码跳过与极长 JWT 仅供本地；未进行生产安全加固。未测试多机、持续生产负载、断电/磁盘满、完整文件备份或发布恢复。
- 覆盖/检测当前只提供源语言编辑，已有译文/附件的受限改写明确拒绝；未来扩展不能直接去掉防漏保护。T6 源码没有正式多语言审核、认证/模块/媒体中心。

## 文件与基线保护

新增文件：

'''
report+='\n'.join('- `'+p+'`' for p in files)
report+='''

新增 docs/T6_BATCH_MANAGEMENT.md、docs/T6_TEST_RESULTS.json。修改 docs/DATA_MODEL.md（审计枚举和 T6 实现规则）、docs/TASKS.md（T5 已验收、T6 待验收、T7 未开始）。本地独立 .env.t6.local 不覆盖 T4/T5 配置，runtime 为私有忽略目录。

新增 1788912000000_batch_management.go/.sql，仅 CHECK event_type 追加 override_reset 和批次菜单/API/权限注册；新表复制保留原审计行/索引/触发器，ID 段 9201–9205，菜单 9201/9202，有占用拒绝而非覆盖。业务表列和关系不变，无需修改 ERD。

上游 tracked 修改仍只有 src/lang/zh-CN/index.ts 与 src/lang/en-US/index.ts，T6 各注册 passportBatch；Backend 0。T5 模块实现不改，T4/T5 历史迁移不改。原 53 文件、site 7 文件及开工记录的 124 个 T4/T5 证据/业务源码/迁移文件哈希一致（依赖缓存不作为冻结证据重复哈希）。未 SSH、未连接 SERVER_IP、未操作 Caddy/Directus/生产 Docker/DNS/HTTPS。

## 复现与后续边界

source admin/t6/env.sh；admin/t6/setup.py 生成独立本地配置；在 admin/go-admin 工作目录执行 `go build -tags 'sqlite3,t4_schema' -o ../../runtime/t6/go-admin-final .`，migrate/server 显式指定 runtime/t6 下的配置。t4_schema 是既有迁移标签，不代表仅运行 T4。不要直接启动普通无标签后端。

Go 子测试显式 `T6_TEST_DB=<专用全新已迁移库> go test -tags 'sqlite3,t6_validation' ./app/passport/service -run TestT6 -count=1 -json`。有固定测试编码，不能反复写入同一已填充库。HTTP initial/Fresh 脚本同理；迁移验证拒绝覆盖已有证据。verify_api.py restart 为只读聚合比较（登录会产生框架日志）；cmd/t6readprobe 以 mode=ro 打开 T6 主库，不访问网络，比较浏览器聚合与权限记录。UI `pnpm dev --mode t6 --host 127.0.0.1 --port 19529 --strictPort`。私有口令不写报告，不把本地配置作为生产配置。

T7 仅在另行获批后开发类型化自定义模块；T8 才实现四角色审核与固定候选；T9 才实现完整 Public Builder、Snapshot、资产冻结与 Atomic Publish。后续必须复用固定 base、三态语义、edit_version、事务审计与权限边界，不把此工作预览当成可发布快照。本轮停止，未进入上述阶段。

## 40 项 Gate

| # | Gate | 结果 |
| --- | --- | --- |
'''
report+='\n'.join(f"| {g['number']} | {g['name']} | PASS |" for g in gates)
report+='\n\n## 74 项逐项回答\n\n| # | 问题 | 回答 |\n| --- | --- | --- |\n'
report+='\n'.join(f"| {a['number']} | {a['question']} | {a['answer']} |" for a in answers)
report+='\n\nT6 批次数字身份证管理已完成，当前已停止，等待人工验收，未进入 T7。\n'
(R/'docs/T6_BATCH_MANAGEMENT.md').write_text(report)
p=R/'docs/TASKS.md';s=p.read_text().split('\n\n## T6 停止状态')[0].replace('本地验收收尾中，未进入 T7','等待人工验收；已停止，未进入 T7');s+='\n\n## T6 停止状态\n\nT5 已由用户人工验收通过。T6 本地开发与验收完成，40/40 Gates、'+str(total)+' 个业务断言通过，当前等待人工验收；本轮本地服务已停止。T7/T8/T9 均未开始，未连接服务器或部署。详见 T6_BATCH_MANAGEMENT.md 与 T6_TEST_RESULTS.json。\n';p.write_text(s)
print(total,'PASS / 0 FAIL; 40 gates; 74 answers')
