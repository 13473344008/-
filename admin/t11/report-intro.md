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
