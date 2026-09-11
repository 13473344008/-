# T0–T14 完整任务地图

日期：2026-09-10。T0–T11 已由用户人工验收通过；T12 原轮次未通过（83/95 Gates）。当前 T12 修复后本地验收95/95 Gates、1144 PASS、0 FAIL，全部本轮服务已停止，等待人工验收。T13/T14 未授权、未进入；服务器及共享组件操作未授权。

| 阶段 | 目标 | 输入 | 操作 | 输出 | 验收标准 | 服务器操作 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T0 项目冻结与现状基线 | 保留静态 POC，建立可核对基线 | 当前工作区、README、既有测试证据 | 只读清点文件/功能/限制，计算哈希；新增 docs | CURRENT_BASELINE.md、BASELINE_SHA256.json | 既有 53 文件哈希与清单一致，含 site 7 文件；区分历史测试与本轮验证 | 禁止 | 已人工验收通过 |
| T1 官方项目核验 | 确定可追溯的官方版本与复用边界 | 官方后端/UI 标签、Release、源码 | 核验维护、License、版本、数据库、Docker、JWT/Casbin、管理模块、上传/生成器；静态契约检查 | GO_ADMIN_EVALUATION.md、UPSTREAM_LOCK.json | 两仓 repository/tag/commit 可复核；17 项核验有证据；明确静态检查范围与运行待验项 | 禁止 | 已人工验收通过，运行联调留 T4 |
| T2 架构和数据库决策 | 决定管理端/公开端分离及独立数据库 | T0/T1、用户新架构约束 | 比较 SQLite/PostgreSQL；设计继承、审核、快照、发布/回滚、安全与隔离 | ARCHITECTURE.md、DATABASE_DECISION.md、TASKS.md | 明确选 SQLite；公开不依赖后台；POC 不改；正式表结构留 T3 | 禁止 | 已人工验收通过 |
| T3 正式数据模型 | 定义混合模型、约束和版本语义 | 获确认 T2、现有 Schema | 设计核心表、关联、模板固定/覆盖语义、可配置字段/模块、审核修订、版本/激活关系及公开字段映射 | DATA_MODEL.md、DATA_MODEL_ERD.md、PUBLISH_MODEL.md、PUBLIC_PAYLOAD_SCHEMA.md | 19 表逐字段/关系/索引/删除；固定模板与批次；冻结快照和资产；V4 回滚；翻译表；公开白名单与测试示例；下方 22 项已人工验收 | 禁止 | 已人工验收通过 |
| T4 基础框架本地启动 | 用锁定官方版本验证真实运行 | T3、上游锁、用户 T4 授权 | 独立 SQLite、官方与业务 Migration、UI 登录、RBAC 重启、冻结/事务/并发/备份恢复 | T4_RUNTIME_VALIDATION.md、SQLITE_VALIDATION.md、T4_TEST_RESULTS.json、admin 技术代码 | 本轮用户定义的 16 Gates；99 项检查 PASS；上传与完整业务数据范围矩阵不在本轮验收结果内 | 禁止 | 已人工验收通过；T4 证据保留 |
| T5 产品模板管理 | 稳定 Product + 不可变 Revision + 翻译 | 已验收 T3/T4、T5 授权 | 独立 T5 SQLite；产品/版本/翻译 API、事务、封版/默认/归档、菜单/UI、审计 | T5_PRODUCT_TEMPLATE.md、T5_TEST_RESULTS.json、产品模块源码 | 26 Gates；自动与浏览器验收、升级/空库/重启/完整性/基线保护 | 禁止 | 已人工验收通过；T5 证据保留 |
| T6 批次身份证管理 | 低操作成本创建批次与覆盖 | 产品模板、批次模型 | 新建批次、继承/覆盖、复制上一批、任意检测项目编辑/排序 | T6_BATCH_MANAGEMENT.md、T6_TEST_RESULTS.json、批次 API/UI 和复制流程 | 40 Gates；固定模板、覆盖三态、动态检测、克隆、事务/权限/并发/浏览器/重启/新库/基线保护 | 禁止 | 已人工验收通过；T6 证据保留 |
| T7 自定义字段/模块 | 非技术人员添加展示内容 | 自定义定义与值模型、T6 表单 | 类型约束、添加/删除/排序、公开控制、文本/键值/表格/资产模块 | T7_CUSTOM_SECTIONS.md、T7_TEST_RESULTS.json、模块 UI/API | 45 Gates；受控四类型、冻结/克隆/继承/隐藏/多语言/事务/权限/浏览器/并发/重启/新库/完整性 | 禁止 | 已人工验收通过；T7 原始证据保留 |
| T8 RBAC 与审核工作流 | 实现四角色与不可绕过的审核 | 上游 Casbin、T3 工作流、T5–T7 | 配角色/菜单/路由权限；固定审核修订；提交/驳回/发布授权；撤权与敏感操作记录 | T8_RBAC_REVIEW_WORKFLOW.md、T8_TEST_RESULTS.json、审核 API/UI | 50 Gates：四角色、冻结输入、不可自审、事务/并发/浏览器/重启/空库/基线 | 禁止 | 已人工验收通过（用户本轮确认） |
| T9 静态发布引擎 | 从已审核工作数据生成安全快照 | Public DTO 契约、固定审核修订、公开资产 | 白名单映射、Schema 校验、不可变资产、同文件系统 staging/rename、幂等和可恢复任务 | T9_PUBLISH_ENGINE.md、T9_TEST_RESULTS.json、静态发布执行器/API/UI | 半写/磁盘满/权限错误不破坏旧版；无内部数据；晚到任务不覆盖新版；文件与 DB 可对账恢复 | 禁止 | 已人工验收通过；T9 原始证据保留 |
| T10 版本/日志/回滚 | 保留历史并安全恢复旧内容 | T9 版本与任务、业务审计 | 发布历史 UI、可靠审计、按历史 Payload 回滚、资产保留/恢复 | 版本查询、回滚流程及故障验收 | v3→v2 生成新 v4，保持 v1/v2/v3 历史且新增回滚记录；不重算最新模板；切换前失败保持旧公开版，切换后失败对账恢复，审计不丢 | 禁止 | 已人工验收通过 |
| T11 公开端/预览/QR URL | 接入完整快照，保留稳定批次 URL | 原 POC、T9 Payload、T10 历史 | 独立 public-site 正式入口；授权私有预览；本地路由、JSON/资源/缓存策略；URL 构造 | 正式静态模板、本地预览与测试 URL | site POC 保留；/b/编码 内容正确；缺失资源真 404；草稿不公开；图片不依赖后台；不制作投产二维码 | 禁止 | 已人工验收通过（用户本轮确认）；历史证据保留 |
| T12 本地端到端验收 | 验证完整编辑到扫码闭环 | T4–T11 | 四角色新建/复制/审核/发布/回滚；并发与中断；停止本项目本地后台/DB；备份恢复；移动端和泄露检查 | 本地 E2E 报告、恢复报告、遗留项清单 | 后台停止已发布页/图片仍正常；模板改动不改历史；越权拒绝；失败旧版可读；恢复一致，全部关键项通过 | 禁止；只操作本项目本地实例 | 修复后95/95 Gates、1144 PASS、0 FAIL；服务全部停止，等待人工验收；原83/95失败报告保留 |
| T13 服务器独立部署 | 在独立项目安全部署，先测试后生产 | 明确服务器授权、T12 通过、实况只读核查 | 先确认生产/测试容器划分、目录/Compose/网络/资源/备份和回退方案；单独部署 passport-admin；受控集成公开产物目录 | 独立服务/数据/日志/备份、实际部署与回归记录 | 不碰 Directus 数据，不进 proxy Compose，无后台公网端口；资源与恢复验证；任何共享层变化先确认；既有站点不回归失败 | 仅另行明确授权后；共享变更逐项确认 | 未开始，当前禁止 |
| T14 Caddy/DNS/HTTPS/正式二维码 | 获批后接入正式入口与扫码地址 | T13 通过、用户明确解除相关暂缓、域名与路由方案 | 最小增量 Caddy 配置备份/校验/确认 reload；按独立批准执行 DNS/HTTPS；测试后正式二维码 | 路由/TLS/域名验证、二维码清单与回退说明 | 保留既有配置/卷/TLS；不重建共享 Caddy；回归全部相关站点；实扫 /b/批次且内容/资源正确 | 仅每项明确确认后；SSL 当前仍暂缓 | 未开始，当前禁止 |

## T3 历史交付记录（已人工验收）

新增 DATA_MODEL.md、DATA_MODEL_ERD.md、PUBLISH_MODEL.md、PUBLIC_PAYLOAD_SCHEMA.md；修改本 TASKS.md。T0–T2 已验收文档原文保留，T3 更具体的回滚方案（新 V4 来源 V2）以本轮设计为准。

T3 当轮只做文档与离线 JSON Schema 检查；未建 SQLite 文件、未执行迁移、未启动后端/UI、未连接业务服务器、未操作 Docker/Caddy/Directus，未修改 site 或既有 53 个基线文件。

### T3 核心验收清单（设计已覆盖，已人工验收）

| # | 验收问题 | 设计依据 |
| --- | --- | --- |
| 1 | 模板是否冻结 | product_revisions sealed + 全部子表冻结触发器设计 |
| 2 | Batch 是否固定基准 | base_product_revision_id 必填、FK、创建后禁止换绑 |
| 3 | 新模板是否不影响旧批次 | products.current 指针仅用于新建，不用于历史读取 |
| 4 | Override 灵活且受控 | 闭合白名单、类型匹配、FK 资产值、状态校验 |
| 5 | 继承/覆盖能否区分 | 无行 / set / clear；删除覆盖恢复继承 |
| 6 | 检测新增是否不改 Schema | inspection_items 逐行；仍有容量/安全上限，不承诺物理无限 |
| 7 | 认证更新是否不改历史 | 固定认证版本 + 公开附件独立冻结 |
| 8 | 模块新增是否不改 Schema | 四种受控模块类型可新增实例；新渲染类型可能需开发 |
| 9 | 多语言是否单套主数据 | Translation Tables + 每实体/语言唯一 |
| 10 | Passport Revision 是否不可变 | sealed 后内容冻结，正式 published 后全部不可改 |
| 11 | Published JSON 是否不可变 | versions/vN 原文/Hash 固定；仅稳定入口替换 |
| 12 | Published Assets 是否冻结 | 内容寻址独立副本 + 不可变版本清单 |
| 13 | 回滚是否保留全部历史 | 新 V4 来源 V2，保留 V1–V3 与操作记录 |
| 14 | Public DTO 是否独立 ORM | typed Public Builder 显式映射 |
| 15 | 是否有公开白名单 | 嵌套 JSON Schema 禁未知属性 + 审核公开意图 |
| 16 | 是否有 schema_version | 1.0 契约与后续版本分派策略 |
| 17 | Record 是否记录完整发布 | 唯一幂等操作、进度、关联版本、失败与恢复 |
| 18 | Audit 是否区别系统日志 | 追加式业务事件，和业务变更同事务 |
| 19 | 删除是否保护历史 | RESTRICT/Archive/墓碑，公开资产不级联删除 |
| 20 | SQLite→PostgreSQL 是否可迁移 | UUID/类型/FK/枚举映射；触发器需改写，Payload 原文保留 |
| 21 | Clone Batch 是否可实现 | 新主/子 ID，固定基准，重置检测/日期/审批/发布 |
| 22 | 稳定 QR URL 是否可实现 | /b/批次读取完整稳定 JSON，不查后台数据库 |

本轮离线检查：文档内 JSON Schema/完整 PF-TEST-001 样例及泄露字段、非法日期、结果/判定冲突、路径和语言等反例共 25 项通过；19 张表均有字段字典和 ERD 节点，文档链接与代码围栏检查通过。复核原 53 文件 SHA-256 全部一致。未运行数据库、Migration、触发器或发布故障测试。

以上为 T3 的设计验收记录。用户后续已确认 T3 通过，并单独授权 T4；T4 的真实运行结果以 T4_RUNTIME_VALIDATION.md 为准。

## T4 历史交付记录（后续已人工验收）

16 Gates 全部 PASS，99 项检查 PASS，最终 FAIL 0；T4 等待人工验收，不标记最终完成。新增两份验证报告及机器可读结果，补充 DATA_MODEL.md 的最小实现校准。两个本地服务已停止，site 及原 53 文件 Hash 不变，未操作业务服务器或生产共享组件。只有用户明确验收 T4 并放行后才允许进入 T5。

## T5 交付与停止点

产品模板、版本/翻译、封版/复制/默认/归档与业务审计已经本地验证。26 Gates 全部通过；运行服务已停止，T5 等待人工验收。T6 保持未开始；没有 Batch CRUD、Passport Publish Engine 或服务器操作。T4 原始证据及迁移保留，详细检查计数以 T5_TEST_RESULTS.json 为准。


## T6 停止状态

T5 已由用户人工验收通过。T6 本地开发与验收完成，40/40 Gates、239 个业务断言通过，当前等待人工验收；本轮本地服务已停止。T7/T8/T9 均未开始，未连接服务器或部署。详见 T6_BATCH_MANAGEMENT.md 与 T6_TEST_RESULTS.json。


## T7 本轮交付

T6 已人工验收通过。T7：45/45 Gates，385 项最终业务断言 PASS，0 FAIL；另 UI 301 单元测试 PASS。本轮所有本地服务已停止，等待人工验收。未进入 T8/T9，未操作服务器。详见 T7_CUSTOM_SECTIONS.md、T7_TEST_RESULTS.json。


## T8 本轮交付与停止点

T7 已由用户人工验收通过，历史报告保留交付时状态不重写。T8 已实现四角色和组合权限、冻结审核候选、Submit/Reject/Approve/Return、完整审核历史及事务审计；验收结果见 T8_RBAC_REVIEW_WORKFLOW.md、T8_TEST_RESULTS.json。T8 等待人工验收，本地服务已停止。T9 未开始，未创建公开快照或冻结正式资产，未连接业务服务器。


## T9 当前交付（2026-09-10）

用户已明确验收 T8，历史阶段交付记录保留原时点表述。T9 完成 Approved Candidate→白名单 JSON→规范化冻结资产→封版→原子 Current→数据库确认，具备幂等、每批次锁、失败重试及待对账恢复。本地 API/浏览器、全新 DB、升级/重复迁移、故障、并发、停后台静态访问及基线复验见 T9_PUBLISH_ENGINE.md / T9_TEST_RESULTS.json。T9 等待人工验收；所有本地测试服务已停止。未进入 T10/T11，未连接业务服务器。


## T10 当前交付（2026-09-10）

用户已人工验收 T0–T9；此前各阶段报告保留当时交付状态。T10 增加完整版本/审核/发布尝试历史、业务审计时间线、不可变快照比较、历史完整性检查、Rollback as New Version 和带原因的安全对账管理。65/65 Gates 本地通过；测试明细、源码变化、风险与 93 项逐条回答见 T10_VERSION_AUDIT_ROLLBACK.md / T10_TEST_RESULTS.json。所有 T10 本地服务已停止，等待人工验收；T11/T12 未开始。未改 site、未生成 QR、未连接服务器或部署。

## T11 本轮交付与停止点

T10 已人工验收通过。T11 正式 public-site、三种预览与稳定 QR URL 完成本地验收，75/75 Gates PASS；详细计数、95 项答复与限制见 T11_PUBLIC_SITE_QR_URL.md / T11_TEST_RESULTS.json。真实 Nginx 在后台、UI 停止且配置 SQLite 文件不可访问时仍提供稳定页、历史页和图片。所有本轮服务现已停止。T12 未开始；未连接服务器、未部署、未改共享组件，未生成生产二维码。


## T12 本轮停止点（2026-09-10）

T0–T11 已人工验收。新建独立T12环境，通过空库16迁移、产品/R1/R2、无图片审核发布V1/V2、新V3回滚、并发、对账、JSON损坏阻断、DB/静态备份恢复及无图页面停后台访问。最终83/95 Gates，638项断言/叶测试PASS、3 FAIL；未达到用户要求的95/95。

确认缺口：无正式MediaAsset/AssetLink业务输入入口；已发布主批次Clone被现有Draft规则拒绝。没有使用SQL图片夹具绕过；V2只用了用户第42节明确许可的本地Candidate Fixture。未新增业务能力、未改历史迁移；不能将已有T9/T11图片fixture结果冒充本轮从零业务闭环。

详见[T12_END_TO_END_ACCEPTANCE.md](T12_END_TO_END_ACCEPTANCE.md)与[T12_TEST_RESULTS.json](T12_TEST_RESULTS.json)。[T13_DEPLOYMENT_PRECHECK.md](T13_DEPLOYMENT_PRECHECK.md)仅设计清单，未执行部署。所有本轮服务已停止；T13/T14仍未授权、未进入。


## T12 修复回合停止点（2026-09-10）

正式PNG/JPEG媒体上传/关联、Published来源Clone及API契约修复完成。独立T12-fix新库17迁移，真实Editor图片上传—审核发布—V2图片差异—新V3回滚通过；普通Publish八阶段故障与真实SQLite失败/浏览器Reconcile、图片/JSON/Manifest损坏阻断、完整备份恢复及停后台/DB离线公开图片访问通过。95/95 Gates，1144 PASS、0 FAIL。原53文件基线、site7文件、31854历史受保护文件及原T12失败报告未变。全部本轮服务停止；等待人工验收，不表示已由用户验收。

详见[T12_REMEDIATION.md](T12_REMEDIATION.md)和[T12_REMEDIATION_TEST_RESULTS.json](T12_REMEDIATION_TEST_RESULTS.json)。原第一次83/95、638 PASS/3 FAIL完整保留。没有进入T13/T14，没有连接服务器或修改共享组件。


## 2026-09-11 人工反馈增量：访问与日志

用户指出首页销售/支付/运营示例不适用，要求二维码访问地区/时间/批次及后台登录/操作日志；明确不记录扫码客户身份。已在独立人工副本实现真实静态日志统计、离线地区、日志入口与地区列；309 UI单测及专项服务/API/浏览器检查通过。待人工复验，未把原95/95历史报告改成当前增量已经总验收。详见[T12_MANUAL_FEEDBACK_TRAFFIC.md](T12_MANUAL_FEEDBACK_TRAFFIC.md)。T13/T14未进入；人工副本继续运行。

### 2026-09-11 · 人工反馈修复与生产部署准备

用户已授权修复问题并进行生产准备。已增加测试批次编码的前后端提前校验、历史审核发布保护、生产构建标签修正和独立部署候选。最新结果见 `docs/PRODUCTION_PREPARATION.md`，部署说明见 `deploy/production/README.md`。本轮没有执行服务器部署或修改共享 Caddy/Directus/DNS/HTTPS；目标 Docker 与容器验收、现场检查及共享入口授权仍为上线门禁。原有 T12 报告保留其历史语义。
