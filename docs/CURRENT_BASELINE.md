# T0 — 当前项目冻结基线

记录日期：2026-09-07。工作区：`/path/to/ID`。

本轮只执行 T0、T1、T2，只新增 docs。用户本轮新要求允许规划独立管理后台及其独立数据库，更新了旧“第一阶段仅静态”的阶段范围；不取消 Directus、Caddy、公开服务隔离和服务器操作红线。AGENTS.md 与现有 POC 均不改写。本轮结束必须停止，人工确认后才进入 T3。

## 文件与功能

开始时工作区无 `.git/`、`docs/` 或 `admin/`。冻结通过文件清单与 SHA-256 实现，不声称已创建 Git commit。共 53 个既有普通文件，其中 site 有 7 个文件；完整清单及逐文件哈希见 [BASELINE_SHA256.json](BASELINE_SHA256.json)。该清单也覆盖 outputs、work、.qa、测试和历史说明，不能替代异机备份。

```text
ID/
├── AGENTS.md
├── README.md
├── LOCAL_REPORT.md
├── site/
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js
│   ├── products/PF-STD.json
│   ├── batches/PF-TEST-001.json
│   ├── schemas/{product,batch}.schema.json
│   └── assets/                         # 空目录
├── tests/{schema.py,browser.cjs}
├── .qa/                               # 历史截图、报告、测试结果
├── outputs/                           # 历史 Word 与产品编码工作簿
├── work/                              # 编码表生成脚本和检查资料
├── update_domain.py
└── 数字身份证域名与URL规范_V1.1.docx
```

已确认：HTML、CSS、Vanilla JavaScript；通过批次编码加载 `/batches/{code}.json`，再按 product_code 加载 `/products/{code}.json`。展示产品身份、批次、原料、工艺、检测、包装储存、认证、制造商八模块。支持错误提示、编码/关联验证、文本转义、受限本地图片、手机布局；两个 JSON Schema 使用 Draft 2020-12。没有后台、数据库、审核、发布或历史快照引擎。

现有样例为 PF-STD 马铃薯雪花片 / PF-TEST-001。页面始终显示测试用途标识及 noindex/nofollow。检测结果为空、NOT_TESTED；认证条目 UNVERIFIED；不能当成真实 COA 或商业证明。现有业务状态 TEST/PENDING/RELEASED/HOLD/REJECTED 与未来编辑审核工作流是不同概念。

## 当前本地测试方式

原 README 记录的启动方式（本轮仅记录，未执行）：

```sh
cd /path/to/ID/site
python3 -m http.server 8089 --bind 127.0.0.1
```

正常入口：`http://127.0.0.1:8089/?batch=PF-TEST-001`。另检查无参数、不存在批次、非法参数。端口实时占用未检查，不停止未知进程，也不使用已有 SSH 转发。

开发校验：`node --check site/js/app.js`；安装 jsonschema 4.26.0 的虚拟环境运行 `tests/schema.py`；有 Playwright/Chromium 时以 `PDI_BASE_URL=http://127.0.0.1:8089` 运行 `tests/browser.cjs`，完整环境命令见既有 README。两个测试会重写 `.qa/product-id/` 结果，因此本輪冻结核验不执行它们。

已读取历史结果文件：Schema 21 项 PASS，浏览器 24 项 PASS。这是此前结果，不是本轮重新执行，也不代表服务器或全部浏览器通过。本轮执行的是既有文件哈希复核，以及上游前后端只读静态契约检查。

## 已知限制

1. `/b/{batch}` 只有前端解析；Python 默认服务器会 404。此前通过模拟 HTML 回退验证，实际 Nginx 路由待 T11/T13。
2. 浏览器每次引用可变产品 JSON；产品变更会改变旧批次显示。这不是不可变 Published Snapshot。T11 必须新增独立正式静态入口读取完整快照，不能声称保持当前读取方式也能冻结历史。
3. 没有批次覆盖、复制批次、自定义模块管理、登录/RBAC、审核、发布历史或回滚。
4. 手工维护 JSON；Schema 固定字段且禁止额外属性，不能直接塞入未来 custom_sections。正式 Public Payload 契约需单独版本化，保留旧 Schema 和样例。
5. 无真实图片与完整商业资料；Safari、Firefox、实体手机未验证；noindex 不提供访问控制。
6. 本地目录与历史服务器说明不证明现有服务器部署状态。本轮禁止连接 ECS，不核验 `/opt`、Docker、Caddy、DNS、HTTPS。

## 冻结结论

既有 site 文件修改：No。服务器连接：No。业务功能开发：No。新增内容仅在 docs；上游研究副本在本机 `/tmp/pdi-t012-research/`，未放入 admin、未安装依赖、未启动后台或数据库。
