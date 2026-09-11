# 【T10 执行结果】

T10 状态：**等待人工验收；本地服务已停止，未进入 T11。** T0–T9 已由用户人工验收。仅在 runtime/t10 使用独立本地 SQLite、发布目录和日志，没有连接业务服务器。

**65/65 Gate PASS；1297 项命名断言/叶测试 PASS，0 FAIL。** 含 301 项既有前端单测；不是 1297 个独立业务场景。主库 API 75 项、Fresh API 73 项，另有真实浏览器、故障、互斥、持久化、文件/Schema 和静态访问验收。精确明细见 [T10_TEST_RESULTS.json](T10_TEST_RESULTS.json)。上游通用 check:api 仍非零退出，4 条既有诊断单独记录，不伪称所有检查命令全绿。

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

- `admin/go-admin/app/passport/apis/history.go`
- `admin/go-admin/app/passport/service/history.go`
- `admin/go-admin/app/passport/service/history_test.go`
- `admin/go-admin/cmd/migrate/migration/version/1789257600000_version_history.go`
- `admin/go-admin/cmd/migrate/migration/version/1789257600000_version_history.sql`
- `admin/go-admin-ui/src/api/passport/history.ts`
- `admin/go-admin-ui/src/views/passport/history/HistoryPanel.vue`
- `admin/go-admin-ui/src/lang/en-US/passport/history.ts`
- `admin/go-admin-ui/src/lang/zh-CN/passport/history.ts`

另新增 `admin/t10/` 独立环境、测试和报告脚本；运行数据仅 `runtime/t10/`。新增本文和 T10_TEST_RESULTS.json。

## 修改文件

- `admin/go-admin/app/admin/router/passport_publication.go`
- `admin/go-admin/app/passport/apis/publish.go`
- `admin/go-admin/app/passport/models/publish.go`
- `admin/go-admin/app/passport/service/publish.go`
- `admin/go-admin/app/passport/service/review.go`
- `admin/go-admin-ui/src/api/passport/publication.ts`
- `admin/go-admin-ui/src/views/passport/publication/PublishPanel.vue`
- `admin/go-admin-ui/src/lang/en-US/index.ts`
- `admin/go-admin-ui/src/lang/zh-CN/index.ts`

文档更新：DATA_MODEL.md、DATA_MODEL_ERD.md、PUBLISH_MODEL.md、TASKS.md。上游 tracked diff 仅两个已在前序阶段修改的 UI 语言入口，其余业务文件属于先前/本轮独立模块；未修改上游后端 tracked 文件、框架 API 检查器或锁定版本。

## 65 Gates

| # | Gate | 结果 | 证据套件 |
|---|---|---|---|
| 1 | Version History 可用。 | PASS | Main API, Fresh API |
| 2 | 历史 Passport Revision 只读。 | PASS | Main API, Additional API, File Integrity |
| 3 | 历史 Published Assets 不可修改。 | PASS | Main API, Additional API, File Integrity |
| 4 | 历史 Manifest 不可覆盖。 | PASS | Publish primitives, File Integrity |
| 5 | Version Detail 可用。 | PASS | Main API, Fresh API |
| 6 | Integrity Verify 可用。 | PASS | Main API, Fresh API |
| 7 | 损坏 JSON 可检测。 | PASS | Main API, Fresh API |
| 8 | 损坏 Asset 可检测。 | PASS | Main API, Fresh API |
| 9 | 损坏 Manifest 可检测。 | PASS | Main API, Fresh API |
| 10 | 损坏历史版本禁止 Rollback。 | PASS | Main API, Fresh API |
| 11 | Rollback 仅 Super Admin。 | PASS | Main API, Fresh API |
| 12 | Editor Rollback 403。 | PASS | Main API, Fresh API |
| 13 | Reviewer Rollback 403。 | PASS | Main API, Fresh API |
| 14 | Viewer Rollback 403。 | PASS | Main API, Fresh API |
| 15 | 匿名 Rollback 401。 | PASS | Main API, Fresh API |
| 16 | Rollback Reason 必填。 | PASS | Main API, Fresh API |
| 17 | Rollback 不直接修改 Current pointer 到旧版本。 | PASS | Main API, Fresh API |
| 18 | Rollback 创建新 Passport Revision。 | PASS | Main API, Fresh API |
| 19 | Rollback Version Number 单调递增。 | PASS | Main API, Fresh API |
| 20 | Rollback Source 正确记录。 | PASS | Main API, Fresh API |
| 21 | 旧 V1/V2/V3 全部保留。 | PASS | Main API, Fresh API |
| 22 | Rollback 新 V4 Current 正确。 | PASS | Main API, Fresh API |
| 23 | Rollback Published Assets relation 完整。 | PASS | Main API, Fresh API |
| 24 | Rollback 复用内容寻址资产安全。 | PASS | Main API, Fresh API |
| 25 | Rollback 生成新 Publish Record。 | PASS | Main API, Fresh API |
| 26 | Rollback Audit 完整。 | PASS | Main API, Fresh API |
| 27 | Rollback Build 失败旧 Current 安全。 | PASS | Rollback Faults, Real DB failure, Additional API |
| 28 | Rollback Validation 失败旧 Current 安全。 | PASS | Rollback Faults, Real DB failure, Additional API |
| 29 | Rollback Switch 前失败旧 Current 安全。 | PASS | Rollback Faults, Real DB failure, Additional API |
| 30 | Switch 后 DB Failure 进入 Reconcile。 | PASS | Rollback Faults, Real DB failure, Additional API |
| 31 | Reconcile 能识别 file-switched/db-pending。 | PASS | Real DB failure, Browser Reconcile, Persistence |
| 32 | Reconcile 能完成一致性恢复。 | PASS | Real DB failure, Browser Reconcile, Persistence |
| 33 | 无法证明安全的一致性异常阻止新 Publish。 | PASS | Main API, Fresh API |
| 34 | 无法证明安全的一致性异常阻止 Rollback。 | PASS | Main API, Fresh API |
| 35 | Reconcile 仅 Super Admin。 | PASS | Main API, Fresh API |
| 36 | Reconcile 有 Audit。 | PASS | Main API, Fresh API |
| 37 | Publish History 含成功和失败记录。 | PASS | Rollback Faults, Real DB failure, Additional API |
| 38 | Review History 完整。 | PASS | Main API, Fresh API |
| 39 | Audit Timeline 完整。 | PASS | Main API, Fresh API |
| 40 | Version Compare 可用。 | PASS | Main API, Fresh API |
| 41 | JSON 业务差异准确。 | PASS | Main API, Fresh API |
| 42 | Asset Diff 准确。 | PASS | Main API, Fresh API |
| 43 | Rollback 并发只有一个安全成功。 | PASS | Main API, Fresh API |
| 44 | Publish / Rollback 并发受控。 | PASS | Main API, Fresh API |
| 45 | Rollback 双击安全。 | PASS | Main API, Fresh API |
| 46 | Version Number 不重复。 | PASS | Main API, Fresh API |
| 47 | Rollback 后可继续生成后续版本。 | PASS | Main API, Fresh API |
| 48 | Backend 重启后 History 保持。 | PASS | Persistence |
| 49 | 静态 Release 不依赖 Backend 存活。 | PASS | Backend-off Static |
| 50 | Fresh DB 全链路通过。 | PASS | Fresh API |
| 51 | Migration 可重复。 | PASS | Migration |
| 52 | integrity_check = ok。 | PASS | File Integrity |
| 53 | foreign_key_check 无异常。 | PASS | File Integrity |
| 54 | 全部 JSON Hash 复验一致。 | PASS | File Integrity |
| 55 | 全部 Asset Hash 复验一致。 | PASS | File Integrity |
| 56 | 全部 Manifest 复验一致。 | PASS | File Integrity |
| 57 | Rollback 版本完整性复验通过。 | PASS | File Integrity |
| 58 | 普通 API 不提供历史删除。 | PASS | Main API, Additional API, File Integrity |
| 59 | Audit Append-only 规则保持。 | PASS | Main API, Additional API, File Integrity |
| 60 | 原 53 个基线文件不变。 | PASS | File Integrity |
| 61 | site 7 文件不变。 | PASS | File Integrity |
| 62 | 未修改 T4-T9 历史 Migration。 | PASS | File Integrity |
| 63 | 未部署服务器。 | PASS | File Integrity, Stopped |
| 64 | 未生成正式 QR。 | PASS | File Integrity, Stopped |
| 65 | 未进入 T11。 | PASS | File Integrity, Stopped |

## 93 项逐项回答

1. **是否存在 Version History？** 是；完整 Version History 与统一 History API/面板。

2. **是否显示所有 Published Passport Revision？** 是；历史接口返回全部成功 Published 版本，不受旧 publication 最近 100 条限制。

3. **历史 Revision 是否只读？** 是；无编辑 API，Published/Sealed DB 触发器保护。

4. **历史 Asset 是否不可修改？** 是；历史逻辑资产冻结，物理文件写入禁止覆盖。

5. **历史 Manifest 是否不可覆盖？** 是；Immutable 写入禁止不同字节覆盖，每次验证原文与完整字段。

6. **是否可以查看 Version Detail？** 是；只读 JSON、来源、Manifest、资产和审计详情。

7. **是否可以查看 Payload Hash？** 是；列表展开行和详情显示。

8. **是否可以查看 Asset Hash？** 是；资产详情显示 SHA-256。

9. **是否可以验证历史 JSON Integrity？** 是；按实际原文字节复验。

10. **是否可以验证历史 Asset Integrity？** 是；逐个实际资产 Hash/size 复验。

11. **是否可以验证 Manifest Integrity？** 是；全字段及确定原文字节校验。

12. **损坏 JSON 是否被发现？** 是；篡改 T10 测试 JSON 被检测。

13. **损坏 Asset 是否被发现？** 是；篡改 T10 测试资产被检测。

14. **损坏 Manifest 是否被发现？** 是；Manifest 追加空格也被检测。

15. **损坏 Revision 是否禁止 Rollback？** 是；无管理员强制忽略开关。

16. **Rollback 是否只有 Super Admin？** 是；路由权限加 Service 当前真实角色检查。

17. **Editor Rollback 是否 403？** 是，403。

18. **Reviewer Rollback 是否 403？** 是，403。

19. **Viewer Rollback 是否 403？** 是，403。

20. **匿名 Rollback 是否 401？** 是，401。

21. **rollback_reason 是否必填？** 是；1–1000 字纯文本，拒绝空白/HTML/危险控制字符。

22. **Rollback 是否创建新版本？** 是；新 Revision、Record、Release、资产关系。

23. **Rollback 是否绝不覆盖旧版本？** 是；保留原行、Manifest、JSON、资产。

24. **V3 回 V1 是否生成 V4？** 是；API 与浏览器均实际生成 V4。

25. **V1/V2/V3 是否仍存在？** 是；原行与字节精确比较未变。

26. **V4 是否记录 source V1？** 是；rollback_source_revision_id=V1，source_revision_id=V3。

27. **Current 是否切换到 V4？** 是；Current 指向新 V4。

28. **Version Number 是否继续递增？** 是；V4/V5/V6 及失败后的跳号均验证。

29. **Rollback 是否复用 T9 Publish State Machine？** 是；共用 sealBuilt、verifyPrepared、switchAndFinalize、finalize/fail。

30. **Rollback 是否生成新 Publish Record？** 是；operation_type=rollback、独立原因和幂等键。

31. **Rollback 是否产生 Audit？** 是；rollback_requested、failed/reconcile_required、succeeded 追加记录。

32. **Rollback 是否验证目标版本完整性？** 是；Prepare 前及 Build/切换前验证。

33. **Rollback Asset 是否安全冻结/复用？** 是；不需要私有源图，逐行复制逻辑关系并验证共享 CAS。

34. **Rollback Build Fail 是否保持旧 Current？** 是；注入 build 故障验证。

35. **Rollback Validation Fail 是否保持旧 Current？** 是；注入 validation/manifest/asset 故障验证。

36. **Rollback Switch 前 Fail 是否保持旧 Current？** 是；rename 前故障保留旧 Current。

37. **Switch 后 DB Fail 是否进入 Reconcile？** 是；新文件可能已公开，记录 recovery_required，保留 active。

38. **是否避免错误声称“所有故障 Current 都不变”？** 是；明确区分切换前与切换后失败。

39. **是否存在 Reconcile 状态？** 是；持久化 publication_health 加活动作业状态。

40. **是否可以检测 Current/DB/Manifest 不一致？** 是；DB/静态文件版本、Hash、Manifest、资产和 active 一起核对。

41. **Reconcile 是否只有 Super Admin？** 是；其他角色 403，匿名 401。

42. **Reconcile 是否有原因/Audit？** 是；每次原因必填，started/completed/failed 审计。

43. **严重不一致是否阻止普通 Publish？** 是；持相同 OS 锁重新验证，不信任状态缓存。

44. **严重不一致是否阻止 Rollback？** 是；同上。

45. **Reconcile 后是否恢复一致？** 是；实际重启后浏览器完成原记录，Current V5 一致。

46. **Publish History 是否包含失败 Attempt？** 是；失败/成功/待恢复 Attempt 均保留。

47. **Review History 是否保留所有轮次？** 是；驳回与多次批准记录均保留。

48. **Audit Timeline 是否完整？** 是；业务审计按时间显示，七分类过滤及详情。

49. **是否存在 Version Compare？** 是；业务分组与资产按 key 的差异。

50. **Compare 是否基于 Published Snapshot？** 是；读取并验证不可变 Published JSON 文件。

51. **是否比较 Inspection？** 是；inspection 分组。

52. **是否比较 Sections？** 是；custom_sections 分组。

53. **是否比较 Assets？** 是；role、公开 filename、hash、size 及增删改。

54. **是否不会重新用 Working Data 伪造历史 Diff？** 是；不从 Working Data 重算历史。

55. **Rollback 双击是否安全？** 是；UI busy 防重与服务端完整意图幂等。

56. **并发 Rollback 是否不会重复版本？** 是；同批两请求只一个成功、版本唯一。

57. **Publish 与 Rollback 并发是否受控？** 是；flock/CAS 互斥；冲突允许零个成功，Current 保持一致。

58. **Reconcile 与 Publish 是否不能冲突执行？** 是；共用 OS 锁，直接持锁测试全部写操作拒绝。

59. **Rollback 后是否还能正常发布下一版本？** 是；本地受控 Draft fixture 后真实提交、独立审核、正常发布 V6；正式 Published→Draft UI 未增加。

60. **Version Number 是否永不复用？** 是；分配后永不复用，允许失败跳号。

61. **Batch Archive 是否不删除历史？** 是；Published Batch 归档保留全部历史。

62. **Product Archive 是否不删除历史？** 是；Product 归档后历史和 release 完整性仍通过。

63. **是否没有自动 GC 删除历史 Asset？** 是；仅动态引用统计，不自动删除任何历史资产。

64. **Backend 重启后 History 是否完整？** 是；主库和 Fresh DB 的历史/审计/资产/头/文件重启前后精确一致。

65. **Backend 停止后历史 Release 文件是否仍存在？** 是；后台/UI 全停时 140 项静态访问断言通过。

66. **Fresh DB 是否完成 Publish→Rollback？** 是；空库正常 Publish V1/V2、Rollback V3、History/Verify/Compare 全链路。

67. **Migration 是否重复安全？** 是；T9 升级、空库与重复迁移一致，原数据保留。

68. **integrity_check 是否 ok？** 是，ok。

69. **foreign_key_check 是否无异常？** 是，无异常。

70. **所有成功 JSON Hash 是否一致？** 是；56 个成功、57 个 sealed JSON 全扫描。

71. **所有 Asset Hash 是否一致？** 是；73 条 sealed 资产关系全部校验实际字节。

72. **所有 Manifest 是否一致？** 是；所有 sealed Manifest 复验。

73. **Rollback 新版本 Hash/Manifest 是否完整？** 是；回滚与正常发布一同全量复验。

74. **普通 API 是否没有 Delete Passport Revision？** 是；没有普通删除接口，实际 DELETE 请求失败。

75. **普通 API 是否没有 Delete Published Asset？** 是；没有普通删除接口，冻结资产 DB 保护。

76. **Audit 是否仍 Append-only？** 是；UPDATE/DELETE 触发器拒绝，API 无修改入口。

77. **DATA_MODEL 是否变化？** 是；1 列、1 张四列表、事件 enum 与部分唯一索引调整。

78. **如变化是否新增 Migration？** 是；新增 1789257600000_version_history，不改既有迁移。

79. **是否修改 T4-T9 历史 Migration？** No；T4–T9 历史 Migration 原文 Hash 不变。

80. **是否更新 PUBLISH_MODEL？** 是；补齐实际回滚批准来源、共用链及安全恢复边界。

81. **是否新增 T10 文档？** 是；T10_VERSION_AUDIT_ROLLBACK.md 和 T10_TEST_RESULTS.json。

82. **T10 新 API 是否有独立契约检查？** 是；8 项专用 TS→Go 契约检查通过。

83. **上游 check:api 4 个既有问题是否仍单独记录？** 是；上游通用 check:api 的 4 条既有问题单独记录，不计为业务 Gate 失败或伪称全绿。

84. **是否修改上游 tracked files？** 是；后端 upstream tracked files 未改；UI 两个原已修改的语言入口继续添加 T10 模块注册。

85. **如修改，具体哪些？** admin/go-admin-ui/src/lang/en-US/index.ts；admin/go-admin-ui/src/lang/zh-CN/index.ts。其余新增/修改业务文件见完整清单。

86. **原 53 个基线文件 Hash 是否一致？** 是；53/53 SHA-256 一致。

87. **site 7 文件是否全部未变？** 是；7/7 未变。

88. **是否连接业务服务器？** No；未连接业务服务器，只有 loopback 本地服务。

89. **是否修改 Caddy？** No。

90. **是否修改 Directus？** No。

91. **是否修改生产 Docker？** No。

92. **是否生成正式 QR？** No。

93. **是否进入 T11？** No；T11 未开始。

T10 版本、审计与回滚已完成，当前已停止，等待人工验收，未进入 T11。
