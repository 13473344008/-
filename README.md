# 数字身份证管理系统

产品模板、批次身份证、审核发布和客户扫码页面的完整源码。本仓库是现有项目的源码快照，不包含本地用户账号、数据库、私有图片、发布数据或运行凭据；推送源码不代表已部署。

## 目录

- `admin/go-admin/`：Go 后台，产品模板、批次、自定义模块、RBAC、审核、静态发布、版本回滚、审计与访问统计。
- `admin/go-admin-ui/`：Vue 管理界面。
- `public-site/`：客户公开页面，只读取已发布 JSON 和图片；稳定路径 `/b/{批次编码}`。
- `site/`：保留的初期静态 POC。
- `admin/t*/`、`tests/`：各阶段验收和回归脚本。部分脚本依赖本地生成的运行目录，不能在空仓库中直接完整执行。
- `docs/`：架构、数据模型和阶段验收记录。历史报告记录当时状态，不代表后续修改已重新全量验收。

## 本地开发

依赖 Go、Node.js、pnpm；具体版本与依赖以各子项目的 `go.mod`、`package.json` 和锁文件为准。

1. 将 `admin/go-admin/config/settings.sqlite.example.yml` 复制为 `admin/go-admin/config/settings.yml`，设置独立随机 JWT 密钥并核对本地数据库目录。真实配置已被 Git 忽略。
2. 在 `admin/go-admin` 中运行 `go run -tags sqlite3,t4_schema . migrate -c config/settings.yml` 初始化数据库，再运行 `go run -tags sqlite3,t4_schema . server -c config/settings.yml`。身份证 SQLite 构建必须同时带 `sqlite3,t4_schema`，否则会漏掉业务迁移。初始化后在本地设置管理员密码，勿将框架演示凭据用于生产。
3. 在 `admin/go-admin-ui` 中安装依赖：`pnpm install --frozen-lockfile`。创建 `.env.development.local`，将 `VUE_APP_BASE_API` 指向本地后台；根据实际静态服务设置 `VUE_APP_PUBLIC_BASE_URL` 和 `VUE_APP_PUBLIC_MODE=local`。然后 `pnpm dev`。
4. 静态站点、发布目录、私有媒体和发布工作目录必须分开配置。参见 `public-site/README.md`、`docs/ARCHITECTURE.md` 和发布相关文档。源码中的 Nginx 配置为模板，不是已生效的生产部署。

后台发布所用环境变量包括 `PASSPORT_PUBLISH_ROOT`、`PASSPORT_PRIVATE_MEDIA_ROOT`、`PASSPORT_RELEASE_WORK_ROOT`；访问统计另需私有访问日志和地区数据库配置，见 `docs/T12_MANUAL_FEEDBACK_TRAFFIC.md`。这些运行文件不在仓库中。

## 当前验收说明

- 测试记录批次编码需包含独立的 `TEST` 段，例如 `PRODUCT-TEST-20260911-001`。该条件已在新建、复制、提交审核和发布前校验，管理界面会提前提示。
- 管理界面统一名称为“数字身份证管理系统”。
- 客户页面不展示发布信息区块；公开 JSON 仍包含版本校验所需元数据。
- 二维码使用稳定 URL；当前管理端尚未提供二维码图片下载。
- 本地验收和生产部署分离，禁止直接上传本地测试数据库用于生产。

## 上游与许可证

基于 Go Admin 后台与前端扩展。上游信息见 `docs/UPSTREAM_LOCK.json` 及子项目 README，原有 LICENSE 与版权声明保留在对应目录。`admin/go-admin/internal/ip2region/` 保留其独立许可证。未迁入上游 Git 历史，也未启用上游演示站的自动部署工作流。

## 生产准备

使用 [独立部署候选包](deploy/production/README.md)，不要使用上游演示 Dockerfile 直接上线。最新验证和剩余门禁见 [生产准备报告](docs/PRODUCTION_PREPARATION.md)。
