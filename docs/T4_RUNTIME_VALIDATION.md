# 【T4 执行结果】

日期：2026-09-07（Asia/Shanghai）。T4 状态：**等待人工验收**。T0–T3 已人工验收；未进入 T5。

Backend、UI、SQLite、Migration、RBAC Persistence、T3 Business Schema、Constraints、Transaction、Concurrency、Backup、Restore、Integrity Check、Fresh DB Rebuild：**全部 PASS**。

SQLite Final Recommendation：**继续使用**。这是当前本地低并发技术门槛通过，不是生产部署、完整工作流或发布引擎已经验收。

## 16 个 Gate

| Gate | 内容 | 结果 |
| --- | --- | --- |
| 1 | Backend 使用 SQLite 启动 | PASS |
| 2 | UI 连接后端并登录 | PASS |
| 3 | 官方空库 Migration | PASS |
| 4 | 重启后 RBAC / Casbin | PASS |
| 5 | T3 19 表建立 | PASS |
| 6 | 主要 FK / UNIQUE | PASS |
| 7 | Batch 固定 Revision | PASS |
| 8 | Passport 历史版本 | PASS |
| 9 | Published Asset 冻结 | PASS |
| 10 | Transaction Rollback | PASS |
| 11 | 低并发写入 | PASS |
| 12 | Backup | PASS |
| 13 | Restore | PASS |
| 14 | Integrity Check | PASS |
| 15 | Fresh DB 重建 | PASS |
| 16 | 无需大量侵入修改框架 | PASS |

## 环境与版本证据

- Backend v2.6.0 / `595c4a6be5b1aade8dc30fe2b90ea13dfba61b05`，origin 为 go-admin-team/go-admin；UI v3.2.0 / `e106f68d362d3a7aaa43244eb74cede1a83f4da5`，origin 为 go-admin-team/go-admin-ui；与 UPSTREAM_LOCK.json 一致。
- go version go1.26.5 darwin/arm64；Node v24.18.0；pnpm 9.15.1；git version 2.50.1 (Apple Git-155)；系统 SQLite CLI 3.51.0。
- **Go/GORM 实际 SQLite 3.53.4**；Python 3.13.1 的 sqlite3 为 **3.45.3**。两组分别记录，不把系统 CLI 版本当作服务版本。
- Go 与 pnpm 安装到 runtime/t4/tools，未覆盖其他项目工具链。UI frozen-lockfile 安装；go.mod/go.sum/pnpm-lock.yaml 未修改。官方 Go 压缩包 SHA-256：`efb87ff28af9a188d0536ef5d42e63dd52ba8263cd7344a993cc48dd11dedb6a`。
- 官方 Go proxy 连接超时，改用 goproxy.cn 下载，保留 go.sum/GOSUMDB 校验，没有更换框架、fork 或依赖版本。编译有 go-m1cpu C 扩展警告，编译成功。

## 本地运行配置与复现入口

私有配置 `runtime/t4/settings.yml`，随机本地 JWT 密钥；测试密码在 `runtime/t4/credentials.json`（不要提交或粘贴公开报告）。runtime/t4 权限 0700，数据库/备份 0600；runtime/.gitignore 忽略全部运行产物。两个上游仓均不包含 runtime；UI .env.development.local、node_modules 已验证被忽略。

Driver：上游 `sqlite3` build tag → gorm.io/driver/sqlite → go-sqlite3；没有重写框架数据库层。

```text
DSN=file:/path/to/ID/runtime/t4/db/passport-admin-validated.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL
foreign_keys=1
journal_mode=wal
busy_timeout=5000
synchronous=2 (FULL)
配置 maxOpenConns=1 / maxIdleConns=1
Backend 127.0.0.1:18094
UI 127.0.0.1:19527
```

命令在相应上游目录执行，工具环境先 source `/path/to/ID/admin/t4/env.sh`。本次实际命令：

```sh
# cwd=/path/to/ID/admin/go-admin
GOPROXY=https://goproxy.cn,direct go build -tags sqlite3 -o /path/to/ID/runtime/t4/bin/go-admin .
/path/to/ID/runtime/t4/bin/go-admin migrate -c /path/to/ID/runtime/t4/settings.yml
GOPROXY=https://goproxy.cn,direct go build -tags 'sqlite3,t4_schema' -o /path/to/ID/runtime/t4/bin/go-admin-t4 .
/path/to/ID/runtime/t4/bin/go-admin-t4 migrate -c /path/to/ID/runtime/t4/settings.yml
/path/to/ID/runtime/t4/bin/go-admin-t4 server -c /path/to/ID/runtime/t4/settings.yml
# cwd=/path/to/ID/admin/go-admin-ui
pnpm install --frozen-lockfile --registry=https://registry.npmjs.org --store-dir /path/to/ID/runtime/t4/pnpm-store
pnpm dev --host 127.0.0.1 --port 19527 --strictPort
```

以上是复现记录，不是要求现在重启。当前两个端口均已验证停止。技术脚本均在 admin/t4；部分脚本为了保留证据会拒绝覆盖已有 Backup/Fresh 文件，verify_schema 只应对专用干净测试库跑一次，不能对已含测试数据的库重复灌入。Go 补验测试以 t4_validation build tag 隔离，命令为 `go test -tags 'sqlite3,t4_validation' ./cmd/t4probe -run TestT4ActualGoDriver -count=1 -json`。Go 补验库是 restored.db 的 Backup API 副本；重复补验前同样需明确准备专用副本。

## Migration 与 Schema

官方先独立编译并执行 7 个版本：1599190683659、1653638869132、1786700000000、1786700001000、1786700002000、1786700003000、1786700004000。第二次无需重建。

业务新增 1788739200000、修正 1788739201000；共 9 个版本由 sys_migration 记录。上游是**版本化 Migration，其中具体版本调用 GORM AutoMigrate 和 seed SQL**，不能称为完全不使用 AutoMigrate，也不能把随服务启动无差别 AutoMigrate 当作本项目正式升级策略。业务 Schema 使用显式 DDL。

19 表、308 列、104 个触发器建立；另有 21 张上游表（含演示表），合计 40 表。全新库实际 Schema 对象与验证主库一致；所有迁移重跑后 Schema / 版本不变。生成脚本现只输出 runtime/t4/schema-candidate.sql 草案，防止以后覆盖已执行迁移。

发现和修复：

1. 首次业务插入暴露可空 UTC CHECK 拒绝 NULL。未修改已执行版本，而是新增 1788739201000。修正版本事务内先确认 **19 张业务表全部为空** 才重建；非空时拒绝执行，因此不会默默丢数据。它是本轮初始建库修正，不能作为未来有数据的通用升级方案。
2. 检测值约束显式 COALESCE，避免三值逻辑接受无值 pass/fail/informational；在首次业务迁移前修正。
3. 初始 fixture 漏传 transform_version 被 NOT NULL 拒绝。补齐调用值；DATA_MODEL.md 明确 schema_version / transform_version 由应用显式传入。未改变关系或表数，ERD 无关系变动。
4. UI 自动化最初误用 submit 类型按钮和 history URL，按官方 submit-btn 与 Hash 路由修正；没有修改上游 UI。
5. Go 补验首次用复制整行测试 UNIQUE 会先碰到 PK/冻结/发布保护；修正测试为新 UUID、合法准备态，并断言 UNIQUE 错误。此问题在测试样本，不是绕过数据库保护。

## RBAC / UI 实测

用 admin 随机测试口令登录，JWT 可访问 getinfo，非法 token 被拒。通过官方 role / sys-user API 创建 T4 Test Reader（role_key=t4_reader）和 t4-reader；授权 sys_role_menu 和 casbin_rule 实际写入 SQLite。测试角色 GET /api/v1/role 获准、GET /api/v1/sys-user 被拒（上游返回 HTTP 200 + JSON code 403，以业务码判断）。后端进程停止并新启动后，重新登录及相同允许/拒绝检查均通过。

浏览器实际登录并显示基础菜单；用户、角色、菜单页面可打开；6 项 UI 检查通过、未捕获 JS 错误 0。截图保存在 runtime/t4/evidence/ui-*.png。上游首页销售/流量数字是演示内容，不是产品数字身份证业务指标。

## 冻结与业务样本边界

测试 Product=T4-PF-STD，Batch=PF-T4-001，R1 sealed 后新建 R2 并设为当前模板，历史 Batch 仍绑 R1，重绑被拒。主体、Translation、Custom Section、冻结子行修改被拒。Override 无行/set/clear 分别得到 25/20/NULL，未知字段拒绝；检测 7 项含 Bulk Density 与四种判定无需 ALTER；六语言同父共存且重复被拒。

V1/V2/V3 保留，V4 引用 V2 为回滚来源。image-A 冻结复制到 assets/sha256/前两位/hash.png；另建工作 B、归档 A 后 V1 字节 Hash 不变，A 物理删除因 FK 被拒。**这是最小数据库及文件副本原型**；测试 Payload 有 TEST RECORD — NOT FOR COMMERCIAL USE 标记，使用 t4_schema_fixture，内容摘要中的占位值不代表正式白名单 Payload 或正确构建摘要。

| 保护 | 层次和实测边界 |
| --- | --- |
| UNIQUE / FK / NOT NULL / enum / 覆盖白名单 / 固定绑定 | Database-enforced；主要负向用例已实测 |
| sealed 模板主体和子行、published revision/asset、追加审计 | Database-enforced；104 触发器中的关键路径已实测，不声称所有组合穷尽 |
| 文件副本和 SHA 路径 | 最小原型实测；磁盘被外部删改不受 SQLite FK 保护 |
| JWT / Casbin 基础 API 授权 | 上游 Application-enforced，登录与重启允许/拒绝实测 |
| 审核权限矩阵、完整工作流、版本分配、业务内容摘要/发布白名单、MIME/文件净化、恢复对账 | 后续 Application-enforced，T4 未实现，不算已保护 |

## 事务、并发、Backup / Restore

Python 事务跨 Batch / Inspection / Override / Audit：故意重复检测项目导致全部回滚，正常分支全部提交。Python 10 写入者执行 50 事务，成功 50、失败 0、重试 0，最大事务等待+执行 620.31 ms；核对 50 Batch + 50 Inspection + 50 Audit。

Go/GORM SQLite 3.53.4 补验 15 项通过，含 5 个独立连接并发完成 25 事务、75 行计数准确、失败 0、重试 0、四表回滚。两组均未出现 database is locked。是短事务本地测试，不是生产吞吐 SLA 或长事务/多进程/磁盘故障验收。

Backup API 执行时后台可运行；不直接复制 WAL 活库主文件。备份后刻意修改主库测试用户 remark，停止后台/UI，再用 Backup API 恢复到独立 restored.db。恢复库全部 40 表的行数和逐表逻辑 SHA-256 与备份时完全一致，含账号、角色、规则、Product/R1/R2/Batch/V1–V4。Go 实际驱动随后成功打开恢复库。

- Backup 时间：2026-09-07T14:08:15.125046+00:00（UTC）。
- 文件：`/path/to/ID/runtime/t4/backups/t4-consistent.db`。
- 文件 SHA-256：`b26fbff787f26fceabee500927f557a8f9a0f76c8dd10cccb70a442943ec51da`。
- Restore：`/path/to/ID/runtime/t4/db/restored.db`。
- 主库、恢复库、Fresh 库、Go 专用补验库 integrity_check=ok / foreign_key_check 无行。
- SQLite Backup **不包含外部资产目录**。完整项目灾备仍需数据库与私有/冻结资产协调备份及恢复演练，本轮未完成文件灾备引擎。

## 测试计数及证据

最终 99 项，PASS 99，FAIL 0。计数为脚本命名断言/Go 子测试，排除 Go 父测试、Gate 汇总、前期失败和重复尝试；不是 99 个独立端到端业务场景。前期问题见上文，未隐去。

| 测试组 | 检查数 | PASS | FAIL |
| --- | --- | --- | --- |
| Schema / Python SQLite | 40 | 40 | 0 |
| 首次 API / RBAC | 11 | 11 | 0 |
| 重启 API / RBAC | 9 | 9 | 0 |
| UI | 6 | 6 | 0 |
| Fresh DB | 4 | 4 | 0 |
| Backup / Restore | 5 | 5 | 0 |
| 最终基线 / Schema / 停止核验 | 9 | 9 | 0 |
| Go/GORM 实际驱动 | 15 | 15 | 0 |

原始证据位于 runtime/t4/evidence：environment.json、go-driver.json、schema-tests.json、api-initial.json、api-restart.json、ui-tests.json、fresh-tests.json、backup-restore.json、restore-go-driver.json、go-tests.jsonl、final-tests.json；日志位于 runtime/t4/logs。运行证据属于本地私有数据，不加入公开源代码。

## 文件变化

新增锁定的 admin/go-admin 与 admin/go-admin-ui 两仓（UI 跟踪文件变化 0；Backend 跟踪文件变化 0，新增迁移/探针）。新增源码及辅助清单：

- `admin/t4/build_report.py`
- `admin/t4/configure.py`
- `admin/t4/env.sh`
- `admin/t4/generate_schema.py`
- `admin/t4/schema_catalog.json`
- `admin/t4/verify_api.py`
- `admin/t4/verify_backup.py`
- `admin/t4/verify_final.py`
- `admin/t4/verify_fresh.py`
- `admin/t4/verify_schema.py`
- `admin/t4/verify_ui.cjs`
- `admin/.gitignore`
- `runtime/.gitignore`
- `admin/go-admin/cmd/t4probe/main.go`
- `admin/go-admin/cmd/t4probe/validation_test.go`
- `admin/go-admin/cmd/migrate/migration/version/1788739200000_passport.go`
- `admin/go-admin/cmd/migrate/migration/version/1788739200000_passport.sql`
- `admin/go-admin/cmd/migrate/migration/version/1788739201000_passport_nullable.go`
- `admin/go-admin/cmd/migrate/migration/version/1788739201000_passport_nullable.sql`

新增 docs/T4_RUNTIME_VALIDATION.md、docs/SQLITE_VALIDATION.md、docs/T4_TEST_RESULTS.json；修改 docs/DATA_MODEL.md（最小实现校准）、docs/TASKS.md（T3 人工通过、T4 等待人工验收）。runtime 包含私有工具/依赖缓存、二进制、测试数据库、备份、资产副本及日志，目前约 2.4 GB；UI 依赖约 438 MB，均保留用于复现，没有清理其他项目。

53 个原文件 SHA-256 前后匹配，site 的 7 文件不变；没有连接业务服务器、没有 SSH、没有操作 Caddy/Directus/生产 Docker/DNS/HTTPS，没有服务器部署。

## 已知风险与 T5 注意事项

- 本地 mode=dev 跳过验证码且上游 JWT TTL 极长，仅供本机 T4。生产配置尚未设计或验收，不能复制后上线。
- 上游 sys_role 的 SQLite 分支跳过跨操作事务；本次成功路径持久化通过，**未证明角色/菜单/Casbin 写入失败时原子性**。不要把该模式复制到业务跨表写入；授权变更失败补偿/一致性需后续验证。
- 104 触发器是 SQLite 专用实现；SQLite→PostgreSQL 需重写触发函数/迁移，见 SQLITE_VALIDATION.md。不直接把 DDL 当跨数据库迁移。
- 测试未包含崩溃恢复、断电、磁盘满、长事务、海量数据、多机或真实负载。保持本地文件系统、短事务、有限 busy retry、备份验证。
- 正式 CRUD 应对 NOT NULL / FK / frozen 错误给出可理解反馈，并在单事务完成数据及审计；业务权限/审核/发布引擎仍待后续明确授权。
- 上游代码生成器 MySQL 限制不作为 SQLite 阻断，本轮未适配或换库。

## 47 项逐项回答

| # | 问题 | 回答 |
| --- | --- | --- |
| 1 | Go Admin Backend 是否成功运行？ | Yes；实际启动并重启，现已停止。 |
| 2 | Go Admin UI 是否成功运行？ | Yes；Vite 启动，现已停止。 |
| 3 | UI 是否成功连接 Backend？ | Yes；浏览器登录及三类管理页面通过。 |
| 4 | 是否真实使用 SQLite？ | Yes；Go 实际驱动 SQLite 3.53.4。 |
| 5 | SQLite 文件具体位置？ | /path/to/ID/runtime/t4/db/passport-admin-validated.db |
| 6 | 官方 Migration 是否成功？ | Yes；官方 7 个版本通过。 |
| 7 | 系统表是否建立？ | Yes；21 张上游表（含迁移、Casbin 和演示表），另加 19 张业务表。 |
| 8 | JWT 登录是否成功？ | Yes；签发、getinfo 验证、非法 token 拒绝均通过。 |
| 9 | RBAC / Casbin 是否持久化？ | Yes；真实 API 创建并持久化。 |
| 10 | 重启后用户、角色、权限是否存在？ | Yes；重新登录并复验允许/拒绝接口。 |
| 11 | 19 张业务表是否真实建立？ | Yes；308 列与 T3 字段目录一致。 |
| 12 | Product Code UNIQUE？ | PASS。 |
| 13 | Batch Code UNIQUE？ | PASS。 |
| 14 | Product Revision UNIQUE？ | PASS。 |
| 15 | Passport Revision Version UNIQUE？ | PASS。 |
| 16 | Translation UNIQUE？ | PASS。 |
| 17 | Foreign Key 是否开启？ | Yes；Go 与 Python 实际连接 foreign_keys=1。 |
| 18 | 删除被引用 Product Revision 是否阻止？ | Yes；冻结保护拒绝，外键及禁止级联同时保留。 |
| 19 | Batch 是否固定绑定 Revision？ | Yes；绑定 R1，重绑被拒绝。 |
| 20 | R2 是否不改变历史 Batch？ | Yes。 |
| 21 | Override 三态？ | Yes；无行继承 25、set 为 20、clear 为 NULL，移除覆盖恢复继承；非法字段被拒绝。 |
| 22 | Inspection 新增未知项目无需 ALTER？ | Yes；七项目含 Bulk Density，schema_version 不变。 |
| 23 | 六语言共存？ | Yes；en、zh-CN、es、ar、fr、de。 |
| 24 | V1/V2/V3/V4 回滚模型？ | Yes；V4 的 rollback_source_revision_id=V2，V1–V3 保留。 |
| 25 | Published Asset 保留 image-A？ | Yes；冻结副本路径及实际 SHA-256 不变。 |
| 26 | Media Asset 变化不影响历史资产？ | Yes；另建 B，A disabled，删除 A 被 FK 拒绝，V1 A 副本可读。 |
| 27 | Transaction Rollback？ | PASS；Python 四表故意唯一冲突全回滚，正常四表全提交；Go 四表回滚补验通过。 |
| 28 | 并发写入结果？ | Python：10 写入者/50 事务，50 成功；Go：5 写入者/25 事务，25 成功。 |
| 29 | 是否发生 database is locked？ | 最终两组测试均未发生。 |
| 30 | 锁是否可接受及可处理？ | 本次未触发锁超时；不能据此证明所有负载都不锁。后续保持短事务并设计有限重试。 |
| 31 | Backup 是否实际成功？ | Yes；SQLite Backup API。 |
| 32 | Restore 是否实际成功？ | Yes；停止服务后恢复至独立 restored.db，Go 驱动也成功读取。 |
| 33 | Restore 数据完整？ | Yes；备份时全部 40 表行数及逻辑内容 SHA-256 一致，含用户、角色、权限及核心业务记录。 |
| 34 | integrity_check=ok？ | Yes；主库、恢复库、Fresh 库、Go 补验库均通过。 |
| 35 | foreign_key_check？ | PASS；无异常行。 |
| 36 | Fresh DB 从零建立？ | Yes；删除专用 disposable 数据库后由所有迁移重建，未复制演示 DB。 |
| 37 | Migration 可重复？ | Yes；官方迁移重跑、全迁移 fresh 重跑均通过。 |
| 38 | 是否必须大量修改 Go Admin？ | No；上游已跟踪文件改动 0，仅新增业务迁移与技术探针。 |
| 39 | SQLite 当前是否推荐？ | 继续使用，限已确定的少量内部用户、公开静态化场景。 |
| 40 | 立即切换 PostgreSQL 的证据？ | 未发现；本轮没有安装或连接 PostgreSQL。 |
| 41 | 是否修改 site？ | No；7 文件不变。 |
| 42 | 53 文件 SHA-256 是否一致？ | Yes；开始与结束均一致。 |
| 43 | 是否连接业务服务器？ | No。 |
| 44 | 是否修改 Caddy？ | No。 |
| 45 | 是否修改 Directus？ | No。 |
| 46 | 是否修改 Docker 生产环境？ | No。 |
| 47 | 是否进入 T5？ | No。 |

T4 本地真实运行验证已完成，当前已停止，等待人工验收，未进入 T5。
