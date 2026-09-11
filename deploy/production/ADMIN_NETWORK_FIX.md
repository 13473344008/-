# 测试管理入口端口修复核查报告

## 结论与证据边界

现场终端输出确认 backend 和 admin 容器均为 Healthy，但管理容器的端口栏仅显示容器端口，未出现 `127.0.0.1:18080->8080/tcp`。Compose 查询端口返回 `invalid IP:0`，宿主机访问 app-config 被拒绝。因此，容器健康不能证明宿主机入口已经可用。此前数据库检查和迁移已通过，不需要重新初始化数据库或生成管理员密码。

原始 Compose 让管理 Nginx 和后端仅连接 `internal: true` 网络。Moby 项目中的同类现场报告描述了内部网络单独连接时，端口请求仍存在、实际端口映射为空的现象；这是匹配度很高的线索，不能代替本机检查。修复脚本必须先核对 HostConfig.PortBindings、NetworkSettings.Ports 和网络属性，满足条件后才允许修改。[Moby 现场讨论](https://github.com/moby/moby/discussions/53256)

Docker 官方说明支持前端同时连接普通 bridge 与内部网络、后端只连接内部网络的部署方式。本次采用这一结构，新增网络由数字身份证测试管理 Compose 项目单独管理。[Docker 多网络说明](https://docs.docker.com/engine/network/#connecting-to-multiple-networks)

## 变更与影响

| 对象 | 变更后行为 |
| --- | --- |
| backend | 仅连接 admin_private，不发布宿主机端口；本次不重建 |
| admin Nginx | 连接 admin_private 和独立 admin_access；只绑定 127.0.0.1:18080 |
| admin_access | 项目自己的普通 bridge，不是 external 网络，不接入共享 edge |
| 数据库、密码、镜像 | 保留现有文件和正在使用的镜像，不重新初始化或构建 |
| Caddy、Directus、旧公开站点 | 不对其容器、配置或网络成员执行操作 |

管理 Nginx 会短暂中断，新增网络允许该 Nginx 发起出站连接；后端仍保持内部网络。共享宿主机与 Docker 的共同故障风险仍存在。无需开放公网 18080、安全组或修改 DNS、HTTPS、Caddy。

## 执行与成功标准

更新到包含本修复的源码提交后，使用现有 permissions-build 目录中的 release.env 执行 `repair-admin-network.py --env <现有固定镜像环境文件> --apply`。省略 `--apply` 时只检查。脚本仅接受已知测试项目、目录、端口和原始 Compose 哈希；镜像必须与正在运行的容器一致。任何不匹配都应保留输出并重新核查，不能删除检查绕过。

脚本先保存原始 Compose，再只重建 admin 服务，显式禁止构建和拉取，并使用 `--no-deps`。完成后确认后端容器 ID 与启动时间未变、实际映射仅为回环端口、网络成员符合预期，并从宿主机读取 app-config 的 HTTP 状态和业务 code。全部通过才输出 `BACKEND_UNCHANGED` 和 `TEST_ADMIN_READY`。这些标记尚待现场执行确认。

本地已通过静态隔离契约和 Python 语法/帮助入口检查。本地没有 Docker，不能把这些结果视为服务器运行验收。管理入口恢复后，还需要 SSH 隧道登录和业务验收；公开测试站点与生产发布另行完成。

## 失败处理与回退

失败时保存输出中的 `BACKUP=` 路径，不重做 bootstrap，不清理数据库，不执行全局 prune 或 compose down。修改后的文件可能已安装而容器未完成启动，需结合报错判断。

确需恢复旧配置时，将脚本保存的 `docker-compose.before.yml` 用 `sudo install -m 0644 -o 10001 -g 10001` 恢复到 `/opt/passport-admin-test/docker-compose.yml`，然后使用同一个固定镜像环境文件、明确的该 Compose 文件及 `-p passport-admin-test`，执行 `up -d --no-build --pull never --no-deps --force-recreate admin`。只恢复管理网关；旧配置会恢复到原来的端口不可用状态，不代表问题解决。新增的空项目网络可以保留，不为回退操作清理共享资源。

## 来源

- 现场证据：部署终端粘贴输出，2026-09-11；包括容器健康状态、端口输出、Python ConnectionRefusedError。未取得修复后的现场输出。
- Docker 官方文档：[Networking overview](https://docs.docker.com/engine/network/)，核对日期 2026-09-11。
- Moby 项目讨论：[Published ports silently fail for containers attached only to an internal bridge network](https://github.com/moby/moby/discussions/53256)，核对日期 2026-09-11。同类使用者报告，非本机原因的独立证明。
