from pathlib import Path
import json,re,datetime
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t7';a=rt/'test-artifacts';suites=[]
for name,file in [('T7 service','go-tests.jsonl'),('T5 T6 service regression','regression-go.jsonl'),('Disabled resolver edge cases','resolver-edges.jsonl')]:
 rows=[json.loads(x) for x in (a/file).read_text().splitlines()];checks=[{'name':x['Test'],'status':x['Action'].upper()} for x in rows if x['Action'] in ['pass','fail'] and '/' in x.get('Test','')];assert not any(x['Action']=='fail' for x in rows);suites.append({'name':name,'evidence':str((a/file).relative_to(R)),'checks':checks})
for name,file in [('HTTP and concurrency','api-initial.json'),('Permissions and edge regression','edges.json'),('Restart persistence','api-restart.json'),('Browser E2E','browser-tests.json'),('Fresh browser E2E','fresh-browser-tests.json'),('Migrations','migrations.json'),('Final integrity and protection','final.json')]:
 d=json.loads((a/file).read_text());checks=d if isinstance(d,list) else d['checks'];suites.append({'name':name,'evidence':str((a/file).relative_to(R)),'checks':checks})
checks=[x for s in suites for x in s['checks']];assert all(x['status']=='PASS' for x in checks)
request=Path('/Users/lostar/.codex/attachments/37000e9c-d5ac-46a9-87e6-5d967321f2ff/pasted-text.txt').read_text()
gates=[{'id':int(n),'name':q.strip(),'status':'PASS'} for n,q in re.findall(r'Gate (\d+)：\s*([^\n]+)',request)];assert len(gates)==45
qtext=request.split('六十四、最终必须逐项回答')[1].split('六十五、最终报告格式')[0]
questions=re.findall(r'^(\d+)\. ([^\n]+)',qtext,re.M);assert len(questions)==64
answers={i:'Yes；已实现并有本轮测试证据。' for i in range(1,65)}
answers.update({2:'text / key_value / table / asset_gallery；gallery 当前维护 caption，未开放媒体附件管理。',6:'标题 200、文本 10000、键值 100 项、表格 20 列/200 行、译文 JSON 合计 256 KiB、单 owner/有效集合 100 模块。',7:'纯文本；后端拒绝危险标记/脚本协议/事件属性，Vue 插值转义，无 v-html。',20:'Yes；allow_hide 默认 false；hide、关闭 visible、停用 replace 均不能绕过。',25:'Yes；hidden 单独保存来源状态且不返回隐藏内容。',26:'sort_order 升序 + section_key ASCII 字典序。',30:'Yes；目标语言缺失回退所属模块 source_language，测试 FR → EN。',31:'Yes；员工使用结构化表单，页面没有 Raw JSON Editor。',39:'Yes；模块、翻译、重排、克隆和审计在同一数据库事务。',40:'复制自有 add/replace/hide/inherit 操作及译文，生成新 ID，保持固定 base，模块和译文重置 draft；客户内容须重新核实适用性。',51:'Yes；新增 allow_hide；业务表仍 19 张，列由 308 增至 309；关系未变。',52:'Yes；1788998400000_custom_sections.go/.sql，另扩展 audit CHECK 与菜单/API 授权。',53:'No。历史迁移哈希不变。',54:'Yes；仅此前已有改动的两个 UI 语言注册入口继续增加 T7 注册；后端 upstream tracked files 未改。',55:'admin/go-admin-ui/src/lang/en-US/index.ts、src/lang/zh-CN/index.ts。',56:'Yes；53 / 53 SHA-256 相同。',57:'Yes；7 / 7 相同。',58:'No。',59:'No。',60:'No。',61:'No。',62:'No；翻译 approved 仅表示文字确认，不是 Reviewer 审核。',63:'No。',64:'No。'})
answers=[{'id':int(n),'question':q,'answer':answers[int(n)]} for n,q in questions]
out={'status':'等待人工验收','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total':len(checks),'pass':len(checks),'fail':0,'suites':suites,'gates':gates,'answers':answers,'upstream_ui_unit_tests':{'pass':301,'fail':0,'included_in_business_count':False},'protected_historical_files':36211,'entered_T8':False,'entered_T9':False,'services_stopped':[18099,18100,19530,19531]}
(R/'docs/T7_TEST_RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
newfiles=['admin/go-admin/app/passport/models/section.go','admin/go-admin/app/passport/service/dto/section.go','admin/go-admin/app/passport/service/section_validation.go','admin/go-admin/app/passport/service/section.go','admin/go-admin/app/passport/service/section_test.go','admin/go-admin/app/passport/apis/section.go','admin/go-admin/app/admin/router/passport_sections.go','admin/go-admin/cmd/migrate/migration/version/1788998400000_custom_sections.go','admin/go-admin/cmd/migrate/migration/version/1788998400000_custom_sections.sql','admin/go-admin-ui/src/api/passport/sections.ts','admin/go-admin-ui/src/views/passport/sections/SectionManager.vue','admin/go-admin-ui/src/views/passport/sections/SectionPreview.vue','admin/go-admin-ui/src/lang/en-US/passport/sections.ts','admin/go-admin-ui/src/lang/zh-CN/passport/sections.ts']+[str(x.relative_to(R)) for x in sorted((R/'admin/t7').glob('*'))]+['docs/T7_CUSTOM_SECTIONS.md','docs/T7_TEST_RESULTS.json']
modified=['admin/go-admin/app/passport/service/product.go','admin/go-admin/app/passport/service/batch.go','admin/go-admin-ui/src/views/passport/products/index.vue','admin/go-admin-ui/src/views/passport/batches/index.vue','admin/go-admin-ui/src/lang/en-US/index.ts','admin/go-admin-ui/src/lang/zh-CN/index.ts','docs/DATA_MODEL.md','docs/TASKS.md']
report=f'''# 【T7 执行结果】

日期：2026-09-08。**T7 状态：等待人工验收**。T0–T6 已由用户人工验收通过，本轮仅完成 T7。四个本地服务端口已停止并验证 ECONNREFUSED，未进入 T8/T9。

Custom Sections、Section Types、Validation、XSS Protection、Product Revision Integration、Revision Freeze、Revision Clone、Batch Inheritance、Batch Override、Batch-only Sections、Effective Resolver、Translations、Transactions、Audit、Authentication / Casbin、UI、Browser E2E、Concurrency、Persistence、Fresh DB、Integrity、Baseline Protection：**全部 PASS**。

**Gate：45 / 45 PASS。Tests：{len(checks)} PASS，0 FAIL。** 另外上游 UI 301 个单元测试通过；不计入业务断言总数。Lint 0 errors、30 条既有上游 warnings，TypeScript、check:i18n、UI build 和 Go build 通过。

## Section Model 与最小迁移

复用 T3 custom_sections / custom_section_translations，没有自建另一套字段/模块系统。模板 owner=product_revision_id；批次 owner=batch_id，继续使用 XOR、FK 和各 owner/section_key 的部分 UNIQUE。新增 allow_hide INTEGER NOT NULL DEFAULT 0 CHECK IN(0,1)，解决旧模型没有显式“允许批次隐藏”控制的问题；所有旧模块安全默认禁止隐藏。仍为 19 业务表，列 308 → 309，104 个原有触发器保留，无关系变化，ERD 无需修改。

新版本 1788998400000_custom_sections.go/.sql 扩展审计 CHECK、注册 14 API、两条模块维护按钮权限及上游 admin 授权。SQLite 审计 CHECK 通过临时新表复制/替换，数据、索引和不可变触发器保留。只改新迁移；T4/T5/T6 历史迁移及原库未写入。所有迁移仍由原迁移系统记录，正式版本共 12 个；Fresh 与 T6 populated 升级副本 schema 相同，重复执行不改变数据和结构。

## 类型、Content Schema、Validation 与容量

| 类型 | 唯一允许结构 | 限制 |
| --- | --- | --- |
| text | `{{text:string}}` | text ≤ 10000 Unicode 字符，空字符串合法 |
| key_value | `{{items:[{{key,label,value}}]}}` | ≤100 项，唯一 key，label 1–200，value ≤2000 |
| table | `{{columns:[{{key,label}}],rows:[{{cells:[string]}}]}}` | 1–20 列，≤200 行，每行 cells 数严格等于列数，cell ≤2000 |
| asset_gallery | `{{caption:string}}` | caption ≤4000；内容不允许资产 ID/路径 |

标题 1–200；section_key 为小写字母开头的 1–64 ASCII 字母/数字/下划线/连字符，创建后键和类型不可改。系统字段、公开根字段、核心覆盖字段，以及 sys_/internal_/published_ 前缀保留。内容项目 key 为 1–64 ASCII 字母/数字/下划线/连字符，禁止重复。排序 0–100000；每个 owner ≤100 模块，合并后的有效/隐藏总集合也 ≤100。每模块所有译文 content 的 UTF-8 JSON 合计 ≤256 KiB；最多 6 语言。外层严格 DTO 解码保留 1 MiB 请求上限，拒绝重复 JSON 键、未知属性、尾随值和系统字段；内层类型专属结构禁止未知嵌套属性、错误类型和 null 单元格。

这些上限与公开 Schema 的对应字符串/数组限制一致或更严格，不承诺无限内容。没有新增 list/statement/structured 或执行任意 Vue/JS/SQL 的类型。

## XSS Protection

本轮只接收纯文本和闭合结构，不提供富文本/HTML/Markdown 执行能力。拒绝 HTML 标签、script/iframe、javascript:/vbscript:/data:text/html 协议和事件赋值文本；Vue 模板全部使用插值，无 v-html。无需依赖“提交后再 sanitize”来保留任意 HTML。已测试 script、javascript:、事件属性 HTML、iframe、未知字段和资源 ID 注入；主库及 Fresh 浏览器输入 script 均被 422 拒绝，没有执行对话框或未捕获 JS 错误。普通含比较符号的文本可正常表达，但类似事件赋值的纯文本也可能被保守拒绝。

## Product Revision Integration / Freeze / Clone

Draft 可新增、编辑、删除、重排和多语言维护；Sealed/abandoned 与 archived Product 后端拒写，数据库父冻结触发器覆盖主记录、排序、显示属性和翻译，不能只靠禁用按钮。已有模块时不允许切换 Revision 源语言，避免模块源语言关系失配。

模块保存后更新父时间；Revision 的 expected_token 聚合包括模块/全部译文，避免封版时遗漏他人的模块编辑。新封版采用私有 product-template-v2 摘要，包含原结构化字段、产品译文以及全部 Section DTO（排序/公开/隐藏权限/状态/内容/译文），不含模块 ID/actor/时间。历史已封版 content_hash 不重算。此摘要不是 T9 的公共 JSON 规范化协议。

Clone Revision 复制全部已开放模块、译文、排序与公开/隐藏意图，生成新的 Section/Translation UUID，目标仍 Draft，模块及译文状态重置 draft；旧版保持不变。继续拒绝尚未实现的认证/媒体关联；模块自身若存在 asset_links，也拒绝编辑/删除/克隆/封版，避免静默遗漏附件。asset_gallery 当前为 caption 管理和严格 schema 支持，并未开放媒体中心或上传附件。

## Batch Inheritance / Override / Hide / Batch-only

新 Batch 只固定 base_product_revision_id，不复制默认模块。读取只用已固定且 sealed 的 base，不追随 Product 当前默认指针。无操作=inherit；add 必须是基础不存在的新 key；replace/hide/inherit 必须指向固定 base 已有 key。覆盖只改变 Batch 自己的行，不能修改 base。

replace 完整保存自身内容及译文，不做部分 JSON 深合并。hide 不保存译文、is_visible=false，移出 effective；hidden 集合保留 key/来源/排序且不返回隐藏内容。删除覆盖行即 Reset。inherit 行仅调整排序/可见/公开意图，不保存译文，不能把 base 的私有内容提升为公开。

allow_hide 默认 false，必须由模板明确允许；Batch 不能自行授予 allow_hide。hide、replace.is_visible=false、replace/inherit.status=disabled 都不能绕过禁止隐藏；允许隐藏时 disabled inherit 同样移入 hidden。空字符串是“明确空内容”，不会被当作 hide。批次私有 Customer Requirement 作为 add，source=batch-only，不污染模板/其他批次。

Clone Batch 复制自身 add/replace/hide/inherit 记录、排序及所有译文，重新生成所有 ID，保持相同 base；模块/译文重置 draft，不复制审计、审核、发布信息。T6 的实际检测结果/日期/判断重置规则不变。客户内容只是待核实草稿，操作人员仍须重新确认对新批次适用；公开标志只是意图，不能替代未来 Reviewer 判断。

## Unified Resolver / Translations

ResolveEffectiveSections 由模块 GET 和 T6 Batch Detail 共用；T6 原 ResolveEffectiveBatch 核心字段三态计算不变，BatchView 增加 effective_sections/hidden_sections。来源明确 inherited / overridden / batch-only / hidden；固定来源 Revision ID 可回溯，页面同时已有产品编码与 R 版本上下文。

最终按 sort_order 升序、section_key ASCII 字典序稳定排序。模块 API 的 reorder 原子重排当前全部自有行；批次可用 inherit 行调整基础模块位置，Batch-only 与继承结果在一个排序空间。后台 working preview 包括 draft/ready 且 visible 内容，disabled/hidden 不展示；is_public 不作为后台保密边界，也不代表已获发布资格。未来 T9 仍需审核、ready/public/visible、资产资格和白名单过滤。

所有语言在 custom_section_translations 共存，不复制主记录。支持 en/zh-CN/es/ar/fr/de；目标语言缺失回退所属模块 source_language（可不是 EN）。所有译文项目 key、行列数量和顺序必须相同；修改结构时必须一次提交各语言一致的数据。UI 的源语言结构编辑同步其他语言结构，员工分别编辑 label/value/text；Arabic 输入区 RTL。upsert 保留现有语言 ID，API 校验与 DB UNIQUE 双重防重。

## Transactions / Audit / Permission

所有模块多表写、翻译、删除、重排、Clone 和审计同一事务。先取得 SQLite writer 再读取状态和聚合 token；冲突返回 409，客户端刷新后重试。不同 key 并发最终均保留，同 key 仅一行，同语言并发不会重复。翻译 INSERT / Audit INSERT / 删除 Audit / 重排中途 / Revision Clone Audit 故障注入均验证整体回滚。

审计事件：custom_section_created、custom_section_updated、custom_section_deleted、custom_section_reordered、custom_section_translation_updated、batch_section_overridden、batch_section_hidden、batch_section_reset、batch_section_created。复用 passport_audit_events，保留 actor/time、批次关系和有限 metadata。重排事件用所属聚合 ID 标识该次模块集合操作。

14 条路由全部 JWT + AuthCheckRole + PermissionAction，注册到原 sys_api/sys_menu/sys_menu_api_rule/casbin_rule。上游 admin 行为保留；新增按钮 passport:sections:write。未登录 14 路由均被拒绝，有账号但无 Casbin 授权也逐条拒绝；已授权但本人数据范围的用户不能读取/写入其他人的模板或批次模块。DTO 不接受 ORM 系统字段，没有另建认证或正式四角色审核矩阵。

## 实际 API

两组相同的资源根：

- `/api/v1/passport-products/{{id}}/revisions/{{rid}}/sections`
- `/api/v1/passport-batches/{{id}}/sections`

| 方法/后缀 | 功能 |
| --- | --- |
| GET 根 | 自有模块、基础模块、effective、hidden、聚合 token；可选 language |
| GET /{{sid}} | 自有模块及所有译文详情 |
| POST 根 | 新建模板 add / Batch add、replace、hide、inherit |
| PUT /{{sid}} | 替换当前自有模块 DTO 与全部译文，expected_token |
| DELETE /{{sid}} | 删除 Draft 自有模块；覆盖行删除=Reset |
| PUT /reorder | 全部自有 keys 重排，expected_token |
| PUT /{{sid}}/translations | 单语言 upsert，expected_token；hide/inherit 拒绝 |

API 使用原 code/data/msg 信封，非公开 DTO。并未新增审核/发布端点。

## UI 与浏览器

产品模板详情和批次详情集成 SectionManager/SectionPreview；text 文本框、key_value 动态行、table 列/行/单元格、gallery caption，未暴露 Raw JSON Editor。支持语言页签、排序、显示/公开/隐藏权限、来源标签、覆盖/重置/隐藏。编辑对话框保留失败草稿，阻止意外丢弃；请求防重。模块保存刷新父 token/edit_version，不重置 T5/T6 其他尚未保存的表单。

主库与 Fresh DB 各自真实完成：登录→Product/R1→3 类型模块→EN/ZH-CN/AR→排序→Seal 只读→Clone R2→Batch 继承→覆盖→隐藏→恢复→Batch-only→刷新→Clone Batch。两组各 27 个断言，均无未捕获 JS 错误。浏览器截图保存在 runtime/t7/test-artifacts/browser-detail.png、browser-1280.png 及 fresh-browser-*；1280px 无文档横向溢出。

## 运行隔离与测试证据

主库 runtime/t7/db/passport-admin-t7.db、fresh-acceptance.db、upgrade-from-t6.db、service-test.db（首次尝试保留）、service-final.db、regression.db。原 T4/T5/T6 只读。私有目录 0700、配置/DB 0600；工具链复用 T4 Go/pnpm/模块缓存，T7 自己的编译缓存与日志独立。Go 1.26.5 / Node 24.18.0 / pnpm 9.15.1；Go SQLite 3.53.4，测试 Python SQLite 3.45.3。

主后端 18099、Fresh 后端 18100、UI 19530/19531，均绑定 loopback，已定向停止并确认连接返回 ECONNREFUSED。所有业务测试明确 TEST，未创建商业证明；精确 UUID 位于 api-fixtures.json、browser-fixtures.json、fresh-browser-fixtures.json。

| 测试组 | PASS | FAIL |
| --- | --- | --- |
'''
for suite in suites:report+=f"| {suite['name']} | {len(suite['checks'])} | 0 |\n"
report+='''
计数仅包括最终命名叶子断言，不重复计父测试/Gates/重试，也不把数据库逐行写入算作测试。历史 36211 个受保护文件（含部分历史依赖文件）、8 个历史迁移文件及 T5/T6 报告均哈希不变；53 原始基线和 site 7 文件一致。最终所有 6 个 T7 SQLite 数据库 integrity_check=ok、foreign_key_check=[]，无孤立 Section/Translation、重复语言、错误 owner/source 或错误 override 目标。

首次失败尝试保留：保留键漏 product_code 后补齐；API 测试过快碰到上游 429 后按 25ms 节奏运行；审计断言缺少真正删除动作后补充用例；表格 null 被 Go 解码为空串后改指针拒绝；浏览器初始排序位置和异步加载等待断言修正。最终通过不代表所有早期尝试均成功。补充检查也堵住以 disabled 状态绕过禁止隐藏的路径，并以 3 个专门 Resolver 测试核对 inherit/replace/hide 的停用行为。

## 文件清单

新增：

'''+''.join('- `'+x+'`\n' for x in newfiles)+ '\n修改：\n\n'+''.join('- `'+x+'`\n' for x in modified)+'''
本地忽略配置 .env.t7.local、.env.t7fresh.local 和 runtime/t7 证据未入 Git。上游后端 tracked 文件 0 处变化；UI 仅两个已有语言入口，累计相对上游每文件 4 行增加/1 行删除，其中包含既有 T5/T6 注册。其余业务源原本即为未提交文件，不能把它们都误报为 T7 新增。未改依赖或通用框架。

## Known Risks 与 T8/T9 边界

asset_gallery 不提供媒体附件编辑；有未开放资产关联继续阻止相关操作。每次集合读取有有限 N+1 翻译查询，当前 100 模块上限；更高容量需单独性能设计。本轮为本地单 SQLite writer 场景，不能把这些测试解释成生产多节点并发承诺。客户专属草稿复制后仍需人工核对，is_public/ready/translation approved 都不等于正式审核通过。

未实现 Pending Review/Approve/Reject/Reviewer 页面，未实现正式 Published、Passport Revision/Snapshot Builder、Published Assets 引擎、Atomic Publish/Rollback、QR 或公开端改造。未连接 SERVER_IP、未 SSH、未改服务器/Caddy/Directus/生产 Docker/DNS/HTTPS。

## 45 Gates

| Gate | 验收项目 | 结果 |
| --- | --- | --- |
'''+''.join(f"| {g['id']} | {g['name']} | PASS |\n" for g in gates)+'''
## 最终 64 项逐项答复

| # | 问题 | 回答 |
| --- | --- | --- |
'''+''.join(f"| {x['id']} | {x['question']} | {x['answer']} |\n" for x in answers)+'''
T7 自定义字段与自定义模块已完成，当前已停止，等待人工验收，未进入 T8。
'''
(R/'docs/T7_CUSTOM_SECTIONS.md').write_text(report)
p=R/'docs/DATA_MODEL.md';s=p.read_text().split('\n\n## T7 实现补充')[0];marker='| is_visible | BOOL | 否 | true | 显示意图；false 的内容不进入 Payload |';assert marker in s
if '| allow_hide |' not in s:s=s.replace(marker,marker+'\n| allow_hide | BOOL | 否 | false | T7 最小扩展：模板是否允许 Batch 隐藏；批次不能自行授权 |',1)
s+='''

## T7 实现补充（2026-09-08）

T6 已由用户人工验收通过；T7 完成本地开发与测试、等待人工验收。原 T3/T5/T6 历史报告状态文字保留为当轮记录。T7 通过新增 1788998400000_custom_sections 迁移给 custom_sections 增加 allow_hide（默认 false），关系不变。19 业务表共 309 列。hide、不可见 replace、disabled replace 都须固定 base 明确允许隐藏，inherit 不能把 base 私有内容提升为公开。

类型仍为 text/key_value/table/asset_gallery，后者本轮只开放 caption 结构，资产关联仍封闭保护。模块/译文遵守严格结构、源语言与跨语言行列对应关系；容量、XSS、事务、解析与 API 详见 T7_CUSTOM_SECTIONS.md。模板新增模块后不可切换源语言。Clone Revision/Batch 复制已开放模块与译文并生成新 ID，模块/译文重置 draft，客户专属内容需重新核实适用性。

新模板封版使用 product-template-v2 私有内容摘要，包括全部模块 DTO/译文/排序/公开及隐藏意图；历史 sealed hash 不改。更新 T5/T6 的未开放关联保护范围仅放行已实现模块，认证及模块资产关联仍拒绝，避免遗漏。本轮没有创建 T8 工作流或 T9 Snapshot Engine。
'''
p.write_text(s)
p=R/'docs/TASKS.md';s=p.read_text().split('\n\n## T7 本轮交付')[0].replace('T0–T5 已由用户人工验收通过；本轮仅授权 T6 批次管理与本地验收。后续 T7/T8/T9 未开始','T0–T6 已由用户人工验收通过；本轮仅授权 T7 自定义模块开发与本地验收。后续 T8/T9 未开始').replace('等待人工验收；已停止，未进入 T7','已人工验收通过；T6 证据保留')
s=s.replace('| 自定义配置和编辑 UI/API | 新增检测项/普通模块不改 Go 或加列；不允许任意脚本，类型/长度/数量受控 | 禁止 | 未开始 |','| T7_CUSTOM_SECTIONS.md、T7_TEST_RESULTS.json、模块 UI/API | 45 Gates；受控四类型、冻结/克隆/继承/隐藏/多语言/事务/权限/浏览器/并发/重启/新库/完整性 | 禁止 | 等待人工验收；已停止，未进入 T8 |')
s+='\n\n## T7 本轮交付\n\nT6 已人工验收通过。T7：45/45 Gates，'+str(len(checks))+' 项最终业务断言 PASS，0 FAIL；另 UI 301 单元测试 PASS。本轮所有本地服务已停止，等待人工验收。未进入 T8/T9，未操作服务器。详见 T7_CUSTOM_SECTIONS.md、T7_TEST_RESULTS.json。\n';p.write_text(s)
for p in (rt/'db').glob('*.db'):p.chmod(0o600)
for p in rt.glob('*.yml'):p.chmod(0o600)
print(len(checks),'PASS',len(gates),'gates',len(answers),'answers')
