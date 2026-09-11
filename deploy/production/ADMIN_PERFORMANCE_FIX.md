# 管理页面资源传输优化

现场测量中，服务器本地 app-config GET 约 1 毫秒，入口 JavaScript 约 0.5 毫秒；同一入口脚本经 Mac SSH 隧道曾耗时约 12.85 秒。该对比只能说明该次请求传输耗时明显，不能证明所有受保护业务接口均快，也不能将隧道、网络线路或带宽中的某一项单独认定为根因。

已确认旧管理 Nginx 未启用 gzip_static，且对所有响应设置 no-store。镜像内已有预压缩构建资源，其中入口 JavaScript 原文件 237462 字节，gzip 文件 89069 字节。新配置只对 js/css 目录下带内容哈希的构建资源启用预压缩和浏览器私有长期缓存；HTML、API 和登录内容继续 no-store。找不到的哈希资源返回 404，不回退成 HTML。安全响应头保持存在。

gzip_static 根据客户端能力发送已有 .gz 文件，避免动态压缩增加 CPU 开销；gzip_vary 区分压缩响应。配置依据：[Nginx gzip_static 文档](https://nginx.org/en/docs/http/ngx_http_gzip_static_module.html)。缓存响应头及继承规则依据：[Nginx headers 文档](https://nginx.org/en/docs/http/ngx_http_headers_module.html)。不对业务 JSON 启用缓存或动态压缩。

## 已有测试环境的应用方式

`repair-admin-performance.py --env <已有固定镜像环境文件>` 只接受独立测试项目、指定测试目录和回环端口。它先确认安装的 Compose 等于已审核模板、镜像等于运行容器、后台网络正确，然后备份 Compose，安装 `/opt/passport-admin-test/nginx-performance.conf`，通过单独只读挂载覆盖管理镜像的 Nginx 配置。运行同镜像的 Nginx 配置校验后，仅重建 admin，禁止构建、拉取及重建依赖。后端和数据不重做初始化，共享 Caddy、Directus、edge 不修改。

完成检查包括：后台 ID 和启动时间未变、API HTTP 200 且业务 code 200、HTML 和 API 仍 no-store、资源有 gzip 和 immutable 响应头、gzip 解压后与原始脚本逐字节一致。API 可能有多条 Cache-Control 响应头，检查合并后的指令，而不要求完整字符串等于 no-store。

失败后自动恢复备份 Compose，并只重建 admin。备份和配置保留以供诊断。再次执行时，只允许遗留配置与当前候选完全一致；已成功安装后不应重复执行。

## 后续发布与回退

源码中的 nginx-admin.conf 已同步修正，后续正常构建的管理镜像自带此优化。当前服务器的性能配置挂载是既有镜像的临时修复，**后续镜像升级必须检查并协调这份挂载**，避免旧挂载遮住新镜像配置。标准 compose.admin.yml 无该挂载，升级前必须核查安装版与模板差异，保留本次备份。

人工回退使用脚本打印的确切备份，恢复到该测试目录的 docker-compose.yml，再使用同一固定镜像环境文件、明确的测试 Compose 文件和项目名，只对 admin 执行 `up -d --no-build --pull never --no-deps --force-recreate --wait --wait-timeout 120 admin`。无需删除数据、网络或镜像。

减少字节数和允许资源复用是可验证的收益，不是所有操作都会立即达到某个速度的保证。仍需用浏览器验证菜单切换与真实业务操作；若小体积接口也慢，应继续测量网络延迟和受保护接口的服务器处理时间。
