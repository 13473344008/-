# 【T12 修复后执行结果】

T12 状态：**等待人工验收**。本报告记录本地验证事实，未代替用户验收。

第一次结果：83 / 95 Gate PASS；638 PASS，3 FAIL。原报告与原运行证据完整保留。

修复后结果：**Gate 95 / 95 PASS；Tests 1144 PASS，0 FAIL**。

| 项目 | 结果 |
|---|---|
| Media Upload | PASS |
| Media Association | PASS |
| Published Asset E2E | PASS |
| Published Batch Clone | PASS |
| API Contract | PASS |
| Failure Coverage | PASS |
| Fresh E2E | PASS |
| Review | PASS |
| Publish | PASS |
| Rollback | PASS |
| Reconcile | PASS |
| Backup / Restore | PASS |
| Static Restore | PASS |
| Backend Independence | PASS |
| Integrity | PASS |
| Regression | PASS |
| Baseline Protection | PASS |

## 原12项缺口与修复

| Gate | 原根因/证据缺口 | 修复及补验 |
|---|---|---|
| 25 | 正式媒体上传/关联入口不存在，本轮 MediaAsset/PublishedAsset 均为0；未用SQL图片夹具绕过。 | 新增正式上传/关联入口，真实 PNG/JPEG 随 Candidate 规范化并冻结；替换 R2/V2 工作图片后旧文件全 Hash 不变。 |
| 32 | 按顺序从 Published 主批次 Clone，API409：仅允许编辑未锁定的 Draft 批次；PF-T12-TEST-003未建立。 | Clone 从 Draft 写操作改为受权限/版本控制的只读来源复制；允许 Draft/Published，新 Draft 重置状态/实测值，来源 Batch 全行与审计不变。 |
| 35 | 字段、检验与模块差异已验证，但没有实际图片变更，资产差异子项未覆盖。 | V2 通过 UI 覆盖 gallery 并上传新图片；API/UI Compare 出现实际 assets 差异。 |
| 43 | 本轮注入了共用发布执行器的 Rollback build 故障；未单独覆盖普通 Publish 构建失败，不提升为完整通过。 | 普通 Publishing.Publish 实测 build/write/copy:1/copy:2/validation/manifest/rename/finalize，断言注入点确实命中。 |
| 50 | 没有真实媒体输入，无法验证损坏 Published Asset。 | 独立批次真实上传图片形成独立 CAS；损坏后 Verify 失败、Rollback 409、Current 不变，恢复后通过。 |
| 60 | 静态JSON、前端与私有Manifest已独立备份；图片备份缺少真实样本。 | 备份真实 DB、私有源图片、公开 JSON/CAS 图片、Manifest 和前端，逐文件核对。 |
| 61 | 静态恢复后的无图片页面已通过；图片恢复访问未验证。 | 独立恢复目录经真实 Nginx 提供 V1/V2/V3 与所有恢复图片。 |
| 62 | 后台停止后的无图片页面通过；图片独立性未验证。 | 后台/UI 进程停止后真实浏览器图片 naturalWidth>0，HTTP 字节与 Hash 正确。 |
| 63 | SQLite路径不可访问时无图片页面通过；图片独立性未验证。 | 配置 DB 主文件/WAL/SHM 移到 offline 名称，公开版本与图片仍可访问；最后恢复原名原字节。 |
| 64 | Nginx重启及恢复根访问通过；图片子项未验证。 | 独立 Nginx quit 后从恢复根重新启动，真实图片和页面验收通过。 |
| 66 | Version immutable/ETag已通过；Asset immutable缺少实际图片响应。 | 实际 Version/Asset 响应 immutable、ETag 304；恢复图片仍 immutable。 |
| 83 | 资产集合为空，不能以空集遍历声称全量 Asset Hash 验收通过。 | 非空46条 Published Assets逐条校验 Hash/大小；9个私有媒体源逐条校验；全部Manifest确定编码一致。 |

## 实现与三个FAIL

正式媒体入口：`MediaPanel` 使用 FormData，不手设 Content-Type；支持主图与当前对象的 asset_gallery 上传、查看及Draft解除关联。必须填写纯文本标签、显式设置公开意图。扩展名/MIME/实际解码一致，仅PNG/JPEG，输入及规范化输出最多2MiB，边长4096、像素1600万；主图1张，gallery最多16张。页面显示SHA、MIME、大小与从图像读取的尺寸。服务端随机私有文件名、OpenRoot约束与0600写入；归属、权限、状态、Token、媒体记录、关联和审计在同一数据库事务内校验/写入，失败清理本次新文件。审计沿用media_replaced，以changed_fields区分upload/attach/detach；没有新增事件Schema。解除关联保留源文件；替换通过新上传完成，未增加全局DAM或任意媒体挂载入口。

Published Clone：把Clone从Draft编辑锁中分离，事务取得写锁后只读校验来源；允许Draft/Published，拒绝活动发布、Pending、Ready及Archived。新建独立Draft，保持Product/base、允许的override、检验结构及模块；重置日期/实测值/tested_on/质量/审核发布绑定。工作链接复制为新ID并指向不可变私有源；不复制Published关联。UI克隆按钮移到禁用编辑表单外，Published编辑区仍锁定。主来源全行/审计对比通过。Archived无正式归档入口，本轮只将独立辅助Draft设置为Archived来验证Clone明确409，未扩展归档业务。

原3个FAIL分别为正式媒体入口缺失、Published来源Clone409、UI test:ci中的check:api失败；现在对应正向E2E和完整CI均通过。原check:api四项诊断为Batch未解析、Product误配DemoProduct、search误配demo DTO、QueueRow未解析；原`runtime/t12/logs/ui-ci.log`与原T12报告保留。本轮增加Passport实际模型/DTO目录及显式页面绑定；没有删除断言或字段白名单豁免。临时注入未知响应字段/查询仍使检查失败。新媒体响应字段、multipart参数、权限链单独8项契约检查通过。

## Fresh DB、图片主链与版本

新库`runtime/t12-fix/db/passport-admin-t12-fix.db`从空库执行17迁移。Go1.26.5、Go SQLite3.53.4、WAL/FK1/busy_timeout5000/synchronousFULL/maxconn1；Node24.18.0、pnpm9.15.1。图片在浏览器中作为本地上传输入，私有媒体存储文件由正式API创建；没有SQL媒体夹具。

主Product PF-T12-TEST：Editor UI创建R1，正式API补全六语言与四种模块结构；UI维护25kg、上传PNG主图和JPEG gallery、Seal并设默认。UI创建001、20kg override、五项检验及批次模块。Reviewer查看冻结图片、Reject；随后首次V1审核发布通过。第一次驳回后的UI修改脚本误用了中文按钮“编辑”，且初始串行脚本未及时止于该错误；因此未把这段作为完整驳回修改证明。保留失败日志，并用set -e在V2完整重跑 Submit→Reviewer Reject→Editor真实修改→Resubmit→Approve→Admin Publish，全部通过，四次审核尝试及精确驳回原因保留。

R2真实UI Clone R1，解除主图关联后上传replacement.png，改30kg并Seal/default；旧001仍R1，新002使用R2。Published 001实际UI Clone003为Draft，先验证日期和五项实测清空，再将003作为独立媒体锁回归样本维护并发布，未把其最终状态冒充克隆刚完成状态。

普通Published→Draft尚非正式产品入口。按原T12§42明确授权，仅本地主001及故障辅助批次使用受控Candidate状态夹具，保留Current与历史；后续图片上传和业务编辑/审核/发布走正式UI/API。V2 UI覆盖gallery并上传新图、改22kg及检验值，公开两张图；Compare实际assets差异。Admin UI回滚V1为新V3，旧V1/V2完整字节不变。没有为此开放已发布对象任意编辑。

## 故障、权限与回归

普通Publish实际命中build、write、copy:1、copy:2、validation、manifest、rename、finalize八阶段，均检查命中标记。切换前失败状态failed、旧文件Current/DB头不变、旧版不变，新幂等键重试形成新版本；finalize后为recovery_required，文件已换而DB头仍旧，阻止重试，Reconcile完成同一操作。另在独立含两张正式上传图片的批次上，用SQLite BEFORE UPDATE published_at触发器制造真实数据库失败，API观察file_switched_db_pending，Publish/Rollback409，移除故障后由Admin浏览器Reconcile。故障触发器全部清理。

独立CAS图片、JSON、Manifest各自保存原字节后损坏，Verify均integrity_error、Rollback409、Current不变，finally恢复后verified。损坏图片用独立辅助图，不污染主001图片。详情见damage-details.json；Go阶段实际状态见ordinary-publish-faults.log。

Reviewer/Viewer可读但不能上传/解除，Editor可改Draft；Pending/Ready/Published/Sealed锁、跨对象拒绝、私有图片过滤、过期Token、非法MIME/扩展名/解码、超限/超像素、审计失败整体回滚均验证。T5/T6/T7核心服务106个叶测试、普通Publish故障8个叶测试；T8–T11受影响工作流/权限/并发/版本/静态公开路径以本轮API和浏览器验证。六项并发竞争无重复版本/编码/双重审核。UI原301+新增4单测通过；完整test:ci通过；prod build通过。

## Backup / Restore、全量Hash与停止

最终一致备份时间：2026-09-10T12:53:56.994377+00:00，SQLite Backup API。备份 `runtime/t12-fix/backups/t12-fix-final.db`，SHA256 `a3749fbf1f2ee4b0b2ef4e70837753e38e224172c7f536e86713fed11d8e3520`。恢复到独立restored.db，全部表行数与数据摘要一致，integrity/FK通过。日志表包含既有响应截断导致的非UTF-8文本字节；哈希脚本使用surrogateescape无损保留这些字节比较，没有跳过该表或替换坏字节。它不影响业务JSON或数据库完整性，但日志截断的UTF-8处理仍可另行改进。

DB、私有源media、releases/Manifest、公开JSON/CAS及前端分别备份并恢复到独立目录。真实Nginx退出后从恢复根重新启动；后台18111、UI19543停止，配置DB及存在的WAL/SHM移为offline名称，公开六语言/RTL/五尺寸和真实图片通过；V1/V2/V3及全部恢复CAS图片HTTP字节/Hash正确。随后恢复DB原名原字节，最终18111/18112/19543/19544均关闭。

数据计数：{"products": 5, "product_revisions": 11, "batches": 18, "custom_sections": 32, "review_records": 27, "passport_revisions": 32, "publish_records": 32, "media_assets": 9, "asset_links": 10, "published_assets": 46, "passport_audit_events": 271, "unlinked_private_media_retained": 2}。2条解除关联后的媒体源按设计保留，不是悬空外键；foreign_key_check空，无重复revision/batch/review/published版本，无残留活动发布或测试触发器。全部已封存JSON与数据库payload/hash相符、每条PublishedAsset及私有源Hash/大小相符、Manifest全字段确定编码相符，包括保留的失败prepared诊断。53文件基线、site7文件、31854历史受保护文件及原T12两份失败报告不变。

性能样本：HTML 1417B、CSS 5632B、公开JS 35159B、V3 Current JSON 9287B、两张图合计31362B；最大主链图片26371B。六语言、375/390/430/1280/1440px无横向溢出，图片懒加载实际成功。只代表本机测试样本，不是生产容量承诺。

## 文件与Migration

修改已有文件（以本轮source-before为基准，而非混入T4–T11未提交文件）：

- `admin/go-admin/app/passport/service/section.go`
- `admin/go-admin/app/passport/service/batch.go`
- `admin/go-admin/app/passport/service/product.go`
- `admin/go-admin-ui/src/views/passport/sections/SectionManager.vue`
- `admin/go-admin-ui/src/views/passport/products/index.vue`
- `admin/go-admin-ui/src/views/passport/batches/index.vue`
- `admin/go-admin-ui/src/lang/zh-CN/index.ts`
- `admin/go-admin-ui/src/lang/en-US/index.ts`
- `admin/go-admin-ui/scripts/check-api-contract.mjs`
- `docs/TASKS.md`

新增业务/测试源码：

- `admin/go-admin/app/passport/service/media.go`
- `admin/go-admin/app/passport/apis/media.go`
- `admin/go-admin/app/admin/router/passport_media.go`
- `admin/go-admin/cmd/migrate/migration/version/1789430400000_media_permissions.go`
- `admin/go-admin/app/passport/service/t12_fix_publish_test.go`
- `admin/go-admin-ui/src/api/passport/media.ts`
- `admin/go-admin-ui/src/views/passport/media/MediaPanel.vue`
- `admin/go-admin-ui/src/lang/en-US/passport/media.ts`
- `admin/go-admin-ui/src/lang/zh-CN/passport/media.ts`
- `admin/go-admin-ui/tests/unit/components/passport-media.spec.ts`

另新增`admin/t12-fix/`验收脚本、独立`runtime/t12-fix/`证据，以及本报告和机器结果；TASKS更新为等待人工验收。新迁移1789430400000仅增加媒体菜单/API/Casbin授权，无业务DDL。空库17迁移与重复执行通过；原T12数据库的独立复制库升级后，全部业务表Hash不变，只有权限表、迁移记录及其SQLite自增计数改变。没有修改历史迁移或原库数据。

## 计数与已知边界

| 套件 | PASS | FAIL | 证据 |
|---|---:|---:|---|
| flow-prepare | 4 | 0 | runtime/t12-fix/test-artifacts/flow-prepare.json |
| browser-create | 4 | 0 | runtime/t12-fix/test-artifacts/browser-create.json |
| browser-upload-seal | 9 | 0 | runtime/t12-fix/test-artifacts/browser-upload-seal.json |
| browser-batch | 4 | 0 | runtime/t12-fix/test-artifacts/browser-batch.json |
| browser-inspections | 5 | 0 | runtime/t12-fix/test-artifacts/browser-inspections.json |
| working | 14 | 0 | runtime/t12-fix/test-artifacts/working.json |
| flow-pending | 8 | 0 | runtime/t12-fix/test-artifacts/flow-pending.json |
| browser-submit | 5 | 0 | runtime/t12-fix/test-artifacts/browser-submit.json |
| browser-reject | 5 | 0 | runtime/t12-fix/test-artifacts/browser-reject.json |
| browser-adjust | 4 | 0 | runtime/t12-fix/test-artifacts/browser-adjust.json |
| browser-resubmit | 5 | 0 | runtime/t12-fix/test-artifacts/browser-resubmit.json |
| browser-approve | 5 | 0 | runtime/t12-fix/test-artifacts/browser-approve.json |
| browser-publish | 4 | 0 | runtime/t12-fix/test-artifacts/browser-publish.json |
| v1-checks | 3 | 0 | runtime/t12-fix/test-artifacts/v1-checks.json |
| public-browser-v1 | 33 | 0 | runtime/t12-fix/test-artifacts/public-browser-v1.json |
| browser-clone | 4 | 0 | runtime/t12-fix/test-artifacts/browser-clone.json |
| clone-checks | 12 | 0 | runtime/t12-fix/test-artifacts/clone-checks.json |
| browser-r2 | 6 | 0 | runtime/t12-fix/test-artifacts/browser-r2.json |
| v2-prepare | 4 | 0 | runtime/t12-fix/test-artifacts/v2-prepare.json |
| browser-v2-edit | 5 | 0 | runtime/t12-fix/test-artifacts/browser-v2-edit.json |
| v2-checks | 7 | 0 | runtime/t12-fix/test-artifacts/v2-checks.json |
| public-browser-v2 | 33 | 0 | runtime/t12-fix/test-artifacts/public-browser-v2.json |
| browser-rollback | 5 | 0 | runtime/t12-fix/test-artifacts/browser-rollback.json |
| v3-checks | 8 | 0 | runtime/t12-fix/test-artifacts/v3-checks.json |
| media-checks | 23 | 0 | runtime/t12-fix/test-artifacts/media-checks.json |
| media-workflow-checks | 13 | 0 | runtime/t12-fix/test-artifacts/media-workflow-checks.json |
| contracts | 8 | 0 | runtime/t12-fix/test-artifacts/contracts.json |
| fault-prepare | 8 | 0 | runtime/t12-fix/test-artifacts/fault-prepare.json |
| db-failure | 8 | 0 | runtime/t12-fix/test-artifacts/db-failure.json |
| browser-reconcile | 4 | 0 | runtime/t12-fix/test-artifacts/browser-reconcile.json |
| damage-checks | 15 | 0 | runtime/t12-fix/test-artifacts/damage-checks.json |
| concurrency | 10 | 0 | runtime/t12-fix/test-artifacts/concurrency.json |
| browser-admin-pages | 10 | 0 | runtime/t12-fix/test-artifacts/browser-admin-pages.json |
| public-browser-full | 46 | 0 | runtime/t12-fix/test-artifacts/public-browser-full.json |
| http-checks | 28 | 0 | runtime/t12-fix/test-artifacts/http-checks.json |
| static-checks | 49 | 0 | runtime/t12-fix/test-artifacts/static-checks.json |
| migration-backup | 8 | 0 | runtime/t12-fix/test-artifacts/migration-backup.json |
| upgrade-check | 4 | 0 | runtime/t12-fix/test-artifacts/upgrade-check.json |
| final-verify | 145 | 0 | runtime/t12-fix/test-artifacts/final-verify.json |
| offline-verify | 69 | 0 | runtime/t12-fix/test-artifacts/offline-verify.json |
| backup-restore | 11 | 0 | runtime/t12-fix/test-artifacts/backup-restore.json |
| independence | 4 | 0 | runtime/t12-fix/test-artifacts/independence.json |
| public-browser-stopped | 33 | 0 | runtime/t12-fix/test-artifacts/public-browser-stopped.json |
| restored-http | 23 | 0 | runtime/t12-fix/test-artifacts/restored-http.json |
| stopped | 5 | 0 | runtime/t12-fix/test-artifacts/stopped.json |
| core-regression | 106 | 0 | runtime/t12-fix/logs/core-regression.log |
| ordinary-publish-faults | 8 | 0 | runtime/t12-fix/logs/ordinary-publish-faults.log |
| UI unit (301 existing + 4 media) | 305 | 0 | runtime/t12-fix/logs/ui-ci-retry.log |
| Full CI lint/type/API/i18n | 4 | 0 | runtime/t12-fix/logs/ui-ci-retry.log |
| UI production build | 1 | 0 | runtime/t12-fix/logs/ui-build.log |

Only final assertions and Go leaf tests, UI305; command checks separately4+build1. Historical638/3 not included. Failed harness attempts retained and superseded, not counted as unresolved final test failures. Browser phases rerun onV2 use their final successful JSON; earlier actual V1 log evidence retained.

失败脚本尝试原日志保留：日期选择器、中文按钮、已克隆Draft的日期/模块未确认、归档路由不存在、日志非UTF8哈希读取、升级自增元数据计数差异；逐一纠正测试前置条件/定位/比较口径并重跑，未删除产品安全拒绝或降低业务断言。失败截图及旧轮次结果不算本轮未解决FAIL，也不伪装为首次全部成功。

本轮未构建通用DAM/PDF/SVG/WebP上传、跨对象媒体库/GC/自动扫描；上传后更改公开意图通过Draft解除并重新上传实现。没有生产负载、真实断电、远程备份或异机恢复证据。现有本地SQLite方案不等于生产多写实例可行。既有日志响应截断按字节可能产生非UTF8日志，应作为后续维护项处理。

部署边界：原T13_DEPLOYMENT_PRECHECK.md仅历史设计清单，其“媒体/PublishedClone缺口”在本轮已经修复；正式Published→Draft产品边界、测试/生产隔离、源媒体/Manifest/CAS协同备份、运行时权限/资源/代理路径仍须后续明确。清单中的独立Compose、先测试后生产、共享代理变更事前确认、保留旧发布并只回退本项目仍适用。本轮没有实施任何部署，也未生成生产QR。

## 27项特别答复

1. 是。新增三个对象范围、九条带 JWT/LiveIdentity/Casbin/数据范围约束的媒体路由；只接收 PNG/JPEG。

2. 是。普通 Editor 在真实 Chromium 中上传主图 PNG、gallery JPEG，并在 R2/V2 上传替换图片。

3. 是。新库共9条 MediaAsset，全部通过正式上传 API 建立；含2条解除关联后保留的私有源。

4. 是。关联 ProductRevision 主图、Product gallery 与 Batch gallery；通过对象归属、Draft锁和乐观Token检查。

5. 是。Working/Review真实含图预览；提交冻结规范化图像及源Hash，Reviewer浏览器查看。

6. 是。实际产生46条 PublishedAsset记录；与工作关联隔离，封存后不可变。

7. 是。V1/V2/V3及恢复副本真实图片加载通过，PNG/JPEG均生成安全PNG公开副本。

8. 是。R2解除旧主图并上传新图，V2替换gallery；V1/V2已有JSON及图片字节保持不变。

9. 是。Published来源通过Editor UI克隆成新Draft；Draft及回滚后的Published也通过。

10. 是。主来源Batch全行及其审计记录前后完全一致；没有解锁或修改来源批次。

11. 是。新对象无旧Review/Publish/PassportRevision/Current关系；只复制工作模板关联，重新分配关联ID。

12. 是。五项检验结构保留，numeric/text/tested_on及结论重置；日期默认null，质量pending。

13. 是。正式媒体入口缺失、Published Clone 409、通用契约检查失败均已修复并补证。

14. 是。原25/32/35/43/50/60/61/62/63/64/66/83均PASS，逐项证据见下表。

15. 是。新媒体参数/响应/权限独立契约检查通过，真实正负请求通过，完整test:ci通过。

16. 是。原日志和失败报告保留四项诊断原文。本轮修正Passport模型/DTO绑定，未删除检查；未知字段/查询注入仍失败。

17. 是。普通Publish第二张图复制失败实际命中，旧Current不变；另覆盖复制第一张及其余六阶段。

18. 是。普通Publish的实际SQLite触发器制造finalize失败，file_switched_db_pending阻止新发布/回滚；Admin浏览器Reconcile确认同一记录。

19. 是。全新T12-fix空库17迁移，图片由正式UI/API输入，完整审核发布、V2、回滚和恢复通过；媒体未用SQL或手工置入私有目录。

20. 是。后台/UI停止且配置DB文件离线，公开图片仍可访问。

21. 是。独立恢复公开目录经重启Nginx，V1/V2/V3和全部恢复CAS图片通过HTTP Hash验证。

22. 是。工作库、独立恢复库与升级副本integrity_check均为ok。

23. 是。foreign_key_check为空，无悬空外键。

24. 是。全量已封存JSON、46条PublishedAsset、9个私有源及Manifest均一致。

25. No。没有修改T4–T11历史Migration。只新增1789430400000权限迁移，不变更媒体/工作流业务Schema。

26. No。没有连接服务器；未访问SERVER_IP、Caddy、Directus、生产Docker、DNS或HTTPS。

27. No。未进入T13，T14也未进入。等待本轮人工验收；不以本地通过替代部署授权。

## 原95 Gate最终结果

以下文件名默认位于runtime/t12-fix/test-artifacts，logs例外位于runtime/t12-fix。边界Gate以本轮实际工具操作范围核对，未以连接服务器验证“没有连接”。

| Gate | 条件 | 最终 | 证据 |
|---:|---|---|---|
| 1 | Fresh DB 从零建立。 | PASS | environment.json; logs/migrate-first.log; migration-backup.json |
| 2 | 所有 Migration 成功。 | PASS | environment.json; logs/migrate-first.log; migration-backup.json |
| 3 | Migration 重复执行安全。 | PASS | migration-backup.json; upgrade-check.json |
| 4 | 四角色可用。 | PASS | working.json; flow-pending.json; media-checks.json; media-workflow-checks.json; concurrency.json |
| 5 | RBAC 核心回归通过。 | PASS | working.json; flow-pending.json; media-checks.json; media-workflow-checks.json; concurrency.json |
| 6 | Product 创建通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 7 | Revision 创建通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 8 | 六语言通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 9 | Custom Sections 四类型通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 10 | Revision Seal 通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 11 | Default Revision 通过。 | PASS | browser-create.json; flow-prepare.json; browser-upload-seal.json; browser-r2.json |
| 12 | Batch 创建绑定正确 Revision。 | PASS | browser-batch.json; browser-inspections.json; working.json; browser-submit.json |
| 13 | Override 通过。 | PASS | browser-batch.json; browser-inspections.json; working.json; browser-submit.json |
| 14 | Inspection 动态模型通过。 | PASS | browser-batch.json; browser-inspections.json; working.json; browser-submit.json |
| 15 | Batch Custom Sections 通过。 | PASS | browser-batch.json; browser-inspections.json; working.json; browser-submit.json |
| 16 | Working Preview 正确。 | PASS | browser-batch.json; browser-inspections.json; working.json; browser-submit.json |
| 17 | Submit 通过。 | PASS | browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json |
| 18 | Pending Lock 通过。 | PASS | working.json; flow-pending.json; media-checks.json; media-workflow-checks.json; concurrency.json |
| 19 | Reject 通过。 | PASS | browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json |
| 20 | 再次 Submit 保留历史。 | PASS | browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json |
| 21 | Approve 通过。 | PASS | browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json |
| 22 | Self Approval 阻止。 | PASS | working.json; flow-pending.json; media-checks.json; media-workflow-checks.json; concurrency.json |
| 23 | Publish V1 通过。 | PASS | browser-upload-seal.json; browser-publish.json; v1-checks.json; v2-prepare.json; final-verify.json |
| 24 | Public Payload 白名单正确。 | PASS | final-verify.json; offline-verify.json |
| 25 | Published Assets 冻结正确。 | PASS | browser-upload-seal.json; browser-publish.json; v1-checks.json; v2-prepare.json; final-verify.json |
| 26 | Stable URL 显示 V1。 | PASS | public-browser-v1.json |
| 27 | History V1 正确。 | PASS | public-browser-v1.json |
| 28 | 六语言 Public 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 29 | Public RTL 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 30 | R2 Default 不改变旧 Batch。 | PASS | v2-prepare.json |
| 31 | 新 Batch 使用 R2。 | PASS | v2-prepare.json |
| 32 | Clone Batch 规则正确。 | PASS | browser-clone.json; clone-checks.json; media-workflow-checks.json; v3-checks.json |
| 33 | V2 测试发布通过。 | PASS | browser-v2-edit.json; v2-checks.json; version-compare.json; public-browser-v2.json |
| 34 | V1/V2 历史独立。 | PASS | browser-v2-edit.json; v2-checks.json; version-compare.json; public-browser-v2.json |
| 35 | Version Compare 正确。 | PASS | browser-v2-edit.json; v2-checks.json; version-compare.json; public-browser-v2.json |
| 36 | Rollback 生成新 V3。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 37 | Rollback 不覆盖 V1/V2。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 38 | Stable URL 显示 V3。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 39 | Review History 完整。 | PASS | browser-submit.json; browser-reject.json; browser-adjust.json; browser-resubmit.json; browser-approve.json; v2-checks.json |
| 40 | Publish History 完整。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 41 | Audit Timeline 完整。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 42 | V1/V2/V3 Integrity 全部 PASS。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 43 | Publish 前故障安全。 | PASS | logs/ordinary-publish-faults.log; faults.json |
| 44 | Switch 前故障安全。 | PASS | logs/ordinary-publish-faults.log; faults.json |
| 45 | Switch 后 DB Fail 正确进入 Reconcile。 | PASS | db-failure.json; browser-reconcile.json; damage-checks.json |
| 46 | Reconcile 恢复一致。 | PASS | db-failure.json; browser-reconcile.json; damage-checks.json |
| 47 | Reconcile 状态阻止 Publish。 | PASS | db-failure.json; browser-reconcile.json; damage-checks.json |
| 48 | Reconcile 状态阻止 Rollback。 | PASS | db-failure.json; browser-reconcile.json; damage-checks.json |
| 49 | 损坏 JSON 被检测。 | PASS | damage-checks.json; damage-details.json |
| 50 | 损坏 Asset 被检测。 | PASS | damage-checks.json; damage-details.json |
| 51 | 损坏版本禁止 Rollback。 | PASS | damage-checks.json; damage-details.json |
| 52 | 关键并发测试通过。 | PASS | concurrency.json; final-verify.json |
| 53 | 无重复 Revision。 | PASS | concurrency.json; final-verify.json |
| 54 | 无重复 Batch Code。 | PASS | concurrency.json; final-verify.json |
| 55 | 无双重 Review。 | PASS | concurrency.json; final-verify.json |
| 56 | 无重复 Published Version。 | PASS | concurrency.json; final-verify.json |
| 57 | Backup 成功。 | PASS | backup-restore.json |
| 58 | Restore 成功。 | PASS | backup-restore.json |
| 59 | Restore 数据完整。 | PASS | backup-restore.json |
| 60 | Static Release Backup 成功。 | PASS | backup-restore.json |
| 61 | Static Restore 后 Public 正常。 | PASS | backup-restore.json; independence.json; restored-http.json; public-browser-stopped.json |
| 62 | Backend 停止 Public 正常。 | PASS | backup-restore.json; independence.json; restored-http.json; public-browser-stopped.json |
| 63 | SQLite 不可访问 Public 正常。 | PASS | backup-restore.json; independence.json; restored-http.json; public-browser-stopped.json |
| 64 | Nginx 重启 Public 正常。 | PASS | backup-restore.json; independence.json; restored-http.json; public-browser-stopped.json |
| 65 | Current Cache 更新正确。 | PASS | http-checks.json; restored-http.json; public-browser-v1.json; public-browser-v2.json; public-browser-full.json |
| 66 | Version/Asset Immutable Cache 正确。 | PASS | http-checks.json; restored-http.json; public-browser-v1.json; public-browser-v2.json; public-browser-full.json |
| 67 | 375px 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 68 | 390px 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 69 | 430px 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 70 | 1280px 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 71 | 1440px 通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 72 | Admin 关键页面回归通过。 | PASS | browser-rollback.json; v3-checks.json; main-history.json; browser-admin-pages.json |
| 73 | Public Network 无 Admin API。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 74 | Public Network 无 JWT。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 75 | XSS 回归通过。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 76 | Path Traversal 回归通过。 | PASS | http-checks.json; restored-http.json; public-browser-v1.json; public-browser-v2.json; public-browser-full.json |
| 77 | Symlink Escape 回归通过。 | PASS | http-checks.json; restored-http.json; public-browser-v1.json; public-browser-v2.json; public-browser-full.json |
| 78 | Unknown Schema 安全失败。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 79 | Malformed JSON 安全失败。 | PASS | public-browser-full.json; public-browser-stopped.json |
| 80 | integrity_check = ok。 | PASS | final-verify.json; offline-verify.json |
| 81 | foreign_key_check 无异常。 | PASS | final-verify.json; offline-verify.json |
| 82 | JSON Hash 全量一致。 | PASS | final-verify.json; offline-verify.json |
| 83 | Asset Hash 全量一致。 | PASS | final-verify.json; offline-verify.json |
| 84 | Manifest 全量一致。 | PASS | final-verify.json; offline-verify.json |
| 85 | 测试服务最终全部停止。 | PASS | stopped.json |
| 86 | 原基线保护通过。 | PASS | final-verify.json; offline-verify.json |
| 87 | 未连接服务器。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |
| 88 | 未修改 Caddy。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |
| 89 | 未修改 Directus。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |
| 90 | 未修改生产 Docker。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |
| 91 | 未生成生产正式二维码。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |
| 92 | T13 部署前配置清单完成。 | PASS | docs/T13_DEPLOYMENT_PRECHECK.md（历史设计清单）；本报告部署边界补充；未执行部署 |
| 93 | T13 部署顺序完成。 | PASS | docs/T13_DEPLOYMENT_PRECHECK.md（历史设计清单）；本报告部署边界补充；未执行部署 |
| 94 | 部署回退方案完成。 | PASS | docs/T13_DEPLOYMENT_PRECHECK.md（历史设计清单）；本报告部署边界补充；未执行部署 |
| 95 | 未进入 T13。 | PASS | 本轮仅 localhost 工具操作记录；无服务器/共享组件/生产QR操作；stopped.json |

T12 修复回合已完成，95/95 Gate PASS，0 FAIL，当前已停止，等待人工验收，未进入 T13。
