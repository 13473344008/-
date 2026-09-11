"""Build the T5 report from already executed local evidence."""
import json,datetime,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t5';ev=rt/'test-artifacts';read=lambda n:json.loads((ev/n).read_text());rows=[json.loads(x) for x in (ev/'service-tests.jsonl').read_text().splitlines()]
service=[{'name':x['Test'].split('/',1)[1],'status':'PASS' if x['Action']=='pass' else 'FAIL','time':x['Time'],'evidence':'runtime/t5/test-artifacts/service-tests.jsonl'} for x in rows if x.get('Action') in ['pass','fail'] and '/' in x.get('Test','')]
suites={'Go/GORM Service':service,'HTTP API and permissions':read('api-initial.json'),'Backend restart':read('api-restart.json'),'Browser E2E':read('browser-tests.json')['checks'],'Migrations':read('migration-tests.json'),'Fresh HTTP':read('fresh-http-tests.json'),'Final integrity and baseline':read('final-tests.json')};tests=[x for a in suites.values() for x in a];assert len(tests)==135 and all(x['status']=='PASS' for x in tests)
gates=['Products 列表','Product 创建','Product Code 应用及 DB 唯一','初始 Revision','创建事务','失败全回滚','Draft 编辑','新版本不改历史','冻结主体 API 拒绝','冻结翻译 API 拒绝','Clone','Revision Number 唯一','显式默认切换','默认合法性','六语言 API','Translation 唯一','Archive 保留历史','业务 API 认证','业务审计','重启持久化','浏览器全流程','Fresh DB','integrity_check','foreign_key_check','53 文件基线','site 7 文件']
answers=[
('Products 列表真实可用？','Yes；分页、编码/名称搜索、状态筛选及详情通过。'),('Product 创建真实可用？','Yes；同时建立 Product、R1、源语言翻译。'),('重复编码被业务层拒绝？','Yes；trim/大写规范化后返回 409 和清晰提示。'),('DB UNIQUE 最后保护？','Yes；直接 SQL 重复编码/版本/翻译被拒。'),('Product 与 Revision 真正分离？','Yes；稳定 UUID 身份与独立多版本行。'),('初始 Revision 创建？','Yes；Create Product 事务创建 R1 Draft。'),('三表创建使用 Transaction？','Yes，另含业务 Audit。'),('中途失败全回滚？','Yes；注入翻译 INSERT 错误及 Audit INSERT 错误均验证。'),('Draft 可编辑？','Yes；内容令牌检测旧稿冲突。'),('冻结主体 Backend 拒绝？','Yes，409；DB 触发器也保留。'),('冻结 Translation Backend 拒绝？','Yes，409；DB 触发器也保留。'),('新 Revision 不修改旧版？','Yes，旧聚合逐字节比较通过。'),('R1/R2 完整保留？','Yes。'),('Revision Number 不重复？','Yes；取得写锁后事务分配，5 个并发请求生成 R3–R7。'),('Clone 复制允许内容？','Yes；结构化模板及全部已存在译文；未开放子系统存在时明确拒绝。'),('Clone 系统字段重置？','Yes；新 ID/actor/时间，draft、sealed_* / hash 清空；译文重置 draft。'),('默认 Revision 可设置？','Yes，独立显式 API。'),('默认必须属于 Product？','Yes。'),('默认状态校验？','Yes，只允许 sealed。'),('切默认不修改历史？','Yes；仅更新 products 指针和元数据，写审计，不写 Batch/旧 Revision。'),('六语言共存？','Yes；en、zh-CN、es、ar、fr、de。'),('同版本同语言不能重复？','Yes；API upsert，DB UNIQUE。'),('Archive 不破坏历史？','Yes；默认指针及所有版本保留。'),('普通 Hard Delete 破坏历史路径？','本模块没有 DELETE API，只有归档。'),('全部业务 API 要求认证？','Yes；12 条路由匿名负向测试。'),('绕过 Casbin？','No；使用上游 JWT、AuthCheckRole 和菜单/API 权限；保留上游 admin 特权逻辑。'),('使用 Request DTO/白名单？','Yes；严格解码，拒绝未知和重复字段。'),('避免 Mass Assignment？','Yes；系统 ID/actor/状态等不能通过内容 DTO 覆盖。'),('业务 Audit 产生？','Yes；沿用既有审计表及合适事件，新增 7 个注册事件。'),('Audit 与业务同事务？','Yes，全部本模块写操作。'),('重启后业务数据存在？','Yes；产品详情聚合与重启前完全一致。'),('浏览器完整流程？','PASS，21 项断言。'),('并发版本无重复？','PASS，5 个写入者全部成功，无重试。'),('Fresh DB 从零建立？','Yes；全部 10 个迁移后登录并创建产品。'),('Migration 重复运行？','Yes；升级库及 Fresh 库重复执行不改变数据/Schema。'),('integrity_check=ok？','Yes。'),('foreign_key_check？','PASS，无异常行。'),('修改 DATA_MODEL Schema？','仅扩展审计 event_type CHECK；业务 19 表/308 列及关系不变。'),('通过新 Migration？','Yes，1788825600000；T4 历史迁移未改。'),('修改上游 tracked files？','Yes，UI 2 文件；Backend 0 文件。'),('具体哪些及原因？','src/lang/zh-CN/index.ts、src/lang/en-US/index.ts，仅注册新增 passport 语言包。'),('53 基线 Hash 一致？','Yes。'),('site 7 文件未变？','Yes。'),('连接业务服务器？','No。'),('修改 Caddy？','No。'),('修改 Directus？','No。'),('修改生产 Docker？','No。'),('开发 Batch 正式管理？','No。'),('开发 Published Snapshot Engine？','No。'),('进入 T6？','No。')]
result={'status':'等待人工验收','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pass':135,'fail':0,'total':135,'suites':suites,'gates':[{'gate':i,'name':g,'status':'PASS'} for i,g in enumerate(gates,1)],'answers':[{'number':i,'question':q,'answer':a} for i,(q,a) in enumerate(answers,1)],'entered_T6':False};(R/'docs/T5_TEST_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
apirows=[('GET','', '分页、search、status'),('POST','','原子创建 Product/R1/翻译/审计'),('GET','/{id}','Product 详情及 Revision History'),('PUT','/{id}','仅 active/disabled'),('POST','/{id}/archive','归档，保留历史'),('GET','/{id}/revisions','版本列表（含模板内容）'),('GET','/{id}/revisions/{rid}','版本详情，含六语言和编辑 token'),('POST','/{id}/revisions','基于 source_revision_id 创建下一版本'),('PUT','/{id}/revisions/{rid}','Draft 内容替换，expected_token 必填'),('PUT','/{id}/revisions/{rid}/translations','单语言 upsert，expected_token 必填'),('POST','/{id}/revisions/{rid}/seal','封版，expected_token 必填'),('PUT','/{id}/default-revision','显式选择 revision_id，检查 expected_current_revision_id')]
api='\n'.join(f'| {m} | `/api/v1/passport-products{p}` | {d} |' for m,p,d in apirows)
newfiles=[str(p.relative_to(R)) for folder in ['admin/go-admin/app/passport','admin/go-admin-ui/src/api/passport','admin/go-admin-ui/src/views/passport','admin/go-admin-ui/src/lang/zh-CN/passport','admin/go-admin-ui/src/lang/en-US/passport','admin/t5'] for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
newfiles += ['admin/go-admin/app/admin/router/passport_products.go','admin/go-admin/cmd/migrate/migration/version/1788825600000_product_templates.go','admin/go-admin/cmd/migrate/migration/version/1788825600000_product_templates.sql']
summary='\n'.join(f'| {name} | {len(items)} | {len(items)} | 0 |' for name,items in suites.items())
text=f'''# 【T5 执行结果】

日期：2026-09-08。**T5 状态：等待人工验收**。用户已确认 T0–T4 通过；本轮只完成 T5，所有本轮本地服务已停止，未进入 T6。

Products、Product Revision、Revision Freeze、Revision Clone、Default Revision、Translations、Transactions、Validation、Audit、UI、Browser E2E、Fresh DB、Integrity、Baseline Protection：**全部 PASS**。

**Gate：26 / 26 PASS。Tests：135 PASS，0 FAIL。** 构建、TypeScript、限定新增文件 ESLint、上游 check:i18n 另行通过，不计入 135 功能断言。早期尝试中的配置/测试问题见下文，不冒充所有尝试都成功。

## 范围与架构

正式业务代码位于 app/passport 的 Model / DTO / Validation / Service / API，路由文件在已注册的 app/admin/router 包中 init 自注册。没有另建认证体系、ORM 或万能 Product JSON，也没有改动通用数据库、权限和框架基础功能。

稳定 products 身份与 product_revisions、product_revision_translations 分离。每个 Revision 有独立 UUID、产品内序号、来源版本、状态和冻结元数据。公开端及 site 保持冻结，不使用这些私有 ORM 返回值作为 Public Payload。

Backend HEAD：595c4a6be5b1aade8dc30fe2b90ea13dfba61b05（v2.6.0）；UI HEAD：e106f68d362d3a7aaa43244eb74cede1a83f4da5（v3.2.0）。没有升级依赖。工具链复用 Go 1.26.5 / Node 24.18.0 / pnpm 9.15.1，Go 实际 SQLite 3.53.4；测试脚本的 Python sqlite3 为 3.45.3。

## 数据与配置隔离

- 主库：`/path/to/ID/runtime/t5/db/passport-admin-t5.db`，从 Fresh Migration 建立，未复用 T4 工作库。
- 专用服务测试库 service-test.db；升级副本 upgrade-from-t4.db；从零验收库 fresh-acceptance.db；均位于 runtime/t5/db。
- 日志、构建产物、私有凭据、测试截图/报告都在 runtime/t5，runtime/.gitignore 已整体忽略。T5 目录 0700，数据库/私有配置 0600。
- T4 主库/Backup/Restore/资产/证据、二进制及历史迁移共 55 个受保护文件开始/结束 SHA-256 一致。Go/pnpm 工具及已安装模块作为依赖复用，新的 Go 编译缓存写 runtime/t5/cache。
- DSN：`file:/path/to/ID/runtime/t5/db/passport-admin-t5.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL`；连接级 foreign_keys=1、WAL、5000ms、FULL 已通过实际 Go 驱动读取；主后台 maxOpenConns/maxIdleConns=1。
- 本地主后端 127.0.0.1:18095，UI 127.0.0.1:19528；独立新库 HTTP 验收使用 18096。三个端口均已检查停止。未连接任何业务服务器。

## Service 规则与事务

### Product

编码 trim 后规范为大写，1–64 ASCII 字母/数字/下划线/连字符，全生命周期 UNIQUE；创建后不可改，不用业务码充当主键。列表提供分页、编码/任一版本产品名搜索、状态筛选、名称、默认版本、版本数与更新时间。详情分开呈现稳定身份与版本历史。

创建事务：验证 DTO → Product → R1 Draft → 至少源语言 Translation → 两个业务 Audit。失败不留下半成品；测试在合法请求的翻译 INSERT 上注入数据库错误，另一次在 Audit INSERT 注入错误，均确认整个事务回滚。API 不创建没有初始版本的产品。

稳定字段编辑仅开放 active/disabled；Archive 写 lifecycle_status=archived、archived_at，并保留 current_revision_id 与所有版本。归档在本阶段只读，不提供恢复归档或 Hard Delete API。停用仍可维护模板，供重新启用前整理资料；未来新建 Batch 应只选 active 产品。

### Revision / Clone / Freeze

草稿可编辑字段为 DATA_MODEL.md 中 source_language、category_code、origin_country_code、package_quantity、package_unit、package_type_code、shelf_life_days、process_steps、internal_note。普通请求不能覆盖 ID、product_id、revision_number、actor、时间或冻结状态。

现有产品写事务先执行无变化的 Product 主键 UPDATE 取得 SQLite writer，再读取状态/源版本/最大编号，分配新号并写子表/审计；DB UNIQUE 为最后防线。不在浏览器分配号码。5 个并发克隆请求实际成功生成 R3–R7，0 失败、0 重试；已提交版本不删除、不会重用，回滚未提交分配不成为历史版本。

Clone 复制已开放的结构化模板及所有已有译文。新 ID、创建/更新时间与 actor 重建，source_revision_id 固定旧版，revision_status=draft、sealed_at/by/content_hash=NULL。译文复制文字和步骤标签，translation_status 重置 draft。新建或编辑 R2 不改 R1，不隐式切默认。

每次 Draft 修改/翻译/封版提交 expected_token，服务比较当前聚合摘要；旧稿冲突返回 409，避免覆盖他人修改。token 为请求前置条件，不是可编辑系统列。

封版要求源语言存在、产品名合法且 translation_status=approved，其他语言可不齐。此处 approved 表示该语言模板文字已确认，**不是 T8 Reviewer 业务审核已完成**。封版事务校验并计算 product-template-v1 内容摘要、设置 sealed 元数据、写 product_revision_sealed 审计；API 状态检查和 T4 DB 冻结触发器双重保护。

哈希使用固定 DTO 字段序、稳定 map 键序及按 language_code 排列译文，包含已开放模板内容及翻译，排除行 ID/actor/创建时间；这是有版本的私有模板摘要协议，不能当成 T9 Public Payload 的规范化序列化器或资产 Hash。

T5 没有开放 Custom Section、认证关联、Media Center。遇到含这些未开放关联的模板，Clone/Seal 明确返回业务冲突，避免复制/摘要遗漏子内容。没有新增这些系统或假菜单。

### 默认与翻译

默认必须是同一产品的 sealed Revision，且 expected_current_revision_id 与当前值一致。只更新 Product 当前指针及元数据、写审计；不修改旧 Revision 或 Batch。默认影响未来新 Batch 的初始选择，不具备更新已存在 Batch 的行为。

翻译支持 en/zh-CN/es/ar/fr/de，API 单语言 upsert；相同语言不增加第二行，DB UNIQUE 继续保护。源语言默认 en；Draft 至少有源语言名称，不要求六语言齐全。process_steps 是有序 step_key 列表，process_labels 只允许引用已有步骤；页面提供结构化输入，不要求员工编辑 JSON。阿拉伯语表单 RTL。

### 权限、DTO 与错误

12 条新业务路由全部使用上游 JWT + AuthCheckRole + PermissionAction。菜单/API 权限注册到原 sys_menu/sys_api/sys_menu_api_rule/casbin_rule。保留上游 admin 特权逻辑，其余角色必须获权；已测试登录但无 Casbin 授权的账号被拒。

业务 created_by 通过模块内子查询别名适配上游要求的 create_by；通用 Permission 不改。已测试仅本人范围的非 admin 账号能创建/读取自己的产品，列表排除他人，详情及写他人产品被拒。最终 Editor/Reviewer/Viewer 矩阵、撤权会话语义留 T8。

请求使用显式 DTO，严格 JSON 解码，拒绝重复键、未知/系统字段、额外尾值与 >1MiB 请求。应用校验编码、语言、十进制格式、长度、步骤合法性、所属关系、冻结状态及默认状态。错误转为可理解的 409/422/404，不把 SQLite 错误直接显示给员工；技术错误留私有日志。

## 实际 API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
{api}

响应沿用 Go Admin code/data/msg、PageOK；翻译 GET 包含在版本详情中。没有 DELETE、Batch 或 Passport 发布路由。

## UI 页面与浏览器流程

动态菜单：产品数字身份证 → 产品模板；路由 `/#/passport/products`。同页面用 `?product=<UUID>` 进入详情，保持刷新后能重新读取。组件 name=PassportProducts；复用 PageContainer、ProTable、useTable、DateCell、原权限指令和请求拦截器。

列表简洁展示身份/名称/状态/默认/版本数；详情包含稳定身份、默认版本、历史列表和选定版本内容。已封版显示只读说明，并提供“创建新版本”；不把“保存产品”当成覆盖历史。表单文字有中英语言包，产品内容六语言独立管理。

真实浏览器完成登录 → 菜单 → 新建产品/R1 → 编辑净含量 → English/中文翻译 → Clone R2 → R2 改成 20、R1 仍 25 → R1 封版 → UI 禁用编辑且直接 HTTP 被拒 → 显式设默认 → 刷新保持；额外验证 Arabic RTL、1280px 无页面横向溢出、未捕获 JS 错误 0。

截图：runtime/t5/test-artifacts/browser-list.png、browser-frozen.png、browser-1280.png；精确成功样本 ID 在 browser-fixtures.json。测试均带 T5/TEST 标识及 TEST RECORD — NOT FOR COMMERCIAL USE，没有创建正式商业记录。

## Migration 变化与问题修复

新增 **1788825600000_product_templates.go / .sql**，同一事务扩展 audit event_type CHECK、保留审计行/索引/不可变触发器、注册 12 API 与 3 菜单记录及 admin 授权。既有 archived / product_revision_sealed 继续使用；新增 product_created、product_updated、product_revision_created、product_revision_cloned、product_revision_updated、product_default_revision_changed、product_translation_updated。没有新业务表、列或关系；总数仍 19/308。审计与全部本模块写操作同事务。

SQLite 修改 CHECK 采用新表复制旧行并替换的版本迁移，测试 T4 有数据副本升级后 19 表逐表逻辑 Hash 一致，审计不可变触发器仍存在；T4 原库只读、不改历史迁移。菜单 ID 段 9100 起，已占用会报错并回滚，不覆盖未知菜单/API。

首次新迁移发现旧 migration ModelTime 会显式 INSERT deleted_at=NULL，而上游后续迁移已把字段改为 NOT NULL/0。修正**尚未成功提交的新 T5 迁移**为省略该字段并使用表的 0 默认；读取 admin 用明确 deleted_at=0。原 T4 版本文件完全没改。最初配置生成器缺日志 path 键、服务 import 路径及测试库准备顺序问题也已修复；不曾更换框架或依赖。

浏览器最初失败涉及 Element Plus 隐藏 checkbox、异步 Clone 完成等待和默认英文确认按钮。已按真实控件等待，确认框接入原语言包。失败尝试保留在 browser-*-failure.json，最终完整流程 PASS。ESLint 首次指出新文件格式问题，限定新模块及两个语言入口修正，未批量格式化上游。

## 测试汇总

| 测试组 | 数量 | PASS | FAIL |
| --- | --- | --- | --- |
{summary}

共 135 个最终命名检查；不含 Gate 汇总、Go 父测试、重试尝试，也不把每个事务内的 SQL 行数当作测试数量。测试时间、错误、证据路径在 T5_TEST_RESULTS.json 与 runtime/t5/test-artifacts。另通过 Go 编译、UI type-check、限定范围 ESLint、UI 静态构建及上游 check:i18n。

Fresh 验收从删除专用 disposable 库后运行全部 10 版本开始，随后实际启动独立后端、登录、空列表、HTTP 创建 Product/R1/Translation。主后端停止后重新启动，之前完整产品聚合（含六语言及默认指针）与重启前相同。最终 integrity_check=ok、foreign_key_check 无行、编码/版本/翻译无重复。

## 26 Gates

| Gate | 内容 | 结果 |
| --- | --- | --- |
'''+ '\n'.join(f'| {i} | {g} | PASS |' for i,g in enumerate(gates,1))+f'''

## 文件清单

新增业务及验证文件：

'''+ '\n'.join('- `'+p+'`' for p in sorted(newfiles))+'''

新增 docs/T5_PRODUCT_TEMPLATE.md、docs/T5_TEST_RESULTS.json。修改 docs/DATA_MODEL.md（审计枚举及实现边界）、docs/TASKS.md（T4 已验收、T5 待验收、T6 未开始）。

上游 tracked files 仅 UI `src/lang/zh-CN/index.ts` 与 `src/lang/en-US/index.ts`：各增加 passport 语言包 import/注册。Backend tracked 文件修改 0，新路由由已有包自动编译注册；旧 T4 新增但未提交 Git 的文件不算本轮新增或修改。go.mod/go.sum/pnpm-lock.yaml 未改，两个锁定 commit 未变。

原 53 文件和 site 7 文件全部 Hash 一致。没有业务服务器连接，没有 Caddy/Directus/生产 Docker/DNS/HTTPS 操作。

## 复现与已知限制

先 source admin/t5/env.sh；admin/t5/setup.py 只生成本轮独立配置，不覆盖已有口令。Backend 在 admin/go-admin 中使用 `go build -tags 'sqlite3,t4_schema'`（t4_schema 是既有业务迁移标签，本轮未改名），migrate / server 均指定 runtime/t5/settings.yml。UI 用 `pnpm dev --mode t5 --host 127.0.0.1 --port 19528 --strictPort`；独立 .env.t5.local 不覆盖 T4 .env.development.local。

服务单测使用 `T5_TEST_DB=<专用全新 T5 库> go test -tags 'sqlite3,t5_validation' ./app/passport/service -run TestT5ProductTemplates -count=1 -json`。须先对专用库执行全部迁移；测试会创建固定测试编码，不可反复灌入同一已填充库。HTTP 初始验收同理；迁移脚本拒绝覆盖已有证据数据库。verify_api.py restart 为只读持久化复验。运行数据与口令保持私有，不提交公开仓库。

- dev 模式验证码跳过、JWT 极长仅属本地配置；不是生产安全基线，未开发生产部署。
- 上游 SQLite 角色跨操作失败原子性仍是 T4 边界；产品业务事务没有照搬该模式，已独立测试。
- 本轮没有完整文件存储/资产冻结、认证/模块管理、Batch、审核、发布、Snapshot、Atomic Publish、Rollback 或二维码。不能把模板封版摘要当成已发布身份证。
- 草稿为显式保存，没有自动保存；切换版本/语言前需要保存表单。发生内容令牌冲突需刷新并重新编辑。
- 来源中已有未开放关联时拒绝 Clone/Seal；未来开放对应模块后必须扩充复制、摘要及冻结测试，不得移除此防漏保护后直接丢子数据。
- 本地并发测试不覆盖多机、长事务、断电/磁盘满及真实生产负载；锁等待达到上限返回可读冲突，不做无限重试。
- T6 只能在另获用户授权后开始：只选 active Product 的 sealed 当前默认模板，创建 Batch 时固定 base_product_revision_id；默认切换不重绑旧批次。继续复用 DTO/事务/审计/权限边界，不复用测试数据充当商业资料。

## 50 项逐项回答

| # | 问题 | 回答 |
| --- | --- | --- |
'''+ '\n'.join(f'| {i} | {q} | {a} |' for i,(q,a) in enumerate(answers,1))+'''

T5 产品模板管理已完成，当前已停止，等待人工验收，未进入 T6。
'''
(R/'docs/T5_PRODUCT_TEMPLATE.md').write_text(text);print('135 PASS / 0 FAIL; 26 gates; 50 answers')
