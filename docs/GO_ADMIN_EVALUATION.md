# T1 — Go Admin 官方项目核验

核验日期：2026-09-07。证据分为官方 Release 页面、精确 Tag 的源码、实际执行的静态检查。没有执行 Go 编译、数据库迁移或后台启动；这些属于 T4，不能将源码支持写成运行验收通过。

## 版本选择与维护状态

| 组件 | 官方 repository | 推荐稳定 Tag | 实际 commit SHA |
| --- | --- | --- | --- |
| Backend | https://github.com/go-admin-team/go-admin | v2.6.0 | `595c4a6be5b1aade8dc30fe2b90ea13dfba61b05` |
| UI | https://github.com/go-admin-team/go-admin-ui | v3.2.0 | `e106f68d362d3a7aaa43244eb74cede1a83f4da5` |

两个 [Backend Releases](https://github.com/go-admin-team/go-admin/releases)、[UI Releases](https://github.com/go-admin-team/go-admin-ui/releases) 页面当前分别把上述版本标为 Latest，未标预发布。Git 标签查询也确认它们是当前最高的正常语义版本标签；没有选 master。后端 v2.6.0 是 annotated tag，标签对象 SHA 为 `f3583efc918207672393f0ee2f4d79286c6f59c0`，不能把它误写成 commit SHA。

两个推荐提交时间分别为 2026-08-31 15:01:42 +08:00、2026-08-31 21:28:27 +08:00（Git 元数据，不冒充 Release 发布时间）。结合两仓近期正式发布与修复代码，可以判断仍有维护活动；不据此承诺长期支持、响应 SLA 或全部 CI 通过。GitHub 公共 API 此次返回 403 rate limit，使用官方网页与 Git 协议交叉核验，未取得 archived API 字段或全量 CI 状态。没有采用随机 Fork。

推荐理由：采用当前明确发布的修复版本，避免从旧 README 推断旧技术栈。版本锁见 [UPSTREAM_LOCK.json](UPSTREAM_LOCK.json)。这是后续本地验收基线，不是上线批准。

## 工具链与前后端兼容

- [后端 go.mod](https://github.com/go-admin-team/go-admin/blob/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05/go.mod) 声明 Go **1.26.5**，Gin 1.12.0、GORM 1.31.2、go-admin-core/v2 2.3.0、Casbin/v3 3.8.1；按该要求准备 T4，不照搬旧 Go 1.x 教程。本机当前 PATH 未找到 go，本轮不安装。
- [UI package.json](https://github.com/go-admin-team/go-admin-ui/blob/e106f68d362d3a7aaa43244eb74cede1a83f4da5/package.json) 声明 Node >=22、pnpm >=9，packageManager 锁定 pnpm 9.15.1；Vue 3、Element Plus、Vite，已经不是旧 Vue 2 UI。推荐 T4 用 Node 24 系列与 pnpm 9.15.1，使用 frozen lockfile；具体补丁与镜像 digest 在 T4 实装时记录。[UI Dockerfile](https://github.com/go-admin-team/go-admin-ui/blob/e106f68d362d3a7aaa43244eb74cede1a83f4da5/Dockerfile) 也采用 Node 24。
- 未发现一份覆盖所有版本的官方配对矩阵，因此不因两个 Tag 数字不同而判断不兼容，也不宣称有官方逐版本认证。
- 已通读并执行 UI 自带只读 [check-api-contract.mjs](https://github.com/go-admin-team/go-admin-ui/blob/e106f68d362d3a7aaa43244eb74cede1a83f4da5/scripts/check-api-contract.mjs)，显式指向上述后端，启用 `--require-models`，没有缺少后端而跳过。

```text
GO_ADMIN_PATH=/tmp/pdi-t012-research/backend node /tmp/pdi-t012-research/ui/scripts/check-api-contract.mjs --require-models
API contract ok: 8 fixtures, 15 migrated pages, 3 Options-API pages, and the declarations in types/admin.ts
```

执行 Node 为本机 v24.18.0。结论：被脚本覆盖的模型字段、查询参数与页面声明契约通过；脚本不覆盖所有路由、登录行为、授权语义、上传、运行时响应或所有页面，不能代替 T4 真正联调。

## License

所选后端 [LICENSE.md](https://github.com/go-admin-team/go-admin/blob/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05/LICENSE.md) 与 UI [LICENSE](https://github.com/go-admin-team/go-admin-ui/blob/e106f68d362d3a7aaa43244eb74cede1a83f4da5/LICENSE) 都是 MIT。允许修改、商业使用和分发，需保留适用版权与许可声明；无担保。该结论仅针对两个根仓库的所选版本，不等于已审计所有依赖、字体、图片、商标或商业 Pro 产品。T4 保留 LICENSE 并整理第三方声明。

## 能力逐项核验

下面后端相对路径均以已锁定 SHA 为准；[源码树](https://github.com/go-admin-team/go-admin/tree/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05) 可复查。

| 要求 | 已确认源码证据 | 项目判断及待验证 |
| --- | --- | --- |
| 数据库 | common/database/open.go、open_sqlite3.go；config/settings.sqlite.yml | MySQL/PostgreSQL/SQL Server 有驱动；SQLite 需 sqlite3 构建标签和 CGO；驱动支持不等于全模块等价 |
| SQLite migration | cmd/migrate/migration/version/1599190683659_tables.go；1786700003000_soft_delete_marker_test.go | 有初始化、SQLite 软删除/唯一约束/重复迁移测试；测试用 glebarez，实际应用 sqlite3 驱动不同，完整迁移仍待 T4 |
| PostgreSQL | gorm.io/driver/postgres 1.6.2；初始化分支与 config/pg.sql | 是可行候补；也需空库全迁移实测，不推定比 SQLite 全模块兼容 |
| Docker | Dockerfile、scripts/Dockerfile、docker-compose.yml、.github/workflows/build.yml；UI Dockerfile | 有容器入口；现成镜像架构、digest 与可用性未验证，需项目专用构建 |
| JWT | common/middleware/auth.go；app/admin/router/sys_router.go | 复用 core jwtauth；Bearer 支持；旧 refresh_token 路由已移除，不能套旧教程 |
| Casbin / RBAC | common/database/initialize.go；common/middleware/permission.go；app/admin/service/sys_role.go | 用同一 GORM DB 建立 Casbin，按角色、路由、HTTP 方法检查；原 admin rolekey 绕过检查，四角色须显式配置并做负向验证 |
| 用户 | app/admin/router/sys_user.go；service/sys_user.go | 已有 CRUD、密码/状态/头像相关入口；新用户与撤权会话行为待 T4/T8 |
| 角色 | app/admin/router/sys_role.go；service/sys_role.go | 已有角色/策略持久化逻辑；本项目角色不是自动具备 |
| 菜单 | app/admin/router/sys_menu.go；models/sys_menu.go | 已有菜单与权限 UI 基础；隐藏按钮不能替代 API 授权 |
| 操作/登录日志 | common/middleware/logger.go；router/sys_opera_log.go、sys_login_log.go | 已有框架日志；SQLite 示例 enableddb=false，不能假定默认落库。业务审核发布审计另规划可靠事务记录 |
| 数据权限 | common/actions/permission.go；service/sys_user.go | 部门、自定义部门、本部门及下级、仅本人范围逻辑；enabledp 示例默认 false，需按业务范围配置 |
| 上传 | app/other/router/file.go；apis/file.go | /api/v1/public/uploadFile 在认证路由中；本地及云存储分支已有。私有原件不可沿用公开 /static 直出，需业务资产授权与公开副本分离 |
| 代码生成器 | app/other/models/tools/db_tables.go、db_columns.go | 实际 guard 只允许 mysql，并查询 information_schema；SQLite 和 PostgreSQL 都不能直接使用该表结构读取生成流程 |

**生成器结论：不适合作为本项目核心实现依赖。** 可参考模块组织和模板，但不为它增加 MySQL，也不为 SQLite 重写整个生成器。业务编辑表单、子项排序、模板覆盖与审核发布需要业务代码；非技术用户添加检测项/自定义模块走业务数据配置，不是运行代码生成器。

## SQLite 的实际支持边界

已核验 [open_sqlite3.go](https://github.com/go-admin-team/go-admin/blob/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05/common/database/open_sqlite3.go) 注册的是 `sqlite3`，不是 `sqlite`。普通 CGO_ENABLED=0 构建不包含该入口。官方有专用配置和 CGO sqlite3 构建工作流，因此启用它属于上游支持的构建/配置选择，不属于大规模侵入修改。

[迁移回归源码](https://github.com/go-admin-team/go-admin/blob/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05/cmd/migrate/migration/version/1786700003000_soft_delete_marker_test.go) 覆盖实际 user_id 主键、带索引的旧 deleted_at、重复执行及自然键唯一性。但本轮未运行这些测试，也未跑完全部 seed/迁移/Casbin 联调。未发现必须因 SQLite 大改框架的已证实阻断，推荐 SQLite，保留 T4 验收门槛。完整比较见 [DATABASE_DECISION.md](DATABASE_DECISION.md)。

## 不可直接复制的上游默认值

1. [官方 Compose](https://github.com/go-admin-team/go-admin/blob/595c4a6be5b1aade8dc30fe2b90ea13dfba61b05/docker-compose.yml) 使用 privileged、宿主机 8000 映射和 latest，与本项目红线冲突。T4 另写本项目配置，不能原样启动。
2. root Dockerfile 复制演示数据库；scripts/Dockerfile 依赖预编译二进制。普通 build 不带 sqlite3，不能把“有 Dockerfile”当作“SQLite 镜像已验收”。不能用演示 DB 代替空库迁移。
3. SQLite 示例是 dev 模式、默认 JWT secret、较长开发期 token，不能带到正式环境；新建自己的密钥与账户，不输出凭据。
4. `/static` 是公开静态路由。上传能力不等于内部资料安全存储能力，私有文件必须移出它的根目录。
5. migrate/server.go 的 initDB 忽略 migrateModel 返回值，仍打印初始化成功；T4 应校验退出结果、实际表、迁移记录和关键操作，不能只看成功日志。

上述风险列入 T4/T8/T12，不在本轮修改任何上游源码或启动系统。
