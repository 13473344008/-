# 非 root 镜像读取权限修复

服务器在 umask 077 下检出源码后，后台初始化出现 `/bin/sh: cannot open /app/entrypoint.sh: Permission denied`。镜像原来直接 COPY 工作区文件，未显式设置运行时权限；Git 工作区普通文件可能是 0600、目录可能是 0700，导致镜像内 root 所有的文件无法由 UID 10001 读取。这是构建定义的遗漏，不能通过让业务服务以 root 运行解决。

修复明确设置后台二进制 0755、SQL 0644、入口脚本 0555，以及管理 Nginx 配置 0644；管理端静态目录补齐读取和目录遍历权限。Dockerfile 在 USER 10001:10001 后加入实际读取检查，后台还执行 --help 验证二进制可启动。这些检查会在目标镜像构建时运行，本地无 Docker，仅验证了配置静态约束及脚本语法；不能宣称已在本地运行容器通过。

执行 rebuild-permissions.py 时明确使用已验证的受限构建器，保留原测试参数、旧镜像及已经生成的数据库/凭据。输出采用新标签，成功后生成独立 release.env，引用新的镜像 ID。脚本只构建，不运行迁移、bootstrap、服务启动或修改 Caddy。已有测试目录不应重新初始化；取得 FIXED_ENV 后再从失败位置继续。

前一条服务器命令被粘贴成 `7h(`，导致子 Shell 起始语法错误，随后 `set -e` 在登录 Shell 中生效；迁移容器失败后 SSH 退出与这一执行顺序一致。应重新连接，在空提示符下执行短命令，不复制终端提示符或残留字符；这不等于服务器重启证据。

参考：[Docker COPY 权限说明](https://docs.docker.com/reference/dockerfile/#copy---chmod)。
