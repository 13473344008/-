# Product Digital Identity · 本地测试模板

本项目使用 HTML、CSS、原生 JavaScript 和静态 JSON 展示产品身份与批次追溯信息。第一款模板为 PF-STD / Potato Flakes / 马铃薯雪花片，测试批次为 PF-TEST-001。无前端框架、数据库、区块链、Directus API 或应用后端；Python HTTP 服务仅供本地读取静态文件。

**当前仅为测试阶段，不可用于商业证明。** 页面始终显示 `TEST RECORD — NOT FOR COMMERCIAL USE`，并保留 `noindex,nofollow`。这些标识不构成访问控制。没有真实 COA、证书编号、日期、厂家或产地信息时留空；不根据品牌或域名推断厂家。Moisture 仅用于展示字段结构，结果为空、状态 NOT_TESTED；认证名称只是未验证的模板条目。

## 本轮目录

```text
ID/
├── README.md
├── LOCAL_REPORT.md
├── site/
│   ├── index.html
│   ├── css/style.css
│   ├── js/app.js
│   ├── products/PF-STD.json
│   ├── batches/PF-TEST-001.json
│   ├── schemas/
│   │   ├── product.schema.json
│   │   └── batch.schema.json
│   └── assets/                         # 当前为空
├── tests/
│   ├── browser.cjs
│   └── schema.py
└── .qa/product-id/
    ├── browser-results.json
    ├── schema-results.json
    ├── 320.png
    ├── 390.png
    ├── 768.png
    └── 1440.png
```

已有 AGENTS.md、outputs/、work/、其他 .qa 文件、update_domain.py 及 Word 文档保留，未修改。本轮开始时不存在 site/ 或 README.md，因此不存在需要覆盖备份的旧源码。将来修改已有部署前必须另行备份，不得把本地新建误称为服务器备份。

## Product 字段

Product 保存长期固定信息，文件名必须等于 `identity.product_code + '.json'`。

| 分组 | 字段与含义 |
| --- | --- |
| identity | product_code 产品编码；product_name 英文名；product_name_zh 中文名；category 类别；country_of_origin 产品原产国；manufacturer 制造商名称（字符串）；product_image 产品图片路径 |
| description | short_description 简介 |
| raw_material | name 原料名；type 类型；origin 常规来源描述；description 原料说明 |
| manufacturing_process | 有序字符串数组，保存标准参考工艺，不是批次生产日志 |
| packaging | package_size 包装规格；package_type 包装类型；inner_material 内包材；storage_conditions 储存条件；shelf_life 保质期说明（字符串） |
| certifications | 数组，每项 name、certificate_number、valid_from、valid_until、status、image |

PF-STD 的顺序为 Raw Potato Receiving → Washing → Peeling → Cooking → Mashing → Drum Drying → Flaking → Inspection → Packaging，即包含蒸煮、制泥、滚筒干燥。顺序由样例数据回归检查；通用 Product Schema 不把其他产品锁定成马铃薯工艺。

认证状态：UNVERIFIED / VALID / EXPIRED / SUSPENDED。当前两项为 UNVERIFIED，不表示持有证书，也不自动根据日期推导有效性。

## Batch 字段

依照最新需求，批次身份字段置于顶层，不再包在 identity 内。Batch 仅引用 product_code，不复制产品名、包装或工艺。

| 字段 | 含义 |
| --- | --- |
| record_type | test 或 commercial；本轮只创建 test |
| product_code | 关联 Product 编码 |
| batch | 批次编码，与文件名一致 |
| production_date / expiry_date | 生产日期 / 到期日期 |
| status | TEST / PENDING / RELEASED / HOLD / REJECTED；测试样例为 TEST |
| record_updated | 记录更新日期；本版本采用日期而非时间戳 |
| raw_material_traceability | raw_material_batch 原料批次；raw_material_origin 本批次实际原料来源 |
| inspection | 数组，每项 name 项目名、specification 标准、result 结果、unit 单位、status 检测状态 |

检测状态：NOT_TESTED / PENDING / PASS / FAIL。检测结果与规格采用字符串，以支持不等式等表达。空字符串表示未提供，绝不代表零或合格。页面显示 `—`。record_updated 不填写本地开发时间，避免将其误认为真实批次更新日期。

## Schema 规则

使用 JSON Schema Draft 2020-12。字段名称及分组固定为 snake_case，各层 `additionalProperties: false`，规范要求完整结构，可将未知字符串值写为 `""`，未知数组写为 `[]`，不使用 null。日期为 `YYYY-MM-DD` 或空字符串；校验器必须启用 format 检查，才能检查真实日历日期。产品名称不可为空。

编码仅接受 A-Z、a-z、0-9、短横线和下划线。test 批次编码还必须包含以短横线/下划线分隔的 TEST 段，批次状态必须是 TEST。Schema 支持 future commercial 字段值不等于允许本轮创建真实批次。

Schema 校验用于数据维护；网页不加载校验框架。网页仅检查必要身份、关联关系和安全路径；缺失非关键字段仍能显示。通过 Schema 不能证明数据真实、证书有效或日期先后合理；将来正式数据上线需人工核验这些业务关系。Schema 不替代真实 COA 或商业审核。

## 新增产品与批次

1. 复制 Product 样例到 `site/products/<product_code>.json`，同步修改 identity.product_code；填写已有证据的固定信息，未知字段留空。
2. 图片只使用 `site/assets/` 中可公开的 PNG/JPG/JPEG/WebP/GIF；JSON 写 `/assets/name.png` 或 `assets/name.png`。文件名及子目录只用字母、数字、短横线、下划线。不接受远程图片、SVG、路径穿越或脚本协议。
3. 复制 Batch 样例到 `site/batches/<batch>.json`，同步修改 batch，引用已存在的 product_code。本阶段只使用包含 TEST 段的批次，保持 record_type=test、status=TEST。
4. 不复制固定产品数据进批次。未知检测结果留空、NOT_TESTED，不写虚假 PASS。
5. 用对应 Schema 校验新增文件，并在浏览器逐一打开批次。tests/schema.py 的样例回归目前针对 PF-STD / PF-TEST-001；新增记录应另外调用相同 validator 校验。

## 本地启动

不要使用 file://；仅提供 site/，不要把整个项目目录公开。

本次发现 8088 被既有 SSH 进程占用，未停止、改动或使用该转发。实际验证使用 8089：

```bash
cd /path/to/ID/site
python3 -m http.server 8089 --bind 127.0.0.1
```

正常记录：http://127.0.0.1:8089/?batch=PF-TEST-001

不存在批次：http://127.0.0.1:8089/?batch=ABC-NOT-EXIST

无参数：http://127.0.0.1:8089/

非法参数：http://127.0.0.1:8089/?batch=../../test

如果以后确认 8088 已空闲，可自行以相同命令把端口改为 8088，使用 http://localhost:8088/?batch=PF-TEST-001；不要停止未知进程以抢占端口。

前端预留 `/b/{batch}` 解析，但 Python 默认静态服务器不提供 HTML 路由回退，直接请求该路径会 404。本轮用 query URL 验收。路径解析单测通过浏览器拦截提供 HTML，仅验证前端，不能视为服务端路由已配置。本轮没有更改 Nginx/Caddy 或部署路由。

## 本地测试

浏览器手工检查四个地址及手机视口；检查八个模块、顶部测试标识、五项检测字段、无水平溢出、清晰错误信息。

```bash
cd /path/to/ID
node --check site/js/app.js
```

自动验证仅使用开发工具，不随网页加载：

```bash
python3 -m venv /tmp/pdi-schema-venv
/tmp/pdi-schema-venv/bin/pip install jsonschema==4.26.0
/tmp/pdi-schema-venv/bin/python tests/schema.py
```

浏览器测试需要可用的 Playwright 和 Chromium。本机复现命令（其他机器调整路径）：

```bash
cd /path/to/ID
NODE_PATH=/Users/lostar/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules \
PDI_CHROMIUM='/Users/lostar/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' \
PDI_BASE_URL=http://127.0.0.1:8089 \
node tests/browser.cjs
```

覆盖正常/缺失/非法批次、JSON 解析失败、Product 不存在、网络失败、缺失字段、身份不匹配、HTML 注入、图片安全/缺失、编码路径穿越、长文本、320/390/768/1440px 布局。异常数据通过浏览器请求拦截注入，不添加虚假公开批次文件。测试截图和 JSON 结果在 .qa/product-id/。

## 本轮边界

没有连接服务器、修改服务器文件或部署。没有修改 /opt/proxy、Caddy、Directus、PostgreSQL、DNS、HTTPS、防火墙、Docker 或二维码。页面只提供英文主界面和中文产品名；字段标签和错误文案有集中定义，完整多语言仍待后续开发。仅本地 Chromium 已验证；真实手机 Safari/Firefox 尚未验证。
