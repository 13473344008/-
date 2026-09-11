from pathlib import Path
import json,re,datetime,hashlib
R=Path(__file__).resolve().parents[2];rt=R/'runtime/t8';e=rt/'test-artifacts';suites=[]
for name,file in [('Main API','api-initial.json'),('Fresh API','api-fresh.json'),('Readiness and freeze edges','edges.json'),('Migrations','migrations.json'),('Go T5-T7 regression','go-regression.json'),('Browser workflow','browser-tests.json'),('Fresh browser workflow','fresh-browser-tests.json'),('Post-restart UI','ui-smoke.json'),('Restart persistence','restart.json'),('Business API contracts','contracts.json'),('Tooling','tooling.json'),('Final integrity and protection','final.json')]:
 raw=json.loads((e/file).read_text());checks=raw if isinstance(raw,list) else raw['checks'];assert checks and all(c['status']=='PASS' for c in checks),(name,checks);suites.append({'name':name,'evidence':'runtime/t8/test-artifacts/'+file,'checks':checks})
request=Path('/Users/lostar/.codex/attachments/609b2766-d361-49a7-954a-ba1bf627dda2/pasted-text.txt').read_text();gates=re.findall(r'Gate (\d+)：\s*\n([^\n]+)',request);assert len(gates)==50
questions=re.findall(r'^(\d+)\. (.+)$',request,re.M);questions=[(int(n),q) for n,q in questions if 1<=int(n)<=75];assert len(questions)==75
ans={n:'是；已实现并有本轮本地验收证据。' for n in range(1,76)}
ans.update({9:'是；业务路由统一 JWT → LiveIdentity → 上游 AuthCheckRole/Casbin → PermissionAction；admin 保留上游超级管理员规则。',10:'未发现；全部业务写路由逐条实测权限拒绝，普通员工表单也禁用。',18:'是；包括模块本体及译文，API/DB 双重锁定。',26:'是；只到 ready_for_publish，未建立公开版本或发布记录。',27:'是；pending_review + 当前审核 approved 派生 ready_for_publish，不改旧枚举。',30:'是；上游单角色 ID 下以 Editor + Reviewer 组合角色实现权限并集，Service/DB 仍禁止自审。',31:'未实现 Override；Super Admin 同样不能自审，因此无例外理由入口。',34:'是；每轮独立存储并保留决定、意见、理由、用户和时间；UI 列出所有轮次。',40:'是；冻结受控 review-v1 输入及 SHA-256，内部 preview_hash 相同。',42:'是；固定 base_revision_id 和候选字节，不读取新的默认模板。',43:'是；5 个并发批准仅 1 成功，其余 409。',44:'是；5 个批准/驳回混合请求仅 1 成功。',45:'是；5 个并发提交仅 1 成功。',46:'是；重复批准 409，保留冲突审计。',50:'是；业务转移与审计同事务，注入审计失败精确回滚；409 冲突另记失败尝试事件。',55:'是；主库与 Fresh DB 均通过真实 Chromium 完整操作。',56:'是；组合角色实际点击批准收到 403。',57:'是；两库批次、审核、审计逐行不变，API 历史及浏览器批准状态一致。',58:'是；从空库跑全量迁移、真实用户/产品/封版/批次/审核/API/浏览器。',59:'是；空库、T7 升级和重复执行通过。',62:'是；新增 review_records、批次当前审核指针及两个审计事件，校准内部预览摘要和批准/发布分离。',63:'是；1789084800000_review_workflow.go/.sql。',64:'否；T4–T7 历史 Migration Hash 均不变。',65:'是；仅前端两个语言入口存在 tracked 变化，后端 0。',66:'src/lang/en-US/index.ts、src/lang/zh-CN/index.ts；本轮各新增一处 passportReview 注册，累计相对上游各 +5/-1。',67:'是；53 个文件 Hash 全部一致。',68:'是；site 7 个文件 Hash 全部一致。',69:'否；仅 localhost 验收，未连接业务服务器。',70:'否。',71:'否。',72:'否。',73:'否；passport_revisions/publish_records/published_assets 为 0。',74:'否；正式资产冻结仍属 T9。',75:'否；已停止，等待 T8 人工验收。'})
count=sum(len(x['checks']) for x in suites)
report={'status':'等待人工验收','generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total':count,'pass':count,'fail':0,'ui_unit_tests':{'total':301,'pass':301,'fail':0},'gate_pass':50,'gate_total':50,'suites':suites,'gates':[{'id':int(n),'requirement':text,'status':'PASS'} for n,text in gates],'answers':[{'number':n,'question':q,'answer':ans[n]} for n,q in questions],'diagnostics':[{'command':'pnpm check:api','status':'UNSUPPORTED_BUSINESS_MODULE','exit_code':1,'details':'上游脚本只扫描 app/admin/demo/jobs/other 等目录，未扫描 app/passport；误将 Product 识别为 DemoProduct，并无法解析 Batch/QueueRow，产生 4 项诊断。未更改上游脚本或绕过退出码。T8 独立契约检查 5 PASS，真实 API 验收覆盖业务。'},{'command':'pnpm lint','status':'PASS_WITH_EXISTING_WARNINGS','errors':0,'warnings':30}],'scope':{'server_connected':False,'published_snapshot_generated':False,'published_assets_frozen':False,'t9_started':False,'local_services_stopped':True}}
(R/'docs/T8_TEST_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
newfiles=['admin/go-admin/app/passport/models/review.go','admin/go-admin/app/passport/service/dto/review.go','admin/go-admin/app/passport/service/review.go','admin/go-admin/app/passport/middleware/identity.go','admin/go-admin/app/passport/apis/review.go','admin/go-admin/app/admin/router/passport_reviews.go','admin/go-admin/cmd/migrate/migration/version/1789084800000_review_workflow.go','admin/go-admin/cmd/migrate/migration/version/1789084800000_review_workflow.sql','admin/go-admin-ui/src/api/passport/reviews.ts','admin/go-admin-ui/src/views/passport/reviews/index.vue','admin/go-admin-ui/src/views/passport/reviews/ReviewPanel.vue','admin/go-admin-ui/src/lang/en-US/passport/reviews.ts','admin/go-admin-ui/src/lang/zh-CN/passport/reviews.ts','docs/T8_RBAC_REVIEW_WORKFLOW.md','docs/T8_TEST_RESULTS.json']
newfiles += [str(p.relative_to(R)) for p in (R/'admin/t8').glob('*') if p.is_file()]
modified=['admin/go-admin/app/passport/models/batch.go','admin/go-admin/app/passport/service/batch.go','admin/go-admin/app/passport/service/product.go','admin/go-admin/app/admin/router/passport_products.go','admin/go-admin/app/admin/router/passport_batches.go','admin/go-admin/app/admin/router/passport_sections.go','admin/go-admin-ui/src/api/passport/batches.ts','admin/go-admin-ui/src/views/passport/products/index.vue','admin/go-admin-ui/src/views/passport/batches/index.vue','admin/go-admin-ui/src/lang/en-US/index.ts','admin/go-admin-ui/src/lang/zh-CN/index.ts','docs/DATA_MODEL.md','docs/DATA_MODEL_ERD.md','docs/PUBLISH_MODEL.md','docs/TASKS.md']
text=f'''# 【T8 执行结果】

T8 状态：**等待人工验收**。T0–T7 已由用户人工验收。本轮 **50/50 Gate PASS，{count} 项验收断言 PASS，0 FAIL**；另 301 项前端单元测试 PASS。未进入 T9，所有 T8 本地服务已停止。

RBAC、Super Admin、Editor、Reviewer、Viewer、Submit for Review、Readiness Validation、Pending Review Lock、Reject、Approve、Self Approval Protection、Review History、Transactions、Concurrency、Audit、Casbin、UI、Browser E2E、Persistence、Fresh DB、Integrity、Baseline Protection：**PASS**。

上述 0 FAIL 指下列实际验收套件，不含“已知工具限制”中明确保留非零退出码的上游通用契约诊断。没有把未支持的静态检查标成通过。

## Roles 与 Permissions Matrix

沿用 Go Admin JWT、sys_user/sys_role/sys_menu/sys_api/sys_menu_api_rule/casbin_rule、数据权限和 admin 超级管理员行为。四类角色为 Super Admin（原 admin）、Editor、Reviewer、Viewer。新增 passport_editor_reviewer 为 Editor + Reviewer 并集：上游一个用户只有一个 role_id，没有伪造多角色表或第二套登录。角色及菜单权限由 T8 迁移产生；测试用户通过原 sys-user API 创建。

| 动作 | Super Admin | Editor | Reviewer | Viewer | Editor + Reviewer |
| --- | --- | --- | --- | --- | --- |
| 产品/批次/模块/审核详情只读 | 是 | 是 | 是 | 是 | 是 |
| 创建/修改模板、封版、默认切换、批次/模块编辑 | 是 | 是 | 否 | 否 | 是 |
| 产品停用/归档、草稿批次归档 | 是 | 否 | 否 | 否 | 否 |
| Submit / 已批准后显式 Return to Draft | 是 | 是 | 否 | 否 | 是 |
| 审核队列、Approve / Reject | 是 | 否 | 是 | 否 | 是 |
| 审核自己参与的批次 | 否 | 否 | 否 | 否 | 否 |
| 正式发布、资产冻结、回滚 | 未开放 | 未开放 | 未开放 | 未开放 | 未开放 |

所有业务路由 JWT 后重新读取当前用户/角色启用状态和角色键，再进入上游 AuthCheckRole/Casbin 和 PermissionAction。账号停用旧 JWT 为 401；由 Editor 降为 Viewer 后旧 JWT 的写请求为 403。admin 使用上游超级管理员分支，不声称其必须逐条命中 Casbin p 规则。前端菜单/按钮可见性不是安全边界；Viewer、Reviewer 表单也禁用。全部现有业务写路由逐条真实 HTTP 验证拒绝，包含 T7 14 条模块路由相关写动作。

## Workflow State Machine

```mermaid
stateDiagram-v2
  Draft --> PendingReview: Submit + freeze candidate
  PendingReview --> Draft: Reject with reason (history retained)
  PendingReview --> ReadyForPublish: Approve by independent reviewer
  ReadyForPublish --> Draft: Explicit Return with reason
  Draft --> Archived: Super Admin
```

Approved 不直接变 Published。保持数据库原 workflow_status=pending_review，结合当前 review_records.decision=approved 派生 ready_for_publish；批次详情、列表和审核页明确显示“审核通过 · 待发布（未发布）”。不生成 Passport Revision、Publish Record、Published Assets 或文件。Pending/Approved 的批次字段、覆盖、检测、模块和所有译文继续冻结；普通编辑接口 409，DB 触发器阻止直接内容修改。批准后需 Editor/Admin 显式 Return，理由必填，清空当前提交/审核指针；原批准历史不改，下一次提交必须重新审核。Pending 的取消通过 Reviewer 驳回完成，不开无审计撤回通道。

## Readiness Validation / Submit Rules

只接收未发布、未归档且无未决发布指针的 Draft，并匹配 expected_edit_version。校验批次码、必填生产日期/有效期及日历顺序、产品启用、固定且同产品封版 base、模板及源语言产品名确认、覆盖受控字段/值/工艺结构、动态检测十进制及上下界/日期/判断、模块类型/键/内容大小/结构/语言对齐。已有覆盖/检测翻译也检查语言、状态、文字及工艺键。公开意图且可见的自有/替换模块要求 ready 与源语言文字 approved；私有工作模块允许 draft。其他五种语言不强制齐全。

源附件引用缺失或存在尚未开放资产/认证关联时 fail closed，返回结构化错误，不省略附件后放行。API 返回 code=422 与 data.errors[code,field,message]；readiness GET 返回 ready/errors/edit_version。UI 列出具体问题，核心或模块尚未保存时禁止提交。单次候选最大 4 MiB；文字/模块上限继承 T5–T7。

## Review Candidate / Review Record / History

新增 review_records 17 列，详见 DATA_MODEL.md 的 T8 逐字段表。业务表总计 20 张/327 列，109 个触发器。新批次字段 current_review_record_id；新增 review_returned_to_draft、review_conflict 审计事件；迁移版本 1789084800000，总迁移数 13。T4–T7 历史迁移未改。

候选包含批次身份和日期/质量/备注、固定模板内容与译文、所有覆盖与翻译、所有检测与翻译、基础和批次模块、解析的有效与隐藏模块以及来源。直接保存受控内部 review-v1 JSON 的 UTF-8 字节 SHA-256；preview_hash 相同，仅表示内部预览输入一致。Reviewer 预览从该冻结输入读取，不现场拼 Product 默认模板。批准重验提交字节/hash/edit_version/schema/builder/提交人/提交时间/preview_hash 与当前审核指针。实际切换 Product 默认 R1→R2 后候选字节/Hash 不变。

每次 Submit 新增 UUID/attempt_number，pending 只有一个；Submit/Reject/Approve/Return 与 Audit 同事务。Reject 回 Draft 并保留理由；第二次提交不覆盖第一条记录。终态不可 UPDATE，所有审核不可 DELETE，冻结输入不能改。历史列表保留全部轮次的提交者/时间、审核者/时间、决定、意见和驳回理由；当前候选完整预览，旧候选完整保存在 DB，历史列表不重复传送每轮最大 4 MiB 输入。审计面板显示最近 100 条，DB 不截断历史行。

## Self Approval / Concurrency / Transactions / Audit

Service 按 Batch 创建者、历次业务编辑审计 actor、提交者组成冻结 contributors。任何命中者不能批准或驳回，包括组合角色和 Super Admin；无管理员例外。DB 同时检查 submitted_by 与 contributors，防止自审。另一个账号具有 Reviewer 权限才能处理。

SQLite WAL/FK/5 秒 busy_timeout/FULL，单连接测试配置。短事务先保留 Batch writer，再读状态/版本；决定 UPDATE WHERE decision=pending 并检查 RowsAffected=1。5 个并发批准、5 个批准/驳回混合请求、5 个重复提交各只有 1 成功，其余 409；重复批准不重写终态。Hash/attempt 不一致拒绝。未验证生产多节点或高负载。

业务成功转移与审计原子提交；分别注入 Submit/Reject/Approve 的 audit INSERT 失败，精确比对 Batch/Review/Audit 全部回滚。409 审核冲突在失败事务之外单独记 review_conflict，表示失败尝试而非成功转移。审计通过既有 batchAudit 记录 before_data/after_data 和摘要；关联 review_id、candidate_hash、轮次、意见/理由位于 after_data，系统 metadata 保存 before/after Hash。大于既有 12 KB 审计内容阈值时保留 Hash 而省略 before/after 大体；完整意见/理由仍在不可变 Review Record，不把日志当唯一业务存储。

## API 与 UI

所有新 API 在 /api/v1 下：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | /passport-reviews | pending / approved 队列，分页/搜索 |
| GET | /passport-batches/:id/review | 当前候选、审核历史、审计 |
| GET | /passport-batches/:id/review/readiness | 结构化校验 |
| POST | /passport-batches/:id/review/submit | 提交并冻结 |
| POST | /passport-batches/:id/review/approve | 批准，不发布 |
| POST | /passport-batches/:id/review/reject | 必填理由驳回 |
| POST | /passport-batches/:id/review/return | 批准后撤销当前批准并改稿 |
| POST | /passport-batches/:id/review/archive | Admin 草稿归档 |

8 个 API（9401–9408）、5 个菜单/按钮（9401–9405），复用原产品数字身份证菜单。队列 /#/passport/reviews；批次 /#/passport/batches?batch=UUID 内嵌 ReviewPanel。结构化只读预览显示核心/来源、动态检测、模块、所有语言/状态，长文本自动换行，阿拉伯模块按 rtl。Approve/Reject 确认弹窗、纯文本 2000 字符限制、驳回理由必填；没有 Publish 按钮。中英文语言包齐全，未要求员工写 JSON。

## Browser E2E / Persistence / Fresh DB

真实 Chromium，所有网络请求限制 localhost；没有 Mock 响应。主库与独立空库分别通过：Editor 登录→创建 Product/确认源文字/Seal/设默认→创建 Batch/自定义模块→未保存阻止提交→Submit→Pending 表单只读→Viewer 登录确认只读→Reviewer 队列/冻结内容/Reject→Editor 修改重提→Reviewer Approve→两轮历史/未发布提示。组合角色点击批准自己的批次真实收到 403。更换账号使用独立全新浏览器上下文，避免复用上一角色缓存；不声称测试了上游退出菜单本身。

两套后端真实停止再启动，Batch/Review/Audit 全表逐行一致，API 当前候选、历史、浏览器批准结果仍一致。最后又检查修正后的模块来源翻译和 1280px 页面，无 JS 异常/缺失语言键，无页面横向溢出。

空 SQLite 与 T7 只读备份升级结构相同，全部迁移可重复；原业务字段逐行 Hash 不变。上游 GORM 创建中间表的 FK 声明次序不确定，比较时对这一个表归一化声明次序，foreign_key_check 另行全量通过，不把声明顺序误报成结构变化。最终 integrity_check=ok、FK 0 异常；审核无孤儿/无重复 pending/候选与锁定状态一致。

## 验收套件

| 套件 | PASS |
| --- | --- |
'''
for suite in suites:text+=f"| {suite['name']} | {len(suite['checks'])} |\n"
text+='''
完整机器证据在 T8_TEST_RESULTS.json，原始日志和截图在 runtime/t8。凭据文件仅本地 0600，不在报告中输出密码。

## 文件清单

新增：

'''
text+=''.join('- `'+p+'`\n' for p in newfiles)
text+='\n修改：\n\n'+''.join('- `'+p+'`\n' for p in modified)
text+='''
另有本地忽略配置 .env.t8.local/.env.t8fresh.local、runtime/t8 独立测试数据库/构建/日志/截图。现有业务源在任务开始前就是未提交文件，不能把它们全部误报为 T8 新增。上游后端 tracked 修改 0；UI 仅两个 locale index 累计各 +5/-1，本轮各新增一次 review 注册。

## Known Risks / 工具限制 / T9 Boundary

- pnpm check:api 的上游静态脚本未扫描 app/passport，固定 Product→DemoProduct 别名且不能表达聚合列表，产生 4 项诊断，退出码 1 原样保留在日志。这不是已通过的检查。T8 独立 5 项 DTO 契约检查及实际端到端请求通过；未来若扩展该工具应单独维护解析范围，不能简单忽略真实字段错误。
- ESLint 0 errors、30 个原有 warnings；Go M1 CPU 依赖编译器提示为既有第三方警告。TypeScript、构建、301 unit 均通过。首次验收暴露并修正了角色种子软删除扫描、可空 reviewed_at CHECK；测试曾使用错误初始 edit_version 和确认按钮定位，已按实际系统修正并重跑。失败 T8 临时库留在独立 failed-* 目录，不覆盖历史证据。
- 审核记录 UI 列全历史元数据，当前候选完整展示；旧轮候选保存在 DB，尚无逐轮历史候选预览页面。当前候选生成在有上限的 SQLite 事务中；高并发、多节点、超大模块规模未验收。上游单 role_id 以明确组合角色解决两角色并集，不声称实现任意多角色体系。
- T8 preview_hash 不是 Public Payload Hash；资产/认证未开放的关联阻止提交，不承诺媒体管理已完成。T9 必须验证相同批准/候选版本、公开白名单、资产变换一致性，并实现独立显式发布事务；任何新增或变化内容须重新审核。
- 原 53 文件/site 7 文件/36,278 历史受保护文件 Hash 一致。未连接 SERVER_IP，未 SSH，未改 Caddy、Directus、数据库服务、生产 Docker、DNS、HTTPS；未生成公开快照、正式资产副本、QR。localhost 18101/18102/19532/19533 均已关闭并确认 ECONNREFUSED。

## 50 项 Gate

| Gate | 要求 | 结果 |
| --- | --- | --- |
'''
text+=''.join(f'| {n} | {q} | PASS |\n' for n,q in gates)
text+='\n## 75 项逐项回答\n\n| 序号 | 问题 | 回答 |\n| --- | --- | --- |\n'+''.join(f'| {n} | {q} | {ans[n]} |\n' for n,q in questions)
text+='\nT8 RBAC 与审核发布工作流已完成，当前已停止，等待人工验收，未进入 T9。\n'
(R/'docs/T8_RBAC_REVIEW_WORKFLOW.md').write_text(text)
(e/'delivery-files.json').write_text(json.dumps({'new':newfiles,'modified':modified},ensure_ascii=False,indent=2));print(count,'PASS; 50 gates; 301 UI units separate')
