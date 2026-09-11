# SQLite T4 真实验证与继续采用判断

2026-09-07。状态：等待人工验收。T4 实测结果支持在已确定的少量内部后台用户、扫码端读取静态发布内容的架构下继续使用独立 SQLite。没有发现必须立即改用 PostgreSQL 或侵入式改造 Go Admin 的证据。范围及 99 项检查见 [T4_RUNTIME_VALIDATION.md](T4_RUNTIME_VALIDATION.md)；不是生产容量或所有故障模式的保证。

## 已确认配置

数据库为 `/path/to/ID/runtime/t4/db/passport-admin-validated.db`。上游 sqlite3 build tag、gorm.io/driver/sqlite；Go 运行时内嵌 SQLite 3.53.4。Python 验证连接 SQLite 3.45.3，系统 CLI 3.51.0；没有混淆版本。

Go 实际连接的 PRAGMA：foreign_keys=1、journal_mode=wal、busy_timeout=5000、synchronous=2（FULL）。DSN 对每个连接显式设置这些参数。后台配置最大连接数 1；Go 补验专用库开 5 个连接。应用后续增加连接数时必须继续验证每个连接外键/等待超时生效，不能只在某个连接执行一次 PRAGMA 后假设全局有效。

业务 19 表/308 列/104 触发器，21 张上游表，总 40 表。既有数据库与 Directus 无关联。runtime 运行数据整体忽略且目录权限 0700，凭据/库/备份不公开提交。

## 运行证据与局限

| 项目 | 实测 |
| --- | --- |
| 官方 Migration | 空库 7 版本成功；业务 2 版本加入，共 9；Fresh 全量重建及重跑通过 |
| Runtime | 后台启动及重启成功；UI 实际登录，用户/角色/菜单页面打开 |
| RBAC | 通过官方 API 保存账号、角色、菜单/Casbin 策略；重启后允许和拒绝结果一致 |
| 外键/唯一/冻结 | 关键负向约束与历史固定绑定通过；剩余应用责任另列 |
| Python 并发 | 10 写入者 / 50 短事务 / 50 成功 / 0 失败 / 0 重试，最大等待+执行 620.31ms |
| Go/GORM 并发 | 5 写入者 / 25 短事务 / 25 成功 / 0 失败 / 0 重试，核对 75 行；耗时见 go-tests.jsonl |
| Transaction | 四表故意失败全回滚、正常四表提交；Go 驱动四表回滚补验 |
| 锁 | 两组测试无 database is locked；未验证长事务/持续写入下的边界 |
| Backup | 正在运行的后台库用 SQLite Backup API 备份；非活库直接文件复制 |
| Restore | 停止服务后 Backup API 恢复到独立库；全部 40 表逻辑 SHA 和行数与备份时一致；Go 驱动成功读取 |
| 完整性 | 主库、恢复库、Fresh 库、Go 补验库 integrity_check=ok，foreign_key_check 无行 |

SQLite 单写入者模型仍存在；WAL 不等于支持多个事务同时写，busy_timeout 不等于无锁。业务必须缩短写事务，文件处理放事务外，事务内只做必要数据库状态确认与提交；失败后有限重试并保证幂等，不无限等待。

上游 sys_role 对 SQLite 跳过数据库跨操作事务。本次成功创建及重启持久化成立；角色、菜单关联、Casbin 策略更新中途失败的原子性尚未验收。业务事务不能照搬该模式。没有为通过 T4 修改任何上游跟踪文件，也未适配 MySQL 代码生成器。

## 备份恢复方法

`admin/t4/verify_backup.py backup` 使用 Python sqlite3.Connection.backup：源库 → runtime/t4/backups/t4-consistent.db。备份关闭后记录文件 SHA-256、UTC 时间及每表逻辑摘要。随后修改主库测试用户 remark，停止 T4 服务；`verify_backup.py restore` 将备份经 Backup API 写入独立 runtime/t4/db/restored.db，再校验。

准确时间、Hash 和各表结果在 `runtime/t4/evidence/backup-restore.json`，摘要在 T4_RUNTIME_VALIDATION.md。脚本拒绝覆盖已存在的备份/恢复证据。备份时和恢复后内容一致，不要求恢复库包含备份之后的主库变更。

这些是 **数据库** 备份。私有工作资产、冻结发布资产以及配置的灾备归档不在 SQLite 文件里，正式恢复方案必须包含这些文件，并核对数据库引用的内容 Hash；T4 没有声称完整文件灾备完成。

## SQLite → PostgreSQL 复核（未安装 PostgreSQL）

下表是基于实际 DDL 的迁移设计判断，不是 PostgreSQL 运行验证。

| 实际 SQLite 类型/机制 | PostgreSQL 目标与必要处理 |
| --- | --- |
| 业务 TEXT UUIDv4 | UUID；检查全部存量格式，保留值，不重新分配 ID |
| sys_user 整数 ID | 保留上游整数主键，核对 sequence/identity 起点和全部外键；不强迫改 UUID |
| BOOL INTEGER + CHECK(0,1) | BOOLEAN；数据转换，不让应用依赖字符串 0/1 |
| UTC TEXT（毫秒/Z） | TIMESTAMPTZ，统一 UTC 读写；回灌不能把本地时间误作 UTC |
| DATE TEXT | DATE；检查合法日历日期，应用业务日期计算仍需规则 |
| JSON TEXT + json_valid | JSONB；先验证结构及数值语义。公开/审核摘要基于应用规范化字节，不能用 JSONB 重新序列化结果替代原冻结 Payload Hash |
| DECIMAL TEXT | 按字段实际需求选 NUMERIC(p,s)；先清理格式，不经过浮点丢精度 |
| ENUM TEXT + CHECK | TEXT + CHECK 或业务受控枚举；枚举扩展需要版本迁移 |
| HASH / CODE / PATH / TEXT | CHAR(64) 或受检 TEXT、大小写标准化/长度/路径检查；重写 GLOB、instr、时间函数等方言表达式 |
| UNIQUE / 组合 FK / RESTRICT | 保持同父实体组合外键、非空与删除保护；检查约束创建顺序及存量冲突 |
| 部分唯一索引 | 保留 WHERE 谓词，如单 Batch 唯一未决发布，转换为目标方言后测试 |
| 104 SQLite 触发器 | 重写为 PostgreSQL trigger functions（如 PL/pgSQL）及 RAISE EXCEPTION；复测 OLD/NEW、触发顺序、冻结与所有权、计数更新和竞争条件，不能直接复制 BEGIN/RAISE(ABORT) |
| 版本化 Migration | 单独 PostgreSQL DDL，复核上游系统 migration/seed；本轮 t4_schema SQL 为 SQLite 专用，不能仅切 driver 就运行 |
| 文件路径与静态资产 | 相对路径和 SHA 内容寻址语义保留；DB 搬迁不搬文件，要一起核对资产 Hash |

当前没有改变数据库类型的理由；未来如果实际出现多机写入、持续竞争、运维或容量需求，再用证据评估独立 PostgreSQL。不会使用 directus-db。

## 仍待后续验证

断电/进程强杀、磁盘满、长事务、长期数据增长、真实持续负载、备份保留轮换、完整文件灾备；正式权限/审核流程、版本分配、发布摘要/白名单与原子切换。mode=dev 的验证码跳过和极长 JWT TTL 仅限本地实验，不能作为生产配置。

T4 服务已停止，等待人工验收；本文不授权 T5 或服务器操作。
