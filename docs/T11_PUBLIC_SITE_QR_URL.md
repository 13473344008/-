# 【T11 执行结果】

T11 状态：**等待人工验收；所有本轮本地服务已停止。** 用户已人工验收 T0–T10。本轮仅实现 T11，未进入 T12/T13，未连接业务服务器或部署。

| 类别 | 结果 |
|---|---|
| Public Site / Stable Batch URL / Version URL / Current Resolution | PASS |
| Schema Router / Public Renderer / Inspection / Custom Sections | PASS |
| Published Assets / Translations / RTL | PASS |
| Working Preview / Review Preview / Published Preview / QR Target URL | PASS |
| Security / Performance / Mobile / Nginx Local | PASS |
| Backend Independence / Fresh Publish Fixture / Rollback Fixture | PASS |
| Browser E2E / Integrity / Baseline Protection | PASS |

## Public Architecture / 目录

```text
site/                              原始 7 文件 POC，原文保留
public-site/
  index.html / 404.html / robots.txt / README.md
  css/passport.css
  js/boot.js                       独立有限时降级
  js/app.mjs                       静态路由、读取、错误与语言切换
  js/render.mjs / render.d.mts      公共和内部预览共用 DOM 渲染器
  js/i18n.mjs                      六语言模块/状态文案
  js/schema.mjs / schema-1.0.mjs    固定 1.0 契约及版本分派
  js/urls.mjs / urls.d.mts          稳定/历史 URL Builder
  deploy/nginx.conf.template       本地验收模板，未部署
runtime/t11/publish/
  published/{batch_code}.json      已发布完整 Current Snapshot
  versions/{batch_code}/vN.json    不可变历史 Snapshot
  assets/sha256/xx/{sha256}.png     不可变公开图片
runtime/t11/releases/             私有工作目录，Nginx 不暴露
```

原 53 个 T0 基线文件再次验证；原 site 另备份至 `runtime/t11/baseline/site/`。37,126 个 T4–T10 运行证据及历史迁移文件 Hash 全部未变。历史报告没有改写成新结论。

## Stable Batch URL / Version URL / Current Resolution

稳定入口 `/b/{batch_code}`，历史入口 `/b/{batch_code}/v/{version}`。二维码目标只含批次稳定码，无内部 UUID、版本或语言。历史 URL 不跳 Current。

T9/T10 的 Current 本来就是完整 JSON，并非额外 Manifest 指针。稳定页先读取 `published/CODE.json`，通过 Schema、批次码和版本检查，再读取其 `versions/CODE/vN.json`，要求两个响应原文字节表达完全一致才显示。失败显示 temporarily unavailable；不 fallback 到数据库、管理 API 或旧 POC。历史页只读指定历史 JSON 并检查 URL/载荷批次和版本相符。

这是对当前完整快照结构的轻量一致性检查，不重复实现后台全部 Integrity Engine。发布时的 Hash、资产和关系完整性仍由 T9/T10 引擎验证；私有 Manifest 不对客暴露。**Hash 不是签名；同时有权篡改 Current 和历史文件的人不在此检查的防护范围内。** 浏览器不逐图重算 SHA；历史页依赖已验证、受保护的不可变发布存储。

## Schema Router / Public Renderer / Modules

当前严格支持 `schema_version=1.0`，内嵌 Schema 与正式文档中的 Schema 相同。未知 Schema 安全失败，未来 1.1/2.0 应注册独立验证/适配逻辑。固定 Schema 的闭合关键字验证器不是通用 JSON Schema 产品。

独立 Vanilla JS；正式端不读取原 Product JSON 或 Batch JSON，也不加载 Vue/Go Admin bundle。所有业务文字由 Snapshot 提供，使用 createElement/textContent；没有 raw HTML Renderer。产品、原料、工艺、批次、检验、认证、包装/储存、制造商、自定义模块、图片和发布信息有对应渲染路径；合法全空模块隐藏。认证数据在真实发布 fixture 中为空，未伪造持证声明。

Inspection 循环任意项目，pass/fail/not_tested/not_applicable/pending/informational 均有文字。text/key_value/table/asset_gallery 四种类型受控渲染；表格置于可键盘访问的横向滚动容器，页面本身不横向溢出。测试工艺为用户指定的九步骤；全部 TEST 记录显示固定商业禁用提示。

## Translations / RTL / Assets

默认 EN；`?lang=en|zh-CN|es|ar|fr|de`，切换只更新页面文字与 URL 查询参数，不重新选择 Current。实际 Snapshot 中六语言产品名均经正式模板译文保存、封版及发布。缺译字段回退同一 Snapshot 的源语言；显式 null 保留 clear，绝不从模板复活。界面模块名和检验状态有六语言文案，其余字段标签目前采用可读英文标签。

AR 设置 document 和内容 dir=rtl；编码、日期、数量、版本等技术值通过 LTR isolate 保持可读。测试语言刷新、未知语言回 EN、中文缺译和 null clear。

公开图片只接受严格匹配 SHA256 目录/文件名的 PNG 路径。禁止 javascript/data/file/外部地址和后台 mutable media path。首屏产品图可 eager，其余 lazy；固定 4:3 容器与 width/height 避免图片加载撑动。缺图显示安全占位，无无限重试。内部预览例外仅使用认证响应中冻结且验 Hash 的 PNG base64，不读公开路径上的旧图，也不取 mutable 原文件。

## Working / Review / Published Preview

新增认证 `GET /api/v1/passport-batches/:id/preview?kind=working|review&review_id=...`。JWT → LiveIdentity → Casbin → PermissionAction，服务按 batch 数据范围查询；所有响应 no-store。没有永久预览 Token、匿名 Draft URL 或公开 Draft 文件。

Working 使用当前已保存 Draft，经同一 readiness 读取、同一 publishing.Build 白名单构造；未保存改动按钮禁用，不符合构建条件返回 422。Review 按明确 review_id 取同批次冻结 Candidate，验证原始 Hash，不要求它仍是 Current Review，因此可检查退回改稿前的旧候选。两个入口供合法业务读角色使用，均不创建 Revision、PublishRecord 或 Audit 记录。

私有 Builder 为满足 1.0 外壳临时提供 version=1/当前时间，但响应明确 kind，私有共用渲染器完全隐藏 publication 区并显示 `DRAFT / INTERNAL PREVIEW — NOT PUBLISHED` 或 `REVIEW PREVIEW — NOT PUBLISHED`。这些占位元数据不是发布编号，也不会保存成正式 Snapshot。

管理端 PreviewPanel 嵌入 Batch 的 Review/History 区，选择冻结审核记录或历史发布版本。共享 renderer 在 Shadow DOM 中运行以隔离后台样式。View Published 是真正静态 URL 新窗口，noopener/noreferrer，无 JWT。

实际同一批次 `PF-T11-TEST-PREVIEW`：正式 V1=25kg；旧批准 Candidate=22kg；退回后当前 Draft=20kg。真实 Editor/Reviewer 登录点击预览，匿名 Published=25kg，API 与浏览器双重验证。缺少权限匿名 401、跨批 review 404；预览前后 Working/Review/Audit 数据精确一致。

## QR Target Builder

配置 `VUE_APP_PUBLIC_BASE_URL`、`VUE_APP_PUBLIC_MODE=production|local`。origin 不得带凭据、路径、query、fragment。production 要求 HTTPS 并拒绝 localhost、*.localhost、127/8、IPv6 loopback；HTTP 仅限显式 local。测试 origin 为 `http://127.0.0.1:19540`，界面标明仅限测试、不能生产印刷。业务代码没有正式域名默认值。

Batch code 与正式 Schema 使用同一 ASCII 字符边界、最大 64 字符，拒绝空白、尾换行、编码穿越、斜杠等；历史版本为正安全整数。复制稳定/版本 URL 均真实验证；Clipboard 缺失时提示手动复制。未生成 QR PNG、SVG、PDF 或标签模板。

## Nginx Local Route / Caching / Security

官方源包 [Nginx 1.30.4](https://nginx.org/download/nginx-1.30.4.tar.gz) 编译到项目 runtime 内，源码 SHA 见 nginx-provenance.json；未做发行签名验证，未系统安装。实际二进制 `runtime/t11/tools/nginx-1.30.4/objs/nginx`，实际配置 `runtime/t11/nginx.conf`，监听仅 `127.0.0.1:19540`。`nginx -t` 通过。

Nginx 按白名单提供 HTML、JS/CSS、Published JSON、Versions、CAS PNG。禁止目录索引和符号链接；未知文件真实 404，不全局 SPA fallback。原始 request_uri 路径中的百分号、反斜杠、点段被拒绝；Nginx 自身无法归一化的越根请求直接 400，其余非法路由 404。`mjs` MIME 显式设 application/javascript，与 nosniff 相容。

Current、HTML、未指纹化 JS/CSS：`no-cache, max-age=0, must-revalidate`。历史 JSON 与 CAS PNG：`public, max-age=31536000, immutable`；ETag/304 实测通过。错误页重写至安全 404，不把错误响应长期 immutable 缓存。

CSP：default-src none；script/style/img/connect 仅 self；base-uri none、form-action none、frame-ancestors none，无 unsafe-inline。另 nosniff、no-referrer、X-Robots-Tag noindex,nofollow；robots Disallow /，HTML meta 同样不索引。robots 不是权限控制。无第三方 JS/CDN/字体/跟踪/图片请求，系统字体栈。

## Fresh Fixture / Browser / Network / Backend Stop

独立空库运行全部 16 次 Migration，真实 API 建产品、六语言模板、封版、Batch、Review、批准、Publish V1。随后真实 Publish V2，再回滚源 V1 为新 V3。三个阶段各用真实浏览器打开稳定页和历史 V1，证明二维码目标不变。另一独立迁移空库与 T10 数据副本升级结构一致；重复迁移幂等，原业务列值保留。

继续沿用 T10 已披露的 fixture 方法：仅在 T11 测试库将已发布 Batch 工作流受控置 Draft，以开启后续编辑轮次，再走真实保存、提交、独立审核和发布。**没有新增正式 Published→Draft 业务入口，也未修改历史行或快照。** 三态例子通过真实 review/return API 保留旧候选后改稿。

真实浏览器为 Chromium，视口 375/390/430/1280/1440；检查模块、六语言、RTL、历史、动态 Inspection、四种自定义模块、图片、复制、登录/退出、无未捕获 JS Error。安全反例通过浏览器请求拦截注入损坏 JSON/未知 Schema/错误 Current/危险图片路径，DOM 内存 fixture 验 XSS 纯文本；未篡改正式已发布文件。另测网络失败 Retry、慢网、JS 模块缺失 12 秒有限降级和完全禁用 JS。

匿名网络证据仅含 Nginx 静态 origin，无 Authorization/JWT、Admin API、Directus、SQLite 或旧 Product/Batch JSON 请求。见 browser-v1/v2/rollback/full/stopped.json 内逐请求清单。

最后停止 Backend 18107 和 UI 19539，将配置 SQLite 主文件及伴随文件保留移到 db-offline，确认原配置路径不存在，再打开全新匿名浏览器：Stable V3、历史 V1、六语言、冻结图片均通过，HTTP 缓存/头测试也通过。发布目录 Hash 前后精确不变。随后恢复数据库文件，关闭 Nginx，18107/18108/19539/19540 均不再监听。

## Performance / Integrity / 修复记录

最终未压缩体积：HTML **1,417 B**；CSS **5,632 B**；全部运行 JS **35,159 B**（含 1.0 Schema）；Current V3 JSON **8,189 B**；单张规范化测试 PNG **80 B**。本地加载时序和逐资源传输见 performance.json。小 PNG 是明确的受控 fixture，不能据此推断真实生产图片加载速度或广域网体验。未做 Lighthouse 满分/负载/CLS 实验室结论。

SQLite integrity_check=ok、foreign_key_check 空。全部四份成功历史 Payload 与 DB payload/hash 一致，图片 bytes/size/hash 一致；Current 与后台停止前后文件一致。没有公开内部字段。

调试中发现并修复：

1. T9 语义校验原来仅接收 TEST- 前缀，与正式 Schema 的独立 TEST 段及本轮指定 PF-T11-TEST-001 不一致。修正业务校验为 TEST 段，保留 Schema 和强制 TEST 提示，补正反例 Go 测试。首次失败 DB/资料保留在 preflight-failed；完整链从另一个空库重新开始，未复用失败版本号。
2. Nginx 默认 mjs MIME 缺失导致模块不执行，已修复并重跑浏览器。
3. Preview readiness 错误曾被通用错误处理转换 500，现保留类型返回 422 并通过复验。
4. 管理 UI 新文案最初违反语言包检查，已移入中英语言包，301 项 UI 单测通过。

ESLint 最终 0 errors，30 个既有 warnings；type-check 与生产构建通过；发布包 Go race 测试通过。没有修改历史 Migration，新增的授权 Migration 是第 16 个版本。不改变 DATA_MODEL、Public Schema 本体或 T9/T10 历史报告。

## 新增 / 修改文件

新增：上列整个 `public-site/`；`app/passport/service/preview.go`、`app/passport/apis/preview.go`、`app/admin/router/passport_preview.go`；`cmd/migrate/migration/version/1789344000000_private_preview.go`；`app/passport/publishing/t11_contract_test.go`（均位于 admin/go-admin）；管理端 `src/api/passport/preview.ts`、`src/views/passport/previews/PreviewPanel.vue`、中英 `src/lang/*/passport/preview.ts`；`admin/t11/` 独立设置、fixture、浏览器/API/静态/迁移/文件检查及报告脚本；本报告、T11_TEST_RESULTS.json。

修改：后端 `app/passport/publishing/semantics.go` 的 TEST 段校验；管理端 `src/views/passport/reviews/ReviewPanel.vue`、`src/lang/en-US/index.ts`、`src/lang/zh-CN/index.ts`；本地专用 `.env.t11.local`；docs/TASKS.md。运行配置、构建产物、截图、证据仅在 runtime/t11。无 lockfile 或依赖包更新。

## Known Risks / T12–T13 Boundary

- 本轮仅 Chromium 真实执行。Safari/WebKit 不在本机浏览器缓存，未实机运行；仅静态复核模块/DOM/CSS 使用方式，不宣称全浏览器验收。
- 共用 Snapshot 源语回退正确，但部分通用字段标签保留英文；非英语输入法、长篇真实译文和无障碍读屏尚未全面实测。
- 图片仅受控 PNG；当前认证数组为空，未伪造真实认证。真实商业资料与法规内容未核验。
- 静态一致性检查依赖受保护发布存储，不提供数字签名、防管理员篡改或浏览器逐图完整性引擎。
- 本轮只本机 HTTP；不能据此承诺中国/海外网络、生产缓存代理、容器资源限制、断电或同宿主机绝对隔离。
- 历史 URL 当前可匿名访问，是否对客户长期开放由后续策略决定。可读角色的历史审核预览仍受批次数据权限控制。
- 不运行服务器命令，不 SSH、不改 Caddy/Directus/生产 Docker/DNS/HTTPS，不生成生产 QR，不部署 public-site。T12 必须另获人工放行，T13 继续禁止。

## 最终检查统计

**75 / 75 Gates PASS；600 项断言/叶测试 PASS，0 FAIL。** 含 301 项上游 UI 单测，计数口径见机器报告。

| 套件 | PASS | FAIL |
|---|---:|---:|
| browser-v1 | 5 | 0 |
| browser-v2 | 5 | 0 |
| browser-rollback | 5 | 0 |
| browser-full | 47 | 0 |
| browser-edges | 9 | 0 |
| preview-api | 21 | 0 |
| preview-browser | 21 | 0 |
| http-checks | 25 | 0 |
| static-checks | 48 | 0 |
| migrations | 10 | 0 |
| files | 18 | 0 |
| db-offline | 3 | 0 |
| browser-stopped | 34 | 0 |
| stopped | 5 | 0 |
| publishing_go_race | 43 | 0 |
| upstream_ui_unit | 301 | 0 |

## 75 Gates

| Gate | 条件 | 结果 | 证据 |
|---|---|---|---|
| 1 | 正式 public-site 与原 POC 分离。 | PASS | runtime/t11/test-artifacts/files.json |
| 2 | Stable Batch URL 可用。 | PASS | runtime/t11/test-artifacts/browser-v1.json |
| 3 | Stable URL 不包含 Version。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 4 | Stable URL 不包含内部 DB ID。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 5 | Current Resolution 不查数据库。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 6 | Current Resolution 不调用 Admin API。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 7 | 历史 Version URL 可用。 | PASS | runtime/t11/test-artifacts/browser-v1.json |
| 8 | 历史 Version 不被 Current 覆盖。 | PASS | runtime/t11/test-artifacts/browser-v2.json |
| 9 | schema_version 路由有效。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 10 | 不支持 Schema 安全失败。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 11 | 正式端只读取 Published Snapshot。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 12 | 不再读取旧 Product JSON + Batch JSON。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 13 | Product 模块正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 14 | Batch 模块正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 15 | Process 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 16 | Inspection 动态渲染。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 17 | Custom text 正确安全渲染。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 18 | key_value 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 19 | table 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 20 | asset_gallery 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 21 | Published Assets 只使用冻结路径。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 22 | 页面无后台 mutable media URL。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 23 | 首屏以下图片懒加载。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 24 | 移动端 375px 可用。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 25 | 移动端 390px 可用。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 26 | 移动端 430px 可用。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 27 | Desktop 1280 可用。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 28 | 六语言数据可展示。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 29 | Language Switcher 可用。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 30 | Arabic RTL 正确。 | PASS | runtime/t11/test-artifacts/browser-edges.json |
| 31 | Translation fallback 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 32 | Working Preview 与 Published 分离。 | PASS | runtime/t11/test-artifacts/preview-browser.json |
| 33 | Review Preview 与 Published 分离。 | PASS | runtime/t11/test-artifacts/preview-browser.json |
| 34 | Published Preview 读取真正 Release。 | PASS | runtime/t11/test-artifacts/preview-browser.json |
| 35 | 三种 Preview 内容不串。 | PASS | runtime/t11/test-artifacts/preview-browser.json |
| 36 | Stable QR Target Builder 可用。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 37 | QR Target 使用 Batch Code。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 38 | QR Target 不使用 Version。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 39 | Base URL 可配置。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 40 | 不存在正式 localhost 硬编码。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 41 | 不存在 Batch 404 正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 42 | 非法 Batch Code 拒绝。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 43 | 不存在 Version 404。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 44 | 损坏 JSON 安全失败。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 45 | 不支持 schema 安全失败。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 46 | Client XSS 不执行。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 47 | 危险 Asset URL 不加载。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 48 | Path Traversal 防护。 | PASS | runtime/t11/test-artifacts/http-checks.json |
| 49 | 公开浏览器匿名可访问 Published。 | PASS | runtime/t11/test-artifacts/browser-v1.json |
| 50 | 匿名不可访问 Working Preview。 | PASS | runtime/t11/test-artifacts/preview-api.json |
| 51 | Network 不请求 Admin API。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 52 | Backend 停止公开 Stable URL 正常。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 53 | Backend 停止 Version URL 正常。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 54 | Backend 停止 Assets 正常。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 55 | SQLite 不可访问公开端仍正常。 | PASS | runtime/t11/test-artifacts/db-offline.json |
| 56 | V1→V2 Stable URL 更新到 V2。 | PASS | runtime/t11/test-artifacts/browser-v2.json |
| 57 | V1 历史 URL 仍显示 V1。 | PASS | runtime/t11/test-artifacts/browser-v2.json |
| 58 | Rollback Current 后 Stable URL 显示新 rollback version。 | PASS | runtime/t11/test-artifacts/browser-rollback.json |
| 59 | Public JSON Internal 字段仍无泄漏。 | PASS | runtime/t11/test-artifacts/files.json |
| 60 | TEST RECORD 标识正确。 | PASS | runtime/t11/test-artifacts/browser-full.json |
| 61 | 公开页性能保持轻量。 | PASS | runtime/t11/test-artifacts/static-checks.json |
| 62 | Nginx 本地 Route 验证通过。 | PASS | runtime/t11/test-artifacts/http-checks.json |
| 63 | Fresh DB→Review→Publish→Public 完整通过。 | PASS | runtime/t11/test-artifacts/browser-v1.json |
| 64 | Rollback Fixture Public 验证通过。 | PASS | runtime/t11/test-artifacts/browser-rollback.json |
| 65 | 浏览器无未捕获 JS Error。 | PASS | runtime/t11/test-artifacts/browser-stopped.json |
| 66 | integrity_check 仍 ok。 | PASS | runtime/t11/test-artifacts/files.json |
| 67 | foreign_key_check 无异常。 | PASS | runtime/t11/test-artifacts/files.json |
| 68 | 原 53 个 T0 基线文件保留证据完整。 | PASS | runtime/t11/test-artifacts/files.json |
| 69 | 原 site POC 未被无记录破坏。 | PASS | runtime/t11/test-artifacts/files.json |
| 70 | 未连接服务器。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |
| 71 | 未修改 Caddy。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |
| 72 | 未修改 Directus。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |
| 73 | 未修改生产 Docker。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |
| 74 | 未生成生产正式 QR 文件。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |
| 75 | 未进入 T12。 | PASS | Execution scope: local T11 only; tool/action audit and protected baseline. No server or production action executed. |

## 95 项逐项答复

1. **是否建立正式 public-site？** 是，已通过本地验收。
2. **是否保留原 POC？** 是，已通过本地验收。
3. **Stable Batch URL 是否实现？** 是，已通过本地验收。
4. **URL 是否使用 Batch Code？** 是，已通过本地验收。
5. **URL 是否不含 DB ID？** 是，已通过本地验收。
6. **URL 是否不含 Version？** 是，已通过本地验收。
7. **Current 是否纯静态解析？** 是，已通过本地验收。
8. **是否完全不查 SQLite？** 是，已通过本地验收。
9. **是否完全不调用 Admin API？** 是，已通过本地验收。
10. **历史 Version URL 是否可用？** 是，已通过本地验收。
11. **V1 是否不会被 V2 覆盖？** 是，已通过本地验收。
12. **Rollback 后 Current 是否显示新版本？** 是，已通过本地验收。
13. **是否根据 schema_version 解析？** 是，已通过本地验收。
14. **当前支持哪个 schema？** 1.0；未知版本安全失败，未来版本需独立注册解析器。
15. **不支持 schema 是否安全失败？** 是，已通过本地验收。
16. **是否只读取 Published Snapshot？** 是，已通过本地验收。
17. **是否停止使用旧 Product JSON？** 是，已通过本地验收。
18. **是否停止使用旧 Batch JSON？** 是，已通过本地验收。
19. **Product 信息是否正确显示？** 是，已通过本地验收。
20. **Batch 信息是否正确显示？** 是，已通过本地验收。
21. **Process 是否正确显示？** 是，已通过本地验收。
22. **Inspection 是否动态渲染？** 是，已通过本地验收。
23. **Custom text 是否支持？** 是，已通过本地验收。
24. **key_value 是否支持？** 是，已通过本地验收。
25. **table 是否支持？** 是，已通过本地验收。
26. **asset_gallery 是否支持？** 是，已通过本地验收。
27. **是否仅加载 Published Asset？** 是，已通过本地验收。
28. **是否不存在后台 Media URL？** 是，已通过本地验收。
29. **是否使用 lazy loading？** 是，已通过本地验收。
30. **是否避免严重 CLS？** 稳定 aspect-ratio 容器及 width/height；未进行实验室 CLS 压测。
31. **是否支持 EN？** 是，已通过本地验收。
32. **是否支持 ZH-CN？** 是，已通过本地验收。
33. **是否支持 ES？** 是，已通过本地验收。
34. **是否支持 AR？** 是，已通过本地验收。
35. **是否支持 FR？** 是，已通过本地验收。
36. **是否支持 DE？** 是，已通过本地验收。
37. **Arabic 是否 RTL？** 是，已通过本地验收。
38. **Translation fallback 是否正常？** 是，已通过本地验收。
39. **Working Preview 是否与 Published 分离？** 是；认证 API 读取已保存、符合公开构建条件的 Draft，未就绪返回 422。
40. **Review Preview 是否与 Published 分离？** 是；按指定 review_id 读取并验 Hash 的冻结 Candidate。
41. **Published Preview 是否读取真实 Release？** 是，已通过本地验收。
42. **三种 Preview 是否内容隔离？** 是；Editor Working 20kg、Reviewer Review 22kg、匿名 Published 25kg。
43. **Working Preview 是否禁止匿名？** 是，已通过本地验收。
44. **Stable QR Target 是否生成？** 是，已通过本地验收。
45. **QR Target 是否不含 Version？** 是，已通过本地验收。
46. **QR Target 是否不含 DB ID？** 是，已通过本地验收。
47. **Base URL 是否可配置？** 是；VUE_APP_PUBLIC_BASE_URL 与 VUE_APP_PUBLIC_MODE。
48. **是否没有硬编码正式域名？** 是，没有硬编码正式域名。
49. **是否没有把 localhost 当正式 URL？** 是，local 模式明确标记测试；production 拒绝 localhost/loopback 和 HTTP。
50. **不存在 Batch 是否 404/安全错误？** 是，已通过本地验收。
51. **不存在 Version 是否安全错误？** 是，已通过本地验收。
52. **损坏 JSON 是否不白屏？** 是，已通过本地验收。
53. **Missing Asset 是否安全处理？** 是，已通过本地验收。
54. **Client XSS 是否不执行？** 是，已通过本地验收。
55. **危险 Asset URL 是否拒绝？** 是，已通过本地验收。
56. **Path Traversal 是否阻止？** 是，已通过本地验收。
57. **匿名 Published 是否正常？** 是，已通过本地验收。
58. **Network 是否不请求 Admin API？** 是，已通过本地验收。
59. **Network 是否不带 JWT？** 是，已通过本地验收。
60. **Backend 停止后 Stable URL 是否正常？** 是，已通过本地验收。
61. **Backend 停止后历史 URL 是否正常？** 是，已通过本地验收。
62. **SQLite 不可访问是否仍正常？** 是；后台/UI 停止且配置 SQLite 路径不存在时真实浏览器通过。
63. **V1→V2 Stable URL 是否更新？** 是，已通过本地验收。
64. **V1 历史 URL 是否仍 V1？** 是，已通过本地验收。
65. **Rollback Current 是否正确？** 是，已通过本地验收。
66. **TEST RECORD 是否明显显示？** 是，已通过本地验收。
67. **移动端 375 是否通过？** 是，已通过本地验收。
68. **390 是否通过？** 是，已通过本地验收。
69. **430 是否通过？** 是，已通过本地验收。
70. **Desktop 1280 是否通过？** 是，已通过本地验收。
71. **是否真实使用本地 Nginx 验收？** 是，项目目录内编译的 Nginx 1.30.4，仅 127.0.0.1:19540。
72. **Fresh DB→Review→Publish→Public 是否通过？** 是，独立空库经 16 次迁移，真实产品/版本/批次/审核/发布/匿名页面链通过。
73. **Rollback Fixture 是否通过？** 是，已通过本地验收。
74. **是否无未捕获 JS Error？** 是，已通过本地验收。
75. **Public 页面是否保持轻量？** 是，公开端 Vanilla JS，无管理端框架 bundle。
76. **HTML/CSS/JS 体积是多少？** HTML 1417 B；CSS 5632 B；JS 合计 35159 B（含内嵌 Schema）。
77. **Public JSON 测试体积是多少？** Current V3 JSON 8189 B；测试 PNG 80 B。
78. **是否制定 immutable asset cache 策略？** 是，版本 JSON 和内容寻址 PNG：max-age=31536000, immutable。
79. **是否制定 current cache 策略？** 是，Current、HTML 与未指纹化脚本样式：no-cache, max-age=0, must-revalidate。
80. **是否明确 robots/indexing 策略？** 是，robots Disallow /、meta/X-Robots-Tag noindex,nofollow；不作为访问控制。
81. **是否有基础 CSP/security header 方案？** 是，CSP self-only / frame-ancestors none、nosniff、no-referrer。
82. **是否加载第三方 JS/CDN？** 否，不加载第三方 JS/CDN、字体、追踪或外部图片。
83. **是否修改 DATA_MODEL？** 否，业务 DATA_MODEL 不变。
84. **是否需要新 Migration？** 是，新增 1789344000000_private_preview.go，仅授权菜单/API。
85. **是否修改 T4-T10 历史 Migration？** 否，历史迁移 Hash 全部不变。
86. **是否更新 TASKS？** 是，已通过本地验收。
87. **是否新增 T11 文档？** 是，已通过本地验收。
88. **原 53 个 T0 基线文件证据是否保留？** 是，已通过本地验收。
89. **原 site 7 文件是否保留或有明确迁移记录？** 是，已通过本地验收。
90. **是否连接业务服务器？** 否。
91. **是否修改 Caddy？** 否。
92. **是否修改 Directus？** 否。
93. **是否修改生产 Docker？** 否。
94. **是否生成生产正式 QR PNG/SVG？** 否。
95. **是否进入 T12？** 否，T12 未开始。

T11 公开端、预览与稳定 QR URL 已完成，当前已停止，等待人工验收，未进入 T12。
