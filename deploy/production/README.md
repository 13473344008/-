# 生产部署候选包

这是本地生产准备成果，不表示已部署，也不表示已批准修改共享代理、DNS 或 HTTPS。正式域名为 `id.potahub.com`，测试域名为 `id-test.potahub.com`。先测试再生产，分别使用独立目录、数据库、Compose 项目名和发布目录。

## 交付物与验证边界

- 后台多阶段构建 `Dockerfile.backend`：Go SQLite 构建必须带 **`sqlite3,t4_schema`**，后者包含身份证业务迁移；只带 sqlite3 会漏表。镜像不包含开发配置、数据库或账号密码。
- 管理端 `Dockerfile.web`：固定 pnpm、冻结依赖锁；API 同源 `/api/`，公开 Base URL 在构建时指定。根目录 `.dockerignore` 排除运行数据和实际配置。
- `images.lock.json` 锁定官方基础镜像索引摘要；已确认索引支持 linux/amd64 和 linux/arm64。索引摘要不是镜像漏洞扫描或运行兼容性证明。
- `compose.admin.yml`：独立后台和管理 Nginx，内部网络，只有管理 Nginx 绑定宿主机 loopback 端口。默认通过 SSH 隧道管理，无公开后台域名。
- `compose.public.yml`：独立公开 Nginx，无宿主机端口、无 API/数据库依赖；静态页面及发布内容只读挂载。仅接入经现场核实的代理网络，使用独立上游别名。
- `prepare.py`：创建全新私有配置包，mode=prod、独立随机 JWT、随机初始管理员密码，拒绝覆盖。不会执行迁移、启动服务或打印密码。
- `passport-ops`：首次 bootstrap 只允许初始 admin、空业务表及框架默认密码的全新库；拒绝重复重置。启动检查拒绝弱 JWT、dev 模式、未启用数据权限、缺少迁移、默认密码和启用的 t12 验收账号。
- `backup.py`：SQLite Backup API + 私有媒体/工作清单/公开文件，校验当前与已发布历史版本、图片及私有清单；恢复只到新目录，不覆盖正在使用的数据。

本轮已完成 native Go 构建、前端生产构建、完整迁移与回归、本机 Nginx 语法检查和备份恢复。**本机没有 Docker，Docker 镜像构建、Compose 真实解析及容器权限/资源/网络实跑尚未验证，必须在隔离测试环境完成后才能放行生产。** 不把静态 YAML 检查写成 Docker 实跑通过。

## 1. 先只读核对目标

在获得服务器访问授权后，使用 `preflight.sh` 读取 OS/架构、磁盘、Docker/Compose、容器和网络列表。核对现有 `/opt/proxy/docker-compose.yml` 与 Caddyfile，敏感值由持有者遮盖；不索取 `.env` 或私钥。

记录既有站点实际域名、状态码和关键内容基线。检查管理员 loopback 端口是否占用、`/opt/product-id` 和 `/opt/passport-admin` 是否已有数据、磁盘余量、时钟同步、备份盘位置、代理网络子网及成员。现有目录不能直接用本模板覆盖。

## 2. 构建可核对的候选

复制 `release.env.example` 为一个仅用于本次候选的 `.env` 文件。填入已核实的代理网络、独立项目名/路径/端口和唯一版本标签；不要把真实密码写入此文件。测试候选将 `PUBLIC_BASE_URL` 改为 `https://id-test.potahub.com`，且两项目名称及目录必须带测试环境标识。

从完整源码根目录执行（有 Docker 的独立构建环境）：

```sh
python3 deploy/production/release.py validate --env /absolute/path/release.env
python3 deploy/production/release.py build --env /absolute/path/release.env --platform linux/amd64 --manifest /absolute/path/new-release-manifest.json
```

`--platform` 必须与核对的目标架构一致；不要照抄。脚本只执行配置检查、构建和记录镜像 ID，不启动容器。记录源码 commit、工具版本、镜像摘要和产物清单；部署应引用验证后的镜像 ID/摘要，禁止浮动 latest。将验证后的镜像用 `docker image save/load` 或受控镜像仓库传输，不能假定目标主机已有本地标签。变更任意输入后重新构建与验收。

## 3. 配置及首次初始化

在私有位置生成新包：

```sh
python3 deploy/production/prepare.py --destination /absolute/path/new-private-bundle --public-base https://id-test.potahub.com
```

将两个 Compose 定义分别安装为所选独立项目目录的 `docker-compose.yml`，release.env 随项目保管；只复制 `nginx-public.conf` 到公开目录的 `nginx.conf`，只复制 `public-site` 内容到该环境的 `site/`。**配置和 admin-password 只能放到后台根的 config/，绝不能放 site/ 或公开发布根。**

按 Compose 中明确的 bind 清单准备目录：后台 `config/`、`data/db`、`data/media`、`data/logs`、`data/geo`，公开项目 `site/`、`data/published`、`data/work`、`logs/`。仅对这次新建的本项目目录设置 UID/GID `10001:10001`；私有文件 0600、私有目录 0700、公开文件 0644、公开目录 0755。公开日志目录及文件须允许同 UID 后台只读读取。严禁对 `/opt`、共享 Caddy 或其他业务目录递归 chown。配置挂载禁止自动创建缺失源路径。

验证 published 和 work 在同一文件系统；不要使用 NFS/网络盘。地区库单独下载到私有 geo 目录并核对来源和 SHA256。备份中不包含 JWT 配置和初始密码，二者应有独立受控备份。

在**目标已确认、配置已校验的测试项目**中执行独立服务初始化，示例变量必须由实际目录替换：

```sh
docker compose --env-file /absolute/admin/release.env -f /absolute/admin/docker-compose.yml -p passport-admin-test run --rm --no-deps backend migrate
docker compose --env-file /absolute/admin/release.env -f /absolute/admin/docker-compose.yml -p passport-admin-test run --rm --no-deps backend bootstrap
docker compose --env-file /absolute/admin/release.env -f /absolute/admin/docker-compose.yml -p passport-admin-test run --rm --no-deps backend check
```

迁移成功后核对 18 项及业务表、PRAGMA integrity_check / foreign_key_check；再跑一次迁移确认无重复变更。bootstrap 成功后初始密码仅供管理员从受控文件读取，不写日志。该工具不用于已有库的密码重置。设置实名业务账号、角色和密码后，移走挂载中的初始密码文件，妥善保管其受控副本。

迁移与完整初始化通过后，按相同显式 `--env-file/-f/-p` 启动本项目 backend/admin。后台为单实例，禁止横向扩成多个 SQLite 写实例。管理者经 SSH 隧道连接已配置的 loopback 端口；当前设计不开放后台公网地址。需要公网管理域名时应另做入口认证、HTTPS、可信代理、Origin 和暴力登录防护验收。

## 4. 公开入口与扫描地区

只有在测试独立服务通过后，才准备 Caddy 的**单个域名增量路由**：目标为实际网络中核对的 `${PUBLIC_UPSTREAM}:8080`。本包不提供覆盖整份 Caddyfile 的命令，不修改共享 Compose、不 reload Caddy、不调整 DNS 或 HTTPS。

任何共享网络成员调整或 Caddy 修改，先提出具体差异、影响、既有站点回归和回退，再取得明确确认。SSL 暂缓约束仍有效，所以正式 HTTPS/QR 印刷仍是阻断项。

公开 Nginx 只在明确可信代理地址范围后才配置 `set_real_ip_from`、`real_ip_header X-Forwarded-For`、`real_ip_recursive on`，禁止信任所有地址。后台 `ADMIN_TRUSTED_PROXIES` 也只填实际管理代理来源。否则地区可能显示代理/内网位置，不能把它当客户真实地区。SSH 隧道登录的来源通常只反映隧道出口，不宣称能识别使用者所在地。

公开访问文件使用受控 logrotate，示例为 `logrotate.example`，仅向准确 public 服务发 USR1 重开日志，不使用全局容器命令。确认实际保留期与磁盘容量后启用；当前访问统计仍只读取当前访问文件（最多 16 MiB），**不是跨日志轮转的永久统计系统**。部署前确认该统计范围是否满足业务要求。

## 5. 必须在测试容器完成的门禁

- 验证非 root UID、只读挂载、资源限制和磁盘行为；当前 CPU/内存值是初始候选，不是容量保证。
- 检查 backend/admin health 与真实 API/数据库连通；公开 health 只证明静态进程活着，还要检查具体批次内容。
- 用真实验证码登录；旧 dev 验证码 0 必须失败。验证登录限流 429、密码重置、撤权、角色越权、不可自审。
- TEST 编码即时提示及直接 API 拦截；完整产品→批次→审核→发布→公开页，含真实 PNG/JPEG 上传与历史回滚。
- 验证公开页面没有后台请求；只停止该项目 backend 后，已有公开页面仍可读取。
- 测试 `/b/{code}`、Current/历史 JSON、图片、缺失资源真404、缓存头、CSP、无私有文件泄漏。
- 地区库、可信代理、日志轮转；确认伪造 X-Forwarded-For 不改变可信归属。
- 本项目一致性备份与新目录恢复，检查全部 Current/历史/图片；验证上一版本程序和数据库是否兼容。
- 记录既有站点回归结果。测试通过并人工确认后，使用空白生产库和新配置重复初始化；禁止拷贝本地 TEST 账号与数据。

## 6. 备份和回退

先通过完整 Compose 路径和项目名停止**仅 backend**（公开页继续服务），确认准确 backend 容器已停止且无待对账发布；再执行：

```sh
python3 deploy/production/backup.py backup --db /absolute/admin/data/db/passport.db --media /absolute/admin/data/media --work /absolute/public/data/work --published /absolute/public/data/published --out /absolute/private-backup/new-version --offline-confirmed
python3 deploy/production/backup.py verify --source /absolute/private-backup/new-version
python3 deploy/production/backup.py restore --source /absolute/private-backup/new-version --out /absolute/private-restore/new-version
```

`--offline-confirmed` 是操作者在核对确切服务已停止后的声明，工具不能替代 Docker 状态确认。备份工具还会检查未完成发布和数据库写锁，拒绝覆盖、嵌套备份目标、符号链接及校验不符。恢复结果仅是新目录副本；必须对账并验证后再切换本项目绑定。程序镜像、管理前端、公开 site、Compose、release manifest 与私有配置要另做版本化备份，不能只备份 DB。

失败时保留现场和最后验证的公开版本，不删除历史文件或全局 prune。回退旧应用前先确认 DB schema 兼容；有迁移的不兼容回退需恢复匹配数据副本，不能自动做向下迁移。业务内容回滚使用应用内安全回滚流程创建新版本。共享 Caddy 的回退也必须按单独审批的增量方案执行。

参考：[Docker Compose services](https://docs.docker.com/reference/compose-file/services/)；[SQLite Backup API](https://www.sqlite.org/backup.html)。
