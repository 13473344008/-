# T3 正式数据模型（设计稿）

> 当前 T10（2026-09-10）：T0–T9 已人工验收；版本、审计与回滚已本地实现并等待人工验收，详见本文末节及 T10_VERSION_AUDIT_ROLLBACK.md。下方早期阶段文字保留历史语境。

> 2026-09-09 T8 校准：T0–T7 已人工验收；T8 已实现独立审核记录，等待人工验收。下文 T3 的初始状态文字仅为历史记录。当前实现增加 `review_records` 和 `batches.current_review_record_id`，详见本文末节及 T8 报告；发布引擎仍未实现。

状态：**等待人工验收**。范围仅 T3 文档设计，未创建数据库、未执行 Migration、未启动 Backend/UI，未进入 T4。技术基线沿用已验收 T0–T2：Go Admin v2.6.0、UI v3.2.0、独立 SQLite。本文的约束均为待实现设计，不能当作现有数据库已生效的保护。

本轮细化优先于 T2 的开放建议：回滚必须形成新 Passport Revision（V4 来源 V2），不只新增激活记录。`passport_revisions` 是 T2 `passport_versions` 的正式表名；`passport_audit_events` 是 T2 业务 `audit_logs` 的正式名称，不再重复建同义表。

## 1. 设计取舍与类型字典

最终 ID 策略：新业务表统一 **UUIDv4**，SQLite `TEXT NOT NULL PRIMARY KEY`，应用创建 UUID；未来 PostgreSQL 可映射 UUID。Go Admin 原 sys_user 等系统表保留其整数主键，业务 actor FK 沿用它，绝不重做身份系统。产品/批次码为独立唯一业务键，不当 PK，不作为敏感数据授权凭据。

| 候选 | 取舍 |
| --- | --- |
| 自增整数 | SQLite 简单、索引较小，但离线导入/跨环境合并要重映射；公开也无必要暴露 |
| UUIDv4（选定） | 不依赖数据库 sequence，SQLite/PostgreSQL 清晰映射；UUID 唯一约束仍必须存在，不以“随机”替代约束 |
| ULID | 可排序，但增加编码/时间语义约束；本项目已有时间字段，无需额外库与约定 |
| 混合 | 仅保留上游系统整数 ID + 新业务 UUID，避免侵入 Go Admin |

表中每行定义一个真实列。通用列已逐表展开。默认“无”表示 INSERT 必须显式给值，不代表 NULL；“应用”表示应用赋值，不是数据库函数默认值。所有未另述 FK 均 ON UPDATE RESTRICT、ON DELETE RESTRICT。除已被组合索引左前缀覆盖的外键外，每个 FK 列显式建普通索引（SQLite 不自动给子外键建索引）；多态 audit.entity_id 按其表内组合索引处理。表内 `published_by` 等属于私有元数据，不能因名字相似映射到公开 publication。

| 逻辑类型 | SQLite → PostgreSQL | 校验 |
| --- | --- | --- |
| ID | TEXT → UUID | 规范小写 UUIDv4；NOT NULL PK，不能依赖 SQLite 非整数 PK 的隐式非空行为 |
| USER | INTEGER → 与 sys_user.user_id 一致的整数 | 真实上游用户 FK；应用以受认证主体填入 |
| CODE | TEXT → VARCHAR(64) | 1–64 位 ASCII `[A-Za-z0-9_-]`；product_code/batch_code 应用规范为大写后唯一比较；其他受控键区分大小写并采用各字段注册的固定形式，保留 PF-STD/PF-TEST-001，不按大小写制造重复 |
| INT | INTEGER → BIGINT（必要时 INT） | 非负计数/排序、正版本号；Go int64；公开数字限制为安全整数 |
| BOOL | INTEGER CHECK IN(0,1) → BOOLEAN | Go bool；业务不依赖 0/1 算术 |
| DECIMAL | TEXT → NUMERIC 或保留 TEXT | 十进制字符串，最多 18 整数位+9 小数位，不允许指数/NaN/Infinity；用精确十进制比较，不使用 REAL |
| UTC | TEXT → TIMESTAMPTZ | 固定 RFC3339 UTC 毫秒 `YYYY-MM-DDTHH:mm:ss.SSSZ`，同事务统一时间；前端按时区显示 |
| DATE | TEXT → DATE | 真实日历 YYYY-MM-DD；生产/检测/有效期是日期，不作时区转换 |
| TEXT(n) | TEXT → VARCHAR(n)/TEXT | SQLite 不靠 VARCHAR 长度约束，CHECK length + 应用校验；n 为字符数 |
| JSON | TEXT → JSONB（可选） | 受控对象/数组，应用严格解析且拒绝重复 key，DB JSON-valid CHECK 在 T4 核验函数可用性；不是任意 ORM dump |
| HASH | TEXT → CHAR(64) | 小写 64 位十六进制 SHA-256；算法约定固定 |
| PATH | TEXT → TEXT | 相对命名根的 POSIX 路径；拒绝绝对路径、反斜线、..、URL/query/fragment、编码穿越 |
| LANG / ENUM | TEXT → TEXT+CHECK | 不用 PG 原生 enum，便于受控扩展；LANG=en/zh-CN/es/ar/fr/de |

NULL 表示未提供；清空语义由 override.operation=clear 表示，不把空字符串、NULL、继承混同。数组空 [] 是明确没有条目。所有组合唯一索引的可空 owner 必须使用明确部分索引，不能依赖 NULL 的唯一性行为。

## 2. 表目录与字段

共 **19 张业务表**，另复用现有 Go Admin 系统用户/角色/权限表。必需的 14 实体全部保留；新增 5 表为三种额外翻译表、certification_links、asset_links，各自必要性在表说明中列出。没有新增数据库、动态 SQL 字段表、独立语言数据库、队列数据库或第二套用户表。

### 2.1 `products`

稳定产品身份；产品名称由选定 revision 的翻译提供，不能把可变产品主表名称当作历史展示来源。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_code | CODE | 否 | 无 | 全库 UNIQUE；创建后不可改，不重用已归档编码 |
| lifecycle_status | ENUM | 否 | active | active / disabled / archived；控制新建批次可选性 |
| current_revision_id | ID | 是 | NULL | 当前默认可用模板 FK product_revisions.id，RESTRICT；须属于本产品且 sealed |
| archived_at | UTC | 是 | NULL | 仅 archived 时填写 |

约束、索引与删除：UNIQUE(product_code)、UNIQUE(id,product_code)；INDEX(lifecycle_status,updated_at)。current_revision_id 用 (id,current_revision_id) → product_revisions(product_id,id) 组合 FK 保证同产品；插产品时先 NULL，封版后更新。无级联删除；存在任何 revision 即 RESTRICT。归档只禁止新增，不改变历史与公开内容。

### 2.2 `product_revisions`

可封存模板；一个产品多个有序修订。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_id | ID | 否 | 无 | FK products.id，RESTRICT |
| revision_number | INT | 否 | 事务内分配 | 产品内递增正整数，允许失败/弃用留空号，不复用 |
| revision_status | ENUM | 否 | draft | draft / sealed / abandoned；sealed 永久不可改 |
| source_revision_id | ID | 是 | NULL | 复制来源，同产品 product_revisions.id，RESTRICT |
| source_language | LANG | 否 | en | 源语言；封版必须有该语言 approved 翻译 |
| category_code | CODE | 是 | NULL | 结构化分类，不承担翻译 |
| origin_country_code | TEXT(2) | 是 | NULL | 明确资料才填国家代码，不按品牌推断 |
| package_quantity | DECIMAL | 是 | NULL | 默认净含量十进制字符串，非二进制浮点 |
| package_unit | TEXT(32) | 是 | NULL | kg/g 等技术单位 |
| package_type_code | CODE | 是 | NULL | bag/carton 等受控包装类型 |
| shelf_life_days | INT | 是 | NULL | 已知才填，非负；批次有效期不自动随之重算 |
| process_steps | JSON | 否 | [] | 仅有序 {step_key} 列表；唯一 step_key，无任意对象字段 |
| sealed_at | UTC | 是 | NULL | sealed 时必填，之后不变 |
| sealed_by | USER | 是 | NULL | 封版人 FK sys_user.user_id，RESTRICT |
| content_hash | HASH | 是 | NULL | sealed 时对模板与全部子表规范化内容计算，之后不变 |
| internal_note | TEXT(2000) | 是 | NULL | 私有备注，封版后也不改；后续说明写审计 |

约束、索引与删除：UNIQUE(product_id,revision_number)、UNIQUE(product_id,id)；source 同产品且 revision_number 严格更小，禁止自引用；INDEX(product_id,revision_status,revision_number)。source_revision_id 同产品检查；revision_number>0。draft→sealed/abandoned 单向；只有 draft 可修改/物理删除（且无引用）。sealed 行及翻译、section、关联资产/认证全部禁止 INSERT/UPDATE/DELETE；sealed 不转 archived，停用通过 products 或新建修订选择控制。任何 Batch 只能引用 sealed revision；FK 防删除，触发器阻止修改及换绑，不仅依赖 GORM hook。

### 2.3 `product_revision_translations`

每个模板的本地化文字，源语言也在本表保存一次。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_revision_id | ID | 否 | 无 | FK product_revisions.id，RESTRICT |
| language_code | LANG | 否 | 无 | en / zh-CN / es / ar / fr / de |
| translation_status | ENUM | 否 | draft | draft / approved；仅 approved 可进入提交审核的公开候选 |
| product_name | TEXT(200) | 否 | 无 | 可翻译公开候选文字；仍经 Public Builder |
| short_description | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| raw_material_name | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| raw_material_type | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| raw_material_origin | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| raw_material_description | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| package_description | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| inner_material | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| storage_conditions | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| shelf_life_description | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| manufacturer_name | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| manufacturer_address | TEXT(4000) | 是 | NULL | 可翻译公开候选文字；仍经 Public Builder |
| process_labels | JSON | 否 | {} | 仅 process_steps 已声明 step_key → 非空文字；每语言可缺失并回退 |

约束、索引与删除：UNIQUE(product_revision_id,language_code)；INDEX(language_code,translation_status)。源语言 product_name 非空；process_labels 不允许未知 step_key。继承父模板冻结；sealed 后新增翻译也必须走新 product revision，不补写历史翻译。字段级回退只用已 approved 源语言，不能回退到最新模板。

### 2.4 `batches`

稳定批次身份 + 唯一当前工作集/审核状态；已公开版本独立保存。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| batch_code | CODE | 否 | 无 | 全库 UNIQUE；创建后固定，作为 /b/ 路由业务键，不是 PK |
| product_id | ID | 否 | 无 | FK products.id，RESTRICT；配合 base FK 防跨产品 |
| base_product_revision_id | ID | 否 | 无 | 创建时固定；FK product_revisions.id，RESTRICT，只能 sealed |
| record_type | ENUM | 否 | test | test / commercial；创建后固定；测试不转商业，另建 |
| production_date | DATE | 是 | NULL | 实际生产日，未知为空 |
| expiry_date | DATE | 是 | NULL | 实际到期日；非空时不得早于生产日 |
| quality_status | ENUM | 否 | pending | pending / released / hold / rejected；与工作流和单项检测不同 |
| workflow_status | ENUM | 否 | draft | draft / pending_review / published / archived；工作集唯一工作流状态 |
| edit_version | INT | 否 | 1 | 工作聚合修订号；任意工作子表内容变化同事务递增 |
| submitted_edit_version | INT | 是 | NULL | 提交时捕获的 edit_version |
| submitted_content_hash | HASH | 是 | NULL | 固定审核候选的完整工作语义摘要 |
| submitted_input | JSON | 是 | NULL | 本次提交的私有规范化审核输入；包含继承结果、批准候选语言、资产哈希及处理配方，不引用可变最新对象 |
| submitted_schema_version | TEXT(16) | 是 | NULL | 本次预览/审核契约版本 |
| submitted_builder_version | TEXT(64) | 是 | NULL | 本次确定性 Builder 与资产处理版本 |
| submitted_preview_hash | HASH | 是 | NULL | 审核看到的有效公开业务内容 Hash（不含 publication 信封） |
| submitted_at | UTC | 是 | NULL | 本次提交时间 |
| submitted_by | USER | 是 | NULL | 本次提交人 FK sys_user.user_id，RESTRICT |
| reviewed_at | UTC | 是 | NULL | 本次审核决定时间 |
| reviewed_by | USER | 是 | NULL | 本次审核人 FK sys_user.user_id，RESTRICT |
| rejection_reason | TEXT(2000) | 是 | NULL | 最近驳回理由，只在私有后台；历史转审计 |
| current_passport_revision_id | ID | 是 | NULL | 确认已激活公开头；同 batch FK passport_revisions.id，RESTRICT |
| active_publish_record_id | ID | 是 | NULL | 当前唯一未决发布操作；同 batch FK publish_records.id，RESTRICT |
| next_version_number | INT | 否 | 1 | 版本分配器；单事务增加，失败版本不复用 |
| cloned_from_batch_id | ID | 是 | NULL | 复制来源 FK batches.id，RESTRICT，不等于继承源 |
| archived_at | UTC | 是 | NULL | 归档时间；旧公开内容默认保留 |
| archived_by | USER | 是 | NULL | FK sys_user.user_id，RESTRICT |
| internal_note | TEXT(4000) | 是 | NULL | 私有批次工作备注 |

约束、索引与删除：UNIQUE(batch_code)、UNIQUE(id,product_id)、UNIQUE(id,base_product_revision_id)；组合 FK(product_id,base_product_revision_id)→product_revisions(product_id,id)。current/active 指针分别用 (id,指针)→目标表(batch_id,id) FK，目标列 UNIQUE；初始 NULL 避免插入循环。INDEX(product_id,created_at)、(workflow_status,submitted_at)、(quality_status,updated_at)、(current_passport_revision_id)、(base_product_revision_id)。identity/base/record_type 创建后不可 UPDATE；选错则废弃草稿另建或 Clone，禁止偷偷 rebase。workflow=published 要求 current 非空，draft/pending_review 可仍有历史 current；已公开后编辑须显式 published→draft，不清空公开头。active 非空时禁止编辑/驳回/归档/再次操作；恢复对账结束才解锁。

### 2.5 `batch_overrides`

只存被主动改变的白名单字段；无记录表示继承。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| batch_id | ID | 否 | 无 | FK batches.id，RESTRICT |
| field_key | ENUM | 否 | 无 | 闭合白名单，见本文覆盖矩阵 |
| value_kind | ENUM | 否 | 无 | text / decimal / integer / json / asset；必须与 field_key 注册类型匹配 |
| operation | ENUM | 否 | set | set / clear；clear 为主动清空而非继承 |
| value_text | TEXT(4000) | 是 | NULL | 文本字段源语言覆盖，或十进制字符串；与 kind 一致 |
| value_integer | INT | 是 | NULL | 整数覆盖 |
| value_json | JSON | 是 | NULL | 仅 process 的受控 step_key/label 数组，不接受任意对象 |
| value_media_asset_id | ID | 是 | NULL | 仅 product_image_asset；FK media_assets.id，RESTRICT |
| public_asset_label | TEXT(200) | 是 | NULL | 仅图片 set 时必填的公开标签，不用原文件名 |
| source_language | LANG | 否 | en | 与 base 产品源语言一致 |

约束、索引与删除：UNIQUE(batch_id,field_key)。CHECK 白名单、kind 匹配；set 仅对应一个值列（含 value_media_asset_id）非空；asset 类型还须 public_asset_label，clear 所有值列 NULL。文本类其他语言存翻译表；clear 禁止翻译子行。父 Batch 仅 draft 可更改。取消覆盖删除该行及其翻译（先显式删除子行，FK RESTRICT），恢复绑定模板对应字段，不复制默认值。旧/新值在业务审计差异保存，不再在本表冗余 old_value。

### 2.6 `batch_override_translations`

附加表：一个覆盖可有多种语言；不能把六套文字塞通用 value_json，否则覆盖校验及唯一约束失去清晰边界。关系仅依附 batch_overrides。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| batch_override_id | ID | 否 | 无 | FK batch_overrides.id，RESTRICT |
| language_code | LANG | 否 | 无 | en / zh-CN / es / ar / fr / de |
| translation_status | ENUM | 否 | draft | draft / approved；仅 approved 可进入提交审核的公开候选 |
| translated_value | TEXT(4000) | 是 | NULL | text 类非源语言翻译 |
| translated_process | JSON | 是 | NULL | process 类非源语言完整 step_key/label 数组 |

约束、索引与删除：UNIQUE(batch_override_id,language_code)。只允许父 operation=set 且 kind=text/json；源语言在父值中，本表只存其他语言。两值列恰一非空，和 field 类型匹配；process step_key/顺序须与父值相同。继承父 Batch draft 锁，提交时冻结。

### 2.7 `inspection_items`

检测项目逐行记录，无 moisture 等固定列。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| batch_id | ID | 否 | 无 | FK batches.id，RESTRICT |
| item_code | CODE | 否 | 应用建议且用户可确认 | 批次内稳定代码，如 MOISTURE；非全局检测词典 |
| name | TEXT(200) | 否 | 无 | 源语言技术名称 |
| source_language | LANG | 否 | en | 名称和规格源语言 |
| value_type | ENUM | 否 | text | decimal / integer / text / none |
| numeric_value | DECIMAL | 是 | NULL | decimal/integer 数值的规范十进制字符串 |
| text_value | TEXT(2000) | 是 | NULL | text 型原始结果，如 <0.1 或 Not detected |
| unit | TEXT(32) | 是 | NULL | 不进行隐式单位换算 |
| standard_value | DECIMAL | 是 | NULL | 标准/目标数值，不代替限值 |
| min_limit | DECIMAL | 是 | NULL | 下限，单位同 unit |
| max_limit | DECIMAL | 是 | NULL | 上限，单位同 unit |
| min_inclusive | BOOL | 否 | true | 下限是否包含 |
| max_inclusive | BOOL | 否 | true | 上限是否包含 |
| specification | TEXT(2000) | 是 | NULL | 源语言规格表达 |
| test_method | TEXT(500) | 是 | NULL | 方法/方法标准编号，不默认真实合规 |
| judgement | ENUM | 否 | not_tested | pass / fail / not_tested / not_applicable / pending / informational |
| sort_order | INT | 否 | 0 | 非负；同序按 item_code 排 |
| internal_note | TEXT(2000) | 是 | NULL | 检测备注，默认私有，不进入 Payload |
| is_public | BOOL | 否 | false | 明确允许公开后才能输出 |
| tested_on | DATE | 是 | NULL | 检测日期，未知为空 |

约束、索引与删除：UNIQUE(batch_id,item_code)；INDEX(batch_id,sort_order,item_code)、(batch_id,judgement)。decimal/integer 只能 numeric_value，text 只能 text_value，none 两者 NULL；decimal/integer 允许结果 NULL 但此时只能 not_tested/pending/not_applicable，pass/fail 必须有结果。not_tested、not_applicable 要求无结果；informational 表示有结果但无通过判定，pending 表示等待结果/判断。十进制比较由应用精确十进制实现，不用 SQLite CAST REAL；min≤max；拒绝单位不一致自动判定。无需改 Schema 增加项目，但每批容量上限可配置。附件通过 asset_links 的 inspection_item_id。

### 2.8 `inspection_item_translations`

附加表：翻译展示名称/规格/方法，不复制检测值和判定；无法并入产品翻译，因为检测归批次且可任意新增。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| inspection_item_id | ID | 否 | 无 | FK inspection_items.id，RESTRICT |
| language_code | LANG | 否 | 无 | en / zh-CN / es / ar / fr / de |
| translation_status | ENUM | 否 | draft | draft / approved；仅 approved 可进入提交审核的公开候选 |
| display_name | TEXT(200) | 否 | 无 | 非源语言展示名称 |
| specification | TEXT(2000) | 是 | NULL | 规格翻译 |
| test_method | TEXT(500) | 是 | NULL | 方法说明翻译 |
| result_display_text | TEXT(2000) | 是 | NULL | 仅 text 型结果展示译文，原结果仍保留 |

约束、索引与删除：UNIQUE(inspection_item_id,language_code)。父行源语言不在本表重复存；不允许改变值/单位/限值/判定。仅父 Batch draft 可修改，提交快照包含有效翻译。

### 2.9 `certifications`

一行是一份不可变认证资料版本；更新生成新行，通过 family_key 识别同一证书族。避免再增 certification_revisions 表。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| family_key | ID | 否 | 新族 UUIDv4 | 同族各修订共享的业务分组标识，不是另一张表 FK |
| revision_number | INT | 否 | 1 | 族内正整数递增 |
| supersedes_id | ID | 是 | NULL | 同族旧 certifications.id，RESTRICT |
| name | TEXT(200) | 否 | 无 | 源语言认证名称 |
| source_language | LANG | 否 | en | 源语言 |
| certification_type | CODE | 否 | OTHER | HALAL/FSSC_22000/ISO/KOSHER/OTHER 等业务代码，可增加 |
| certificate_number | TEXT(200) | 是 | NULL | 真实编号未知不填 |
| issuer | TEXT(500) | 是 | NULL | 真实颁发机构未知不填 |
| valid_from | DATE | 是 | NULL | 生效日期 |
| valid_until | DATE | 是 | NULL | 到期日期 |
| status | ENUM | 否 | unverified | unverified / valid / expired / suspended / revoked；创建时断言，不动态改历史 |
| is_public | BOOL | 否 | false | 资料可公开资格，不等于已经绑定适用 |
| internal_note | TEXT(4000) | 是 | NULL | 认证内部备注 |
| sealed_at | UTC | 是 | NULL | 组装期为空；封存后必填，只有已封存版本可被 certification_links 引用 |

约束、索引与删除：UNIQUE(family_key,revision_number)；INDEX(certificate_number)、(status,valid_until)。创建认证版本须一次事务附带 translations、asset_links，最后封存；未封存草稿即使因错误残留也不能被关联/提交/发布，引用触发器检查 sealed_at 非空。封存后全部内容和子行不可改删；纠错、换证、增加翻译均新版本。关联旧证书不随族最新值变化。valid_from≤valid_until；supersedes 同族且更早。产品/批次适用性由 certification_links 表达，不将所有认证默认适用所有批次。

### 2.10 `certification_translations`

附加表：同一认证版本可共享给多个模板或批次，翻译须跟认证版本冻结，不能挂在产品翻译上。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| certification_id | ID | 否 | 无 | FK certifications.id，RESTRICT |
| language_code | LANG | 否 | 无 | en / zh-CN / es / ar / fr / de |
| translation_status | ENUM | 否 | draft | draft / approved；仅 approved 可进入提交审核的公开候选 |
| name | TEXT(200) | 否 | 无 | 认证名称译文 |
| issuer_display_name | TEXT(500) | 是 | NULL | 颁发机构展示译文，不改真实编号 |

约束、索引与删除：UNIQUE(certification_id,language_code)。源语言在 certifications，本表只存其他语言。封存前同一创建事务完成，父封存后禁止追加/修改/删除。

### 2.11 `certification_links`

附加表：产品模板默认认证与批次增删替换是多对多、有排序/公开权限的关系，无法合并进认证版本本身而不失去复用和范围。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_revision_id | ID | 是 | NULL | FK product_revisions.id，RESTRICT；与 batch_id 恰一非空 |
| batch_id | ID | 是 | NULL | FK batches.id，RESTRICT |
| link_key | CODE | 否 | 无 | 所属对象内认证槽位，如 halal；批次同 key 替换/移除默认 |
| operation | ENUM | 否 | include | include / exclude；模板只能 include |
| certification_id | ID | 是 | NULL | FK certifications.id，RESTRICT；include 必填，exclude 必须 NULL |
| sort_order | INT | 否 | 0 | 非负；按 sort_order/link_key 排序 |
| is_public | BOOL | 否 | false | 链接级公开意图；仍需 certification.is_public |

约束、索引与删除：两个部分唯一索引：(product_revision_id,link_key) WHERE product_revision_id IS NOT NULL；(batch_id,link_key) WHERE batch_id IS NOT NULL。INDEX(certification_id)。exclude 只能移除 base 中存在的 key；include 同 key 全替换，新增 key 为批次额外认证；不自动合并附件。必须父模板 draft 或父 Batch draft；产品封版/批次提交后关系冻结。

### 2.12 `media_assets`

私有工作资产的不可变字节对象；替换上传产生新记录/新 storage_key。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| storage_key | PATH | 否 | 应用生成 | 相对私有存储根，不含宿主机绝对路径；UNIQUE |
| original_filename | TEXT(255) | 否 | 无 | 仅内部保留，不自动作为公开文件名 |
| mime_type | ENUM | 否 | 检验结果 | image/jpeg、image/png、image/webp、application/pdf；不信任扩展名 |
| file_size | INT | 否 | 实际大小 | 正字节数 |
| sha256 | HASH | 否 | 实际文件 Hash | 对原始私有字节计算 |
| availability_status | ENUM | 否 | ready | ready / disabled / purged；仅管理状态可变，不改 bytes |
| is_public_eligible | BOOL | 否 | false | 允许审核选择公开副本的资格 |
| replaces_media_asset_id | ID | 是 | NULL | FK media_assets.id，RESTRICT |
| internal_note | TEXT(2000) | 是 | NULL | 内部说明 |
| purged_at | UTC | 是 | NULL | 私有原文件清理时间；元数据墓碑仍保留 |

约束、索引与删除：INDEX(sha256,file_size)、(availability_status,created_at)。第一版私有文件不物理去重，以降低误删复杂度；sha256 不设 UNIQUE。字节、Hash、MIME、大小、key 不得修改。disabled/purged 不级联 Published Assets；若 sealed 模板/认证仍引用则禁止私有清理，避免今后重建失败；已发布公开副本永不依赖私有文件。临时扫描/上传文件不是本表 ready 对象，扫描成功再事务创建。

### 2.13 `asset_links`

附加表：模板主图、认证附件、检测报告、自定义模块可有多个资产；使用显式可空 FK+XOR 保证引用，不使用无 FK 的 entity_type/entity_id 泛型关联。不能并入资产行，因为资产可复用并有不同角色/排序。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_revision_id | ID | 是 | NULL | FK product_revisions.id，RESTRICT |
| certification_id | ID | 是 | NULL | FK certifications.id，RESTRICT |
| inspection_item_id | ID | 是 | NULL | FK inspection_items.id，RESTRICT |
| custom_section_id | ID | 是 | NULL | FK custom_sections.id，RESTRICT |
| media_asset_id | ID | 否 | 无 | FK media_assets.id，RESTRICT |
| asset_key | CODE | 否 | 无 | 所属对象内稳定附件键，不用原文件名或数据库 ID |
| asset_role | ENUM | 否 | attachment | product_image / certificate / inspection_report / section_image / attachment |
| public_label | TEXT(200) | 否 | 无 | 人工允许公开的安全显示名称，不默认继承原文件名 |
| sort_order | INT | 否 | 0 | 非负 |
| is_public | BOOL | 否 | false | 关联公开意图 |

约束、索引与删除：四个 owner FK 必须恰一非空。各 owner 建 (owner_id,asset_key) 条件唯一索引，product_revision_id+asset_role=product_image 建单图部分唯一索引；INDEX(media_asset_id)。父对象冻结约束传递到本表。公开需 owner 可公开、此行 is_public、media 资格及审核全部满足。认证/检测附件不自动公开。第一版 public_label 用源语言，其他语言回退，不另建附件翻译表。批次主图覆盖以白名单 product_image_asset 字段：由 batch_overrides 专用新增列 value_media_asset_id（见覆盖矩阵）实现，禁止将文件路径写普通文本。

### 2.14 `custom_sections`

模板模块或批次模块/覆盖操作；复用同一表避免另建一套 override section 表。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| product_revision_id | ID | 是 | NULL | FK product_revisions.id，RESTRICT；与 batch_id 恰一 |
| batch_id | ID | 是 | NULL | FK batches.id，RESTRICT |
| section_key | CODE | 否 | 无 | 所属对象内稳定模块键；和 base 同 key 视为操作目标 |
| operation | ENUM | 否 | add | add / replace / hide / inherit；模板只 add |
| section_type | ENUM | 否 | text | text / key_value / table / asset_gallery；扩展类型须版本化，不接任意 HTML |
| source_language | LANG | 否 | en | 与所属模板/批次源语言一致 |
| sort_order | INT | 是 | NULL | 模板/add/replace 必填非负；inherit 可覆盖顺序，NULL 继承 |
| is_visible | BOOL | 否 | true | 显示意图；false 的内容不进入 Payload |
| allow_hide | BOOL | 否 | false | T7 最小扩展：模板是否允许 Batch 隐藏；批次不能自行授权 |
| is_public | BOOL | 否 | false | 默认私有，须明确批准公开 |
| status | ENUM | 否 | draft | draft / ready / disabled；ready 才允许进入候选 |

约束、索引与删除：owner XOR；两个部分 UNIQUE(owner_id,section_key)，INDEX(batch_id,sort_order)、(product_revision_id,sort_order)。模板/add/replace title/content 存 translations，源语言行必填；hide 不带翻译/附件、is_visible=false；inherit 不带翻译/附件，仅排序/visible/public 可调整且不得把 base 私有内容提升为公开。replace 必须完整提供自身内容/附件，不与 base 部分 JSON 深合并。private base 若要公开须新建/replace 并重新明确审核，不靠 inherit 开关。父模板/批次冻结后子项不可改。

### 2.15 `custom_section_translations`

每语言只存模块标题与类型化内容，源语言也在此表唯一保存。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| updated_at | UTC | 否 | 应用事务时间 | 最后修改时间 |
| updated_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT |
| custom_section_id | ID | 否 | 无 | FK custom_sections.id，RESTRICT |
| language_code | LANG | 否 | 无 | en / zh-CN / es / ar / fr / de |
| translation_status | ENUM | 否 | draft | draft / approved；仅 approved 可进入提交审核的公开候选 |
| title | TEXT(200) | 否 | 无 | 人工公开候选标题 |
| content | JSON | 否 | 无 | 按 section_type 严格结构校验，见 Payload 文档 |

约束、索引与删除：UNIQUE(custom_section_id,language_code)。text={text}；key_value={items:[{key,label,value}]}；table={columns:[{key,label}],rows:[{cells:[text]}]}；asset_gallery={caption}，资产只从 asset_links 提供，不允许内容 JSON 注入路径/ID。所有对象禁止额外 key；翻译不得改行/列/项目稳定 key、数量和对应关系。父 operation hide/inherit 不允许插入本表。

### 2.16 `passport_revisions`

一次获批发布形成的不可变内容版本；准备期与正式 Published 明确区分。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| batch_id | ID | 否 | 无 | FK batches.id，RESTRICT |
| version_number | INT | 否 | 分配器 | 批次内正整数，不复用 |
| base_product_revision_id | ID | 否 | 固定源 | 与 Batch 创建绑定一致，FK product_revisions.id，RESTRICT |
| source_revision_id | ID | 是 | NULL | 本次基于的前一公开头，同 batch passport_revisions.id，RESTRICT |
| rollback_source_revision_id | ID | 是 | NULL | 回滚内容来源，同 batch 已发布旧版本，RESTRICT |
| source_edit_version | INT | 是 | NULL | 正常发布取已审核 edit_version；T10 回滚保留目标原审核 edit_version（来源追溯，不参与重建） |
| source_content_hash | HASH | 否 | 审核候选摘要 | 原审核候选摘要；T10 回滚保留目标审核摘要，业务等值另用 content_hash |
| frozen_input | JSON | 否 | 应用构造 | 私有完整可重建输入+公开批准决策+源资产清单；不是 Public Payload |
| schema_version | TEXT(16) | 否 | 应用显式传入 1.0 | 锁定输出契约 |
| builder_version | TEXT(64) | 否 | 实际构建版本 | 可重复构建所用 Builder 版本 |
| payload | TEXT | 是 | NULL | Validate 前一次写入最终规范 UTF-8 JSON 字符串；禁止存为可重排 JSONB |
| payload_hash | HASH | 是 | NULL | payload 确切字节 SHA-256；prepared 前必填 |
| content_hash | HASH | 是 | NULL | payload 除 publication 信封的规范业务内容 Hash，支持回滚等值验证 |
| snapshot_path | PATH | 是 | NULL | 相对公开根 versions/批次/vN.json；prepared 前必填 |
| asset_manifest_hash | HASH | 是 | NULL | 规范排序冻结资产清单 Hash |
| sealed_at | UTC | 是 | NULL | prepared 前设置；之后 payload/input/资产全不可变 |
| published_at | UTC | 是 | NULL | 文件激活时刻，事后对账可一次填入；一旦非空整行不再改 |
| published_by | USER | 否 | 发起发布用户 | FK sys_user.user_id，RESTRICT；回滚为回滚发起人 |
| reviewed_by | USER | 否 | 批准用户 | FK sys_user.user_id，RESTRICT |
| reviewed_at | UTC | 否 | 审核时间 | 不可变审核证据 |
| release_identifier | ID | 否 | UUIDv4 | 本次发布唯一标识，与唯一 publish_record 对应 |

约束、索引与删除：UNIQUE(batch_id,version_number)、UNIQUE(batch_id,id)、UNIQUE(release_identifier)、UNIQUE(id,release_identifier)；组合 FK(batch_id,base_product_revision_id)→batches(id,base_product_revision_id) 固定批次来源；INDEX(batch_id,published_at)、(published_at)、(rollback_source_revision_id)。source/rollback FK 使用 (batch_id,source_id)→passport_revisions(batch_id,id)；源版本须已 published_at 非空且 version 更小，触发器检查。本表不重复 workflow_status/publish_status，以 published_at 非空定义正式发布历史。publish_record_id 是通过 publish_records.passport_revision_id UNIQUE 反向取得的只读字段，不增加循环持久 FK；API 如需要可派生展示。任何正式发布历史禁止 UPDATE/DELETE；sealed 后唯一允许 published_at 从 NULL 一次补齐。失败未发布准备版本保留，不伪装正式 Vn，版本号允许空洞。

### 2.17 `published_assets`

每个 Passport Revision 的冻结公开资产引用；可共享相同内容寻址物理文件，但每个版本保留独立清单行。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| passport_revision_id | ID | 否 | 无 | FK passport_revisions.id，RESTRICT |
| source_media_asset_id | ID | 否 | 无 | FK media_assets.id，RESTRICT；保留墓碑，不依赖其私有字节 |
| asset_key | CODE | 否 | Builder 生成 | 版本内公开安全键，不含数据库 ID |
| asset_role | ENUM | 否 | 无 | product_image / certificate / inspection_report / section_image / attachment |
| original_filename | TEXT(255) | 否 | 来源记录 | 仅后台留存，不进入公开 Payload |
| public_label | TEXT(200) | 否 | 审核标签 | 可公开友好名称 |
| published_filename | TEXT(80) | 否 | sha256.ext | 不可使用用户原文件名 |
| mime_type | ENUM | 否 | 最终字节检验 | JPEG/PNG/WebP/PDF 四种 MIME |
| file_size | INT | 否 | 最终字节大小 | >0 |
| sha256 | HASH | 否 | 最终文件 Hash | 如清理元数据/转换，以处理后字节为准 |
| published_path | PATH | 否 | assets/sha256/前两位/hash.ext | 相对公开根，content-addressed 路径 |
| transform_version | TEXT(64) | 否 | 应用显式传入 identity-v1 | 记录清理/转码规则版本；identity 也必须验证 |
| source_asset_sha256 | HASH | 否 | 来源私有 Hash | 核验冻结输入和实际来源一致 |

约束、索引与删除：UNIQUE(passport_revision_id,asset_key)；INDEX(passport_revision_id)、(sha256)、(source_media_asset_id)、(published_path)。sha256/path 不 UNIQUE（多个版本可复用）。同路径所有引用必须 MIME/大小/Hash 相同，写入前核对物理字节；prepared/sealed 后本表禁止 INSERT/UPDATE/DELETE。正式版本引用永不 GC；去重文件回收须扫描所有版本和未决记录引用，不用易失计数判断。public_url 由部署 root + published_path 派生，不持久化域名/绝对路径。

### 2.18 `publish_records`

一次逻辑发布操作及其可恢复执行状态；HTTP 重试通过同一幂等键返回同一记录。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | 应用生成 UUIDv4 | 内部主键；绝不输出公网 |
| created_at | UTC | 否 | 应用事务时间 | 创建时间 |
| created_by | USER | 否 | 当前内部用户 | FK sys_user.user_id，RESTRICT；仅 Disable 用户，不硬删 |
| batch_id | ID | 否 | 无 | FK batches.id，RESTRICT |
| passport_revision_id | ID | 否 | 无 | 同 batch FK passport_revisions.id，RESTRICT；UNIQUE 一对一 |
| operation_type | ENUM | 否 | publish | publish / rollback；不把旧版本改成 rolled_back |
| publish_status | ENUM | 否 | pending | pending / building / validating / prepared / switching / published / failed / recovery_required |
| idempotency_key | TEXT(128) | 否 | 请求键 | 作用域 batch，UNIQUE(batch_id,idempotency_key) |
| release_identifier | ID | 否 | 同 revision | UNIQUE；与 revision.release_identifier 必须相等 |
| expected_current_revision_id | ID | 是 | NULL | 操作前公开头，同 batch 已发布 passport revision，RESTRICT |
| started_at | UTC | 是 | NULL | 首次执行开始 |
| completed_at | UTC | 是 | NULL | 终态 published/failed 必填 |
| switched_at | UTC | 是 | NULL | 稳定文件已替换的实际时间证据；恢复时可能是观测时间，见 Publish 文档 |
| updated_at | UTC | 否 | 事务时间 | 执行状态变动 |
| attempt_count | INT | 否 | 0 | 本逻辑操作的内部恢复次数，不重新分配版本 |
| asset_count | INT | 是 | NULL | prepared 前必填，等于 Published Assets 行数 |
| error_code | CODE | 是 | NULL | 脱敏机器错误码 |
| error_message | TEXT(2000) | 是 | NULL | 脱敏错误摘要，不含私有路径/令牌 |
| state_version | INT | 否 | 1 | 状态 CAS 防乱序更新 |

约束、索引与删除：UNIQUE(passport_revision_id)、UNIQUE(batch_id,id)、UNIQUE(batch_id,idempotency_key)、UNIQUE(release_identifier)；INDEX(publish_status,updated_at)、(batch_id,created_at)。组合 FK(batch_id,passport_revision_id) 与 expected_current 确保同批次；(passport_revision_id,release_identifier)→passport_revisions(id,release_identifier) 保证同一次发布标识。再建 UNIQUE(batch_id) WHERE publish_status IN (pending,building,validating,prepared,switching,recovery_required) 的部分唯一索引，从 DB 层限制一个批次最多一个未决作业。published_by/reviewed_by/snapshot_path/payload_hash/rollback_source 为 JOIN revision 派生字段，避免两处互相冲突；审核及发布人不从可变 Batch 当前字段读取。published 终态不改，回滚另建记录+版本；failed 可保留诊断，不直接复活重写已封存 Payload，人工再发用新键/新版本。未知切换结果不能标 failed，必须 recovery_required 对账。

### 2.19 `passport_audit_events`

追加式业务审计；不复用 HTTP 系统日志，业务变更与审计同事务提交。

| 字段 | 类型 | Nullable | 默认值 | 意义 / 外键 |
| --- | --- | --- | --- | --- |
| id | ID | 否 | UUIDv4 | 主键，禁止公开 |
| batch_id | ID | 是 | NULL | FK batches.id，RESTRICT |
| passport_revision_id | ID | 是 | NULL | FK passport_revisions.id，RESTRICT；有值 batch_id 必填且组合 FK(batch_id,passport_revision_id)→passport_revisions(batch_id,id) |
| actor_user_id | USER | 否 | 实际用户或专用执行器账户 | FK sys_user.user_id，RESTRICT；不能用 NULL 模糊责任 |
| created_at | UTC | 否 | 事务 UTC | 追加时间 |
| event_type | ENUM | 否 | 无 | batch_created/batch_cloned/batch_edited/override_set/override_cleared/review_submitted/review_approved/review_rejected/publish_requested/publish_succeeded/publish_failed/rollback_requested/rollback_succeeded/archived/media_replaced/inspection_changed/certification_linked/product_revision_sealed；T5 新增 product_created/product_updated/product_revision_created/product_revision_cloned/product_revision_updated/product_default_revision_changed/product_translation_updated（迁移 1788825600000）；T6 新增 override_reset（迁移 1788912000000） |
| entity_type | ENUM | 否 | 无 | 本文业务表名闭合注册，不是任意字符串 |
| entity_id | ID | 否 | 被操作行 | 逻辑目标标识；多态审计不强行伪造 FK，batch/revision 真 FK 负责主线 |
| summary | TEXT(500) | 否 | 应用生成 | 私有脱敏摘要，不存用户整份输入 |
| before_data | JSON | 是 | NULL | 有界变更字段旧值，不记录整个聚合 |
| after_data | JSON | 是 | NULL | 有界变更字段新值 |
| metadata | JSON | 否 | {} | 闭合键 event_schema_version/request_id/changed_fields/before_hash/after_hash/source_id/record_id/truncated/reconstructed（布尔）；不写凭据 |

约束、索引与删除：INDEX(batch_id,created_at,id)、(passport_revision_id,created_at)、(actor_user_id,created_at)、(event_type,created_at)、(entity_type,entity_id,created_at)。before+after+metadata 总和建议≤16KiB，超限保留字段名/摘要/hash 与已有不可变版本引用，不复制巨量 Payload/PDF。数据库触发器禁止 UPDATE/DELETE；业务 API 无删除入口。对 draft 子行删除事件允许保留已不存在的 entity_id，故多态目标无 FK 是刻意选择；已发布历史与主线 FK 不可硬删。

## 3. 批次覆盖白名单与有效值算法

覆盖注册表由应用显式枚举，并在数据库 CHECK field_key/value_kind 配对中镜像；新增普通检测/模块不扩展本表白名单。注册表扩展是受控开发变更，不允许工作人员输入任意路径。以下是第一版完整覆盖集合：

| field_key | value_kind / 值列 | set 的含义 | clear 的含义 |
| --- | --- | --- | --- |
| raw_material_name / raw_material_type / raw_material_origin / raw_material_description | text / value_text | 当前批次源语言文字；其他语言专表 | 当前批次主动不展示该字段 |
| package_description / inner_material | text / value_text | 本批包装说明/内包材 | 空值，不再回退模板 |
| package_quantity | decimal / value_text | 本批净含量，如 20 | NULL；不再继承 25 |
| package_unit / package_type_code | text / value_text | 受控单位/包装技术代码 | NULL；无文字翻译子行 |
| storage_conditions / shelf_life_description | text / value_text | 本批储存/保质期说明 | 主动空白 |
| shelf_life_days | integer / value_integer | 非负天数；不自动更改已填写 expiry_date | NULL |
| process | json / value_json | 完整有序 [{step_key,label}] 列表；全部替换 | 空数组 |
| product_image_asset | asset / value_media_asset_id | 显式选择可公开工作图片及 public_asset_label | 无主图 |

不允许覆盖 product_code、product_name（稳定产品身份名称随模板固定）、batch_code、workflow_status、quality_status、record_type、任何 ID/版本号/时间审计/权限/发布记录字段；质量状态与日期由独立受控业务字段编辑，不从 override API 写入。manufacturer 也不允许用通用 Override 改变身份，模板选错应另建批次。其他批次公开说明通过自定义模块。认证、检测和模块走各自模型，不藏在万能 override JSON 中。

有效值步骤：读取 `batches.base_product_revision_id` 的 sealed 模板及其翻译 → 按固定语言回退解析 → 应用白名单覆盖。无行=继承；set=使用覆盖（指定语言缺失时回退覆盖的源语言，**不混回模板旧译文**）；clear=对应字段 NULL/空数组。取消覆盖时删除覆盖及翻译，同事务审计后恢复继承固定模板，而不是读取 Product 当前 revision。public_asset_label 在 asset set 时必填，其他类型和 clear 时必须 NULL。取消操作由 Editor draft 权限控制。

覆盖变更、取消都保存 actor/time（当前行通用字段 + append-only audit）；before/after 仅存本次覆盖键、旧/新模式和值，较大 process 保存摘要及有界差异。内含供应商/客户敏感内容仍不能自动公开，须重新审核。

## 4. 认证、模块与多语言解析

认证：以模板 certification_links 按 link_key 建初始映射；批次 include 同 key 全替换，exclude 移除，新 key 添加。只有所引用具体 certification 的 sealed 版本可用，不能按 family_key 查“最新”。输出要求 link.is_public、certification.is_public 和本次审核批准均满足；附件再经 asset_links 资格筛选。认证的当前可用性或到期提示只能影响未来工作选择/新发布，不能改写旧 Snapshot 中的历史状态。

模块：以模板 section_key 建映射；Batch add 必须新 key，replace/hide/inherit 必须命中同一 base 模板的 key。hide 删除最终公开结果，不把隐藏内容随 JSON 下发。replace 完整替换内容与附件，不能深合并；inherit 只覆盖显示/排序且不得将原私有模块升级公开。最终按 sort_order、section_key 稳定排序；只有 ready、visible、public 且审核允许的模块进入 Public Builder。模板/批次可私有保存 Customer Requirement，默认 is_public=false；模块名字不是公开许可。

新增 text/key_value/table/asset_gallery 模块不改数据库 Schema。新增全新渲染类型可能需要 Builder/前端/Schema 版本升级，不能承诺任何未知类型零开发。key_value/table 已覆盖普通“自定义字段”；不另建可任意映射内部数据库列的 custom_fields 引擎。

语言代码规范为 en、zh-CN、es、ar、fr、de。Product/Section 源语言也在 Translation Table，其他有技术源名称的实体只追加非源语言译文。每实体每语言 UNIQUE，禁止六套主数据。translated status 仅表示文字已批准，不替代业务审核。任意译文变动计入父聚合 edit_version/content_hash；sealed 模板/认证新增翻译也要新版本；Batch pending 时禁止改翻译。

前端当前不实现六语言 UI。未来每次发布只输出本次批准的语言集合；逐字段回退到本次快照源语言，不能运行时查后台翻译，也不能回退当前最新模板。展示 AR RTL 留给前端；主数据结构不因方向改变。附件标签首版源语言回退，不因可选能力再增加一张表。

## 5. 状态的唯一权威来源

| 事实 | 唯一权威存储 | 规则 |
| --- | --- | --- |
| 产品是否可选 | products.lifecycle_status/current_revision_id | 默认指针必须指向同产品 sealed 模板；历史 Batch 不跟指针 |
| 模板是否不可变 | product_revisions.revision_status=sealed | 单向封版；主行与所有内容子表冻结 |
| 当前工作集 Draft/Pending/Published/Archived | batches.workflow_status | 不在其他表重复 workflow_status |
| 本轮提交/审核元数据 | batches.submitted_*/reviewed_*/rejection_reason | 每轮重置前先保留审计；submitted_input/hash 固定审核事实 |
| 某次发布进度 | publish_records.publish_status | 不拿 Draft/Pending 代替文件作业进度 |
| 某个内容版本确已正式发布 | passport_revisions.published_at 非空 | 一次填入后整行不可变；不是可反复切换状态 |
| 后台确认的当前版本 | batches.current_passport_revision_id | 只由成功发布/对账事务更新，不从最大 version_number 猜测 |
| 公网实际读取版本 | published/{batch_code}.json 的完整字节 | DB/文件不可能跨资源同事务；发生窗口期以文件实况对账，详见发布文档 |

工作流转换：

- Editor：draft → pending_review，原子计算 submitted_input、content_hash、preview_hash，捕获 edit_version/schema/builder；填提交人时间，清空旧审核字段。对所有公开结果缺失信息和敏感资料做校验，不捏造合格。
- Reviewer 驳回：pending_review → draft，写审核人/时间/理由与审计；保留本轮 submitted_input 直到下一次提交覆盖，旧记录的重要摘要转审计。不能在已有 active publish 时驳回。
- Reviewer 审核发布：必须重算匹配 submitted_edit_version/content_hash/preview_hash；批准与创建唯一 publish_record/准备 revision 在一个 DB 事务。workflow 仍 pending_review，直到原子激活及确认成功再变 published。
- 发布失败：工作集仍 pending_review，旧 current 不变；已失败作业保留。允许明确重新审核发布/驳回，不将失败准备 revision 当正式发布。
- 已发布后改稿：显式 published → draft，保留 current；之后编辑不会影响旧静态 JSON/文件。不可直接 PATCH 已发布 Passport Revision。
- Archive：无未决发布时 Super Admin 将工作集 archived 并写 archived_at/by/审计，停止编辑/发布，默认保留旧公开头和所有历史；不把“归档”误作“公网撤回”。重新开放须显式审计，返回 draft；公开撤回/法律删除不是首版自动能力。

`published_at` 不再重复保存在 batches；列表需要最近发布时间 JOIN current revision。publish_records 中要求的发布用户、审核用户、snapshot_path、payload_hash、rollback_source 从它的唯一 revision JOIN 提供，避免冗余字段分歧。发起人 created_by 与 published_by 相同场景由事务验证，系统执行 actor 可另记审计。

## 6. 数据库约束与不可变保护清单（待 T4 实现，不是已执行 Migration）

外键解决存在性，不会阻止被引用记录 UPDATE；必须补充冻结触发器和应用状态机。GORM hook 可被 Raw SQL 绕过，因此不能是唯一保护。SQLite 每个连接显式开启并验证 foreign_keys；组合 FK 目标 UNIQUE 与类型/排序规则一致。

| 编号 | 数据库层必须拒绝的动作 | 应用层补充 |
| --- | --- | --- |
| I01 | Product/Batch identity 与 Batch.base_product_revision_id UPDATE；引用非 sealed 模板 INSERT | 创建事务固定当前模板，编码规范/路径校验 |
| I02 | sealed Product Revision 的 UPDATE/DELETE；向其 translations/sections/cert links/asset links INSERT/UPDATE/DELETE | 编辑开新 revision；封版事务校验源语言、附件和 hash |
| I03 | certification.sealed_at 非空后内容/翻译/附件修改删除；cert links 引用未 sealed | 换证/纠错/翻译生成新认证版本，旧附件保留 |
| I04 | Batch 非 draft 时任何 overrides/inspection/section/cert links/其翻译附件的写入；active_publish_record_id 非空时改工作集 | 所有内容修改核对 edit_version；同事务增加版本和写审计；系统只可更新许可状态列 |
| I05 | 子行 owner FK 改挂其他父对象，或 section replace/exclude 跨模板命中 | 需要换归属用明确复制/新行；不能移动冻结子项绕过锁 |
| I06 | sealed Passport Revision 修改 payload/hash/input/source/版本/schema/资产清单；正式 published 版本所有 UPDATE/DELETE | 发布构建一次封存；唯一特例 sealed 未 published 时一次设置 published_at，必须对应 switching/recovery 作业 |
| I07 | sealed/Published Revision 的 Published Assets 插入、更新、删除 | content-addressed 文件只写一次并验证 Hash，不能仅保护数据库行 |
| I08 | current head 指向未正式发布/异批次版本；active record 指向异批次记录；版本来源跨批次/非早期版本 | 激活单执行器+文件锁；不允许普通接口直接改 current 指针 |
| I09 | terminal publish_records 内容或状态被改写；audit UPDATE/DELETE | 发布终态写一次，恢复前用非终态；审计只能 append |
| I10 | owner XOR、模式/类型/值列 CHECK、长度/枚举/唯一键/FK 违反 | 嵌套 JSON、十进制比较、语言回退、白名单由 typed validator 检查，DB 不承担任意 JSON 业务合并 |

触发器 UPDATE 必须检查 OLD 与 NEW 父对象，禁止通过改 FK 逃离冻结父对象；触发器涉及多表时不以 SQLite CHECK 子查询实现。I04 例外只允许已枚举的系统状态/计数/提交摘要字段，不允许通用“跳过冻结”开关。批次新 edit_version 使用乐观锁 compare-and-set；子表 DML 的 DB 触发器也递增父 edit_version 防漏记，应用以事务最终版本为准，不能预期每次只加 1。提交事务检查最终版本并冻结。

UUID/版本来源关系必须无自引用，source 版本严格更早。FK 本身不验证“当前字段同批次”时，使用本文组合 FK；sealed 条件、来源发布时间、字段配对等跨表约束用触发器。触发器、CHECK、GORM UUID 映射和外键迁移顺序都需 T4 实际验证。

这里的不可变是应用与正常数据库写入路径下的保护，不是抵御宿主机 root/数据库文件所有者任意篡改的物理保证。文件 Hash 是一致性检测，不是数字签名或第三方认证。

## 7. 删除和保留策略

| 对象 | 普通后台动作 | 物理删除及关系 |
| --- | --- | --- |
| products | Disable/Archive | 有 revision 就 RESTRICT，已用编码永不重用 |
| product_revisions | draft 编辑/abandoned；sealed 保留 | 仅无引用 draft 可显式先删子行再删父，所有 FK RESTRICT |
| batches | Archive | 有 Passport/Publish/Audit 主线引用则 RESTRICT；第一版只归档，不为清理测试批次破坏审计 |
| 覆盖/检测/模块/关联/译文 | 仅可改的工作集显式删除 | 父冻结后禁止删；子表用 RESTRICT，按受控顺序删除并审计，不配置普遍 CASCADE |
| certifications | 新版本替代旧版本 | 已 sealed 不删；未封存组装草稿可显式清理无引用行 |
| media_assets | disabled；符合条件才 purge 私有字节 | 元数据墓碑与 Hash 留存；Published Assets FK RESTRICT，不做 SET NULL 破坏来源追踪 |
| passport_revisions | 查询/从旧版创建新回滚版 | 正式及 sealed 版本不改不删；失败准备版本也保留诊断，文件 GC 不等于删历史记录 |
| published_assets | 不提供编辑/删除按钮 | 有正式或未决引用的文件永不自动删除；version FK RESTRICT |
| publish_records | 查询/新建操作 | 终态不可改删；回滚不改旧记录 |
| passport_audit_events | 查询 | 只追加，受控备份/归档策略另行设计，不默认定时 DELETE |
| sys_user | 使用上游 Disable/软删除 | 有业务历史的用户行 RESTRICT，不能级联删除业务 |

本模型有意不使用 ON DELETE CASCADE/SET NULL 于重要历史链。普通删除产品/资产不能触发历史 JSON 或公开文件删除。私有资产 purge 还须检查 sealed 模板/认证、待审核输入、未决发布与恢复需求；发布记录/资产清单是长期保留引用，GC 不用简单计数器。磁盘容量上限与备份保留规则在后续阶段实现。

## 8. Clone Batch

事务读取可见来源 Batch 的固定 base revision 与选定工作数据（来源若正在审核可只读复制其固定 submitted_input），新建全新 Batch ID/code、同 product/base，cloned_from_batch_id=来源；不隐式升级产品模板。

复制适用的覆盖值、检测项目代码/规格/单位/限值/方法和自定义模块，重建子表新 ID 和翻译 FK。默认清空 numeric/text 结果、tested_on、检测报告关系，判定重置 not_tested；生产日/到期日要求重新输入。认证关联可复制其固定版本，但发布前重新检查适用与资格；明确客户特定/私有模块需要确认是否适用于新批。

新工作流 draft、edit_version=1（构建子行后的实际版本由实现统一确定）、全部 submitted/reviewed/current/active/archived 字段 NULL，next_version_number=1。不复制 Passport Revision、Publish Record、Published Asset 或旧业务审计，不把旧检测合格证据悄悄带入新批。写 batch_cloned 事件后完成事务。员工只需确认模板与适用内容，填写新批号/日期/检测，不需操作数据库。

## 9. SQLite → PostgreSQL 迁移边界

继续使用独立 SQLite，不因为可扩展性提前改库。UUID、FK、整数版本/排序、BOOL、UTC、日期与 TEXT+CHECK 枚举有明确映射；不使用 SQLite rowid 作为业务逻辑、FTS 专用结构、数据库特有 JSON 查询或浮点检测比较。

工作 JSON 如 process_steps/content/frozen_input/audit 可在严格去重键解析后转 JSONB。**passport_revisions.payload 必须保留规范原文 TEXT/字节**：JSONB 可重排键/表示，不能回读 JSONB 再期望 payload_hash 不变。迁移后逐字节验证 JSON 快照、Hash、公开资产路径与历史版本数量。

迁移不是改 DSN 即完成：需要 UUID/UTC/DECIMAL 转换，建立同等 FK/唯一/部分索引，改写对应数据库触发器，检查 sys_user 整数类型与现有权限数据，验证源自增系统表的序列、软删除约定与所有关系。业务表不用 deleted_at 参与自然键复用，产品/批次代码终身唯一。事务状态机保持一致，PostgreSQL 的锁实现按其语义替换 SQLite 单写约束。

物理路径不入 DB，存储根/域名仅环境配置；数据库与公开根备份分别恢复后对账。测试和生产采用独立 DB/存储根/任务队列，单库只管理一个发布环境，不在表中塞混用的生产开关；跨环境移动使用受控导出/导入，不直接复用发布指针。

## 10. 依据与未验证项

SQLite 的类型亲和性和日期/布尔表示参照 [官方类型说明](https://www.sqlite.org/datatype3.html)，外键逐连接启用、组合父键唯一约束参照 [官方外键文档](https://www.sqlite.org/foreignkeys.html)。冻结约束拟用 [SQLite 触发器](https://www.sqlite.org/lang_createtrigger.html)；迁移时 JSONB 的语义差异参照 [PostgreSQL JSON 类型](https://www.postgresql.org/docs/18/datatype-json.html)。这些官方事实支持设计，不代表本机已执行对应保护。

T4 尚待验证：真实 GORM/sqlite3 驱动、外键与触发器安装顺序、空库全部迁移、Casbin 权限持久化、SQLite 锁/备份恢复。T8–T12 尚待验证：角色越权、状态冲突、冻结后 Raw SQL 修改被拒、原子发布中断恢复、资产 GC、跨版本渲染。T3 不执行这些运行测试。

## T4 实现校准（2026-09-07）

19 表、字段及关系不变，SQLite 运行结果见 T4_RUNTIME_VALIDATION.md。可空 UTC 的 CHECK 使用 `column IS NULL OR (...)`，避免 NULL 被 `julianday(...) IS NOT NULL` 拒绝；检测 pass/fail/informational 无值检查使用 COALESCE，避免 SQL 三值逻辑放过空值。前者在首次插入时发现，以新增版本 1788739201000 修正；后者在首次业务迁移前修正。

`schema_version` 与 `transform_version` 的默认语义由调用方显式传入（当前测试为 1.0 / identity-v1），不依赖数据库隐式默认。transform_version 缺失被 NOT NULL 拒绝，防止未经明确选择清理规则就登记冻结资产。其余应用生成 UUID、用户、时间、版本分配仍由事务调用方负责。关系无变化，无需重画 ERD。

数据库已实现的局部冻结触发器不等于完整应用审核/发布状态机。版本分配器、内容摘要重算、公开 Payload 白名单验证、文件 MIME/净化、授权及发布恢复对账仍为后续应用责任；T4 的冻结文件原型不能作为正式发布引擎使用。

## T5 产品模板实现校准（2026-09-08）

T0–T4 已由用户人工验收。本轮仅实现 products / product_revisions / product_revision_translations 的管理、封版、默认选择与归档，不进入批次管理或发布。

唯一 Schema 变化为新增版本化迁移 1788825600000：扩展 passport_audit_events.event_type 的 7 个产品模板事件；保留既有 archived 与 product_revision_sealed 事件名称。事务内重建该审计表的 CHECK，逐行保留已有数据、索引与不可变触发器，同时注册 Go Admin 菜单/API 权限种子。未增加业务表、列或关系，T4 的两份历史迁移保持原文，ERD 关系不变。已以 T4 有数据副本升级验证 19 表数据摘要不变，并验证空库与重复迁移。

Product 创建 API 原子建立 Product + R1 Draft + 至少源语言翻译 + Audit；不提供无 Revision 的产品创建入口，也不提供 Hard Delete。Product Code trim 后转大写，创建后不可改，归档不复用编码。稳定字段编辑只开放 active/disabled；archived 是本阶段终态。

Draft 全量内容替换及单语言 upsert 使用服务层字段白名单；未知系统字段、重复 JSON key 被拒绝。编辑令牌是聚合内容摘要（请求前置条件，不新增数据库列），用于拒绝并发旧稿覆盖。新版本在取得 SQLite 写入锁后于事务中分配号码；已提交版本不删除或复用编号。

Clone 复制三个已开放表的模板内容及六语言，重建 ID、actor、时间，重置 draft、sealed_* 与 content_hash；译文状态重置 draft，必须重新确认源语言才能封版。创建新版本不自动切默认；只能显式选择同产品 sealed Revision。仅改 Product 指针，不写 Batch 或旧 Revision。

封版采用 product-template-v1 的确定性 Go JSON 摘要：固定 DTO 字段序、按 language_code 排列译文、JSON map 键稳定排序，覆盖结构化模板和翻译内容；排除内部行 ID/创建元数据。不等同未来 Public Payload 的规范化构建协议或资产冻结。对于带有 T5 尚未开放的 custom_sections/certification_links/asset_links 的来源，Clone/Seal 明确拒绝，防止悄悄遗漏子内容；不提前开发这些管理系统。

包装数量暂允许非负十进制，最多 18 整数位 + 9 小数位；结构化 CODE/LANG/长度规则沿用本模型，原产国为两位大写代码格式校验。正式发布的数量 >0、完整国家字典、六语言公开条件等仍归未来 Builder/审核校验，不声称 T5 Draft 已符合公开发布要求。完整 API、测试与限制见 T5_PRODUCT_TEMPLATE.md。


## T6 批次管理实现校准（2026-09-08）

用户已确认 T0–T5 人工验收通过。本轮 T6 只实现本地批次草稿管理；完整结果见 T6_BATCH_MANAGEMENT.md。19 张业务表、308 列和 ERD 关系不变；新增迁移 1788912000000 仅扩展审计 event_type CHECK 的 override_reset，以及注册批次菜单/5 条聚合 API 权限。T4/T5 历史迁移保持不变。

- 创建只采用 active Product 的 `current_revision_id`，事务内核实同产品 sealed 后写入 Batch.base_product_revision_id。本阶段没有手选历史版本/重绑接口。请求提交 base_product_revision_id 会被拒绝；历史版本仅通过 Clone 源批次固定保留。
- Batch Code trim/大写、1–64 ASCII 字母数字下划线连字符；创建后固定。record_type 默认 test、可显式 commercial，创建后固定。所有本轮验收记录均为 test。日期仍遵循可 NULL 的模型，未知不伪造，填写时验证真实日历和先后关系。
- 普通更新只接受 Draft 且 active_publish_record_id=NULL；使用 expected_edit_version。基础信息、覆盖、检测及审计作为一个聚合事务保存。子表触发器自动增量与应用显式增加并存，返回实际最终 edit_version，不承诺每次仅加 1。
- 原覆盖矩阵中 13 个非资产字段开放源语言结构化表单，全部保持设计已经明确的 clear 语义；不因未来公开字段可能必填而改变 Draft 清空语义。禁止字段/未开放图片覆盖不能 set/clear。无行=inherit，set 使用类型化值，clear 使用 NULL/process []；恢复继承删除覆盖及其翻译。public_asset 字段管理不在本轮。
- ResolveEffectiveBatch 统一计算固定模板和覆盖的工作内容及来源标签。目标语言覆盖译文缺失时回退到覆盖源语言，不混回模板旧译文。未知/未开放覆盖类型拒绝预览。它没有公开资格过滤、资产构建或快照承诺，不可直接输出公网。
- 检测项目动态逐行，单批最多 100 项。源语言来自固定模板；以批次内 item_code 匹配编辑，普通字段更新保留 ID；更换代码在聚合中表现为显式移除旧项目并新增。六个既有 judgement 状态保留，数值为精确十进制字符串，Min/Max 以 big.Rat 比较；判定由员工录入，不自动判定、不换算单位。
- 本阶段不新增覆盖/检测多语言编辑页面。保持未变译文；覆盖改写已有译文时拒绝，明确恢复继承可删除对应覆盖译文；含译文的检测项目改写拒绝，显式删除项目时删除其译文。含检测附件的改删/Clone 拒绝，避免无管理能力时破坏关系。
- Clone 仅允许可见、未锁定 Draft，要求 expected_edit_version 和新批号；保留源 product/base、record_type 和允许覆盖。新日期来自本次输入（未知可 NULL），质量重置 pending、工作流 draft、审核发布归档字段空、next_version_number=1。重建主/子 ID、操作者和时间，清空检测 numeric/text/result_display_text、tested_on、internal_note、judgement→not_tested；保留定义/限值/排序/公开候选标志，译文状态回 draft。含未开放模块/认证/附件的来源拒绝复制。
- 沿用 batch_edited、inspection_changed 注册事件，inspection_changed 的有界 after_data.operation 区分 create/update/delete；新增 override_reset 表达恢复继承。全部业务写入和 Audit 同事务，前后差异超限改存 Hash 与 truncated 标志。

未实现归档/审核/发布状态操作、T7 模块、T8 工作流、T9 Snapshot/资产冻结/Atomic Publish 或正式 QR。


## T7 实现补充（2026-09-08）

T6 已由用户人工验收通过；T7 完成本地开发与测试、等待人工验收。原 T3/T5/T6 历史报告状态文字保留为当轮记录。T7 通过新增 1788998400000_custom_sections 迁移给 custom_sections 增加 allow_hide（默认 false），关系不变。19 业务表共 309 列。hide、不可见 replace、disabled replace 都须固定 base 明确允许隐藏，inherit 不能把 base 私有内容提升为公开。

类型仍为 text/key_value/table/asset_gallery，后者本轮只开放 caption 结构，资产关联仍封闭保护。模块/译文遵守严格结构、源语言与跨语言行列对应关系；容量、XSS、事务、解析与 API 详见 T7_CUSTOM_SECTIONS.md。模板新增模块后不可切换源语言。Clone Revision/Batch 复制已开放模块与译文并生成新 ID，模块/译文重置 draft，客户专属内容需重新核实适用性。

新模板封版使用 product-template-v2 私有内容摘要，包括全部模块 DTO/译文/排序/公开及隐藏意图；历史 sealed hash 不改。更新 T5/T6 的未开放关联保护范围仅放行已实现模块，认证及模块资产关联仍拒绝，避免遗漏。本轮没有创建 T8 工作流或 T9 Snapshot Engine。

## T8 实现校准：审核决定与发布执行分离

新增迁移 `1789084800000_review_workflow.go/.sql`。T4–T7 迁移原字节不变。当前 20 张业务表、327 列、109 个触发器；上游角色/菜单/API/Casbin 表沿用原结构。

`batches.current_review_record_id`：可空 TEXT FK → review_records.id，RESTRICT，独立索引；UPDATE 归属触发器保证本批次所有。创建草稿为空；提交指向新轮次；驳回保留以查看理由；批准后保留；撤销批准改稿时清空。

### review_records（17 列）

| 字段 | 类型 / NULL | 语义 |
| --- | --- | --- |
| id | TEXT PK NOT NULL | 应用 UUIDv4 |
| batch_id | TEXT NOT NULL FK | batches.id，RESTRICT |
| attempt_number | INTEGER NOT NULL | 本批次递增正整数，UNIQUE(batch_id,attempt_number) |
| decision | TEXT NOT NULL | pending / approved / rejected；一次 pending 到终态转换 |
| candidate_input | TEXT NOT NULL | 受控内部 JSON，最大 4 MiB；永不直接公开 |
| candidate_hash | TEXT NOT NULL | candidate_input 实际 UTF-8 字节 SHA-256，小写 64 位 |
| preview_hash | TEXT NOT NULL | T8 内部预览直接呈现同一候选，故等于 candidate_hash；不是 T9 Public Payload hash |
| source_edit_version | INTEGER NOT NULL | 提交时批次版本 |
| schema_version | TEXT NOT NULL | review-v1（最长 16 字符） |
| builder_version | TEXT NOT NULL | internal-review-v1（最长 64 字符） |
| submitted_by | INTEGER NOT NULL FK | sys_user.user_id |
| submitted_at | TEXT NOT NULL | UTC 毫秒 |
| contributors | TEXT NOT NULL | 冻结创建、编辑、提交用户 ID 的 JSON 数组，用于禁止自审 |
| reviewed_by | INTEGER NULL FK | 决定者，sys_user.user_id |
| reviewed_at | TEXT NULL | 决定时间；pending 时明确允许 NULL |
| comment | TEXT NULL | 最长 2000 字符纯文本 |
| rejection_reason | TEXT NULL | rejected 必填；approved 必须 NULL；最长 2000 字符 |

pending 时所有决定字段 NULL；决定与时间/用户同步写入。部分唯一索引限制每批最多一个 pending，UNIQUE(batch_id,id) 辅助关系；decision/submitted_at/id 队列索引。禁止删除；候选及提交元数据创建后不可变，终态整行不可变；DB 触发器额外拒绝 contributors 中用户自审。新增审计类型 review_returned_to_draft、review_conflict；已有 review_submitted/approved/rejected 复用。

`workflow_status` 原枚举不变。`pending_review + current review.decision=approved` 派生为 `ready_for_publish`，UI 明示“审核通过 · 待发布（未发布）”。这不是 Published，也不产生 Passport Revision/Publish Record/Published Assets。批准后所有工作子表继续锁定。显式 Return to Draft 要求理由，清空当前提交元数据而不修改旧审核行，再次提交产生新行。驳回同样保留旧行并回 Draft。

T8 的 `submitted_preview_hash` 校准为内部 review-v1 的候选摘要；T3 文中“最终公开业务内容 Hash”属于 T9 尚未实现的契约。T9 必须显式验证候选版本、批准有效性、资产转换和公开白名单；不能把 T8 candidate_input 直接当公开 Payload，也不能在不重新审核的情况下引入未见过的业务内容/资产。当前含未开放附件/认证的工作集拒绝提交，不能静默省略。


## T9 实施增量（2026-09-10）

T0–T8 已由用户人工验收。T9 本地实现复用现有 `passport_revisions`、`published_assets`、`publish_records`，没有平行发布模型。

- 新迁移 `1789171200000_publish_engine` 为 `passport_revisions` 和 `publish_records` 各增加 `source_review_record_id TEXT REFERENCES review_records(id) ON DELETE RESTRICT`。允许历史 NULL；新建记录由触发器强制关联同批次、已批准、Hash/输入/编辑版本/审核人一致的审核记录。
- 新增审核来源索引和 `ux_review_published_once`：仅对 `published_at IS NOT NULL` 的记录按 `source_review_record_id` 唯一。失败重试可引用同一审核，新尝试和新版本号仍保留；一次审核最多一个成功修订。
- 新增 4 个触发器，固定审核关联和 PublishRecord 身份字段。原封版、成功修订/资产不可变、复合外键、终态记录不可变约束保留。
- 当前本地业务结构：20 表、329 列、113 个完整性/冻结触发器；14 次迁移。T4–T8 历史迁移未改。
- 新审核候选使用 `review-v2 / internal-review-v2`，冻结可公开图片的原文件元数据、规范化 PNG 字节及摘要；原 `review-v1` 历史记录不改，资产为空的旧候选仍可由发布构建器处理。
- 不新增媒体上传/管理或认证管理。受控测试图片通过既有 MediaAsset/AssetLink 模型在 Draft 时挂接，再走真实 Submit/Approve。PNG/JPEG 转 PNG；PDF/WebP 本轮不开放转换发布，认证关联继续 fail closed。

详细状态、文件契约及证据见 [T9_PUBLISH_ENGINE.md](T9_PUBLISH_ENGINE.md)。


## T10 实现校准（2026-09-10）

新增且仅新增迁移 `1789257600000_version_history`；没有修改 T4–T9 历史迁移。当前 21 张业务表、334 列、115 个触发器、15 次迁移。公开 Schema 1.0 不变。

1. `publish_records.rollback_reason`：可空 TEXT；正常 publish 必须 NULL，rollback 必填 trim 后 1–1000 字且不含 `<`/`>`。Service 另拒绝非法 UTF-8、危险控制字符。身份固定触发器禁止后续改变原因；插入触发器要求对应 Revision 有有效 rollback_source。
2. 新表 `publication_health`：`batch_id TEXT PRIMARY KEY REFERENCES batches(id) ON DELETE RESTRICT`；`reconciliation_required INTEGER NOT NULL DEFAULT 0 CHECK IN(0,1)`；`classification TEXT NOT NULL`；`checked_at TEXT NOT NULL`。这是可更新的最近检查结果，不是业务审计；每次写操作仍以真实文件与 DB 重新验证，不能仅信任此表。
3. `ux_review_published_once` 保持同审核最多一个正常成功发布，partial predicate 增加 `rollback_source_revision_id IS NULL`。回滚保留原批准链，因此可另建回滚版本，但每次有独立管理员授权、原因和审计。Passport 原 `source_review_record_id`、FrozenInput、SourceEditVersion、SourceContentHash、ReviewedBy/At 仍与原已批准 Review 对应，DB 原关联触发器不变。
4. Audit enum 增加 rollback_failed、rollback_reconcile_required、reconcile_started、reconcile_completed、reconcile_failed。复用 rollback_requested（stage prepare/prepared）与 rollback_succeeded。事务内重建 CHECK 表时逐行保留原数据，恢复全部索引与 append-only UPDATE/DELETE 触发器。
5. 9601 功能菜单 `PassportRollback` / `passport:history:rollback`，只授 admin；API 9601–9606 供完整历史/详情/校验/比较/健康/回滚。GET 授既有四角色与组合角色；Reconcile 继续复用 9503 admin 权限并新增必填 reason 请求。

逻辑历史行均无普通修改/删除 API；PublishedAssets 与 Passport 冻结触发器、终态 PublishRecord、审核记录及 Audit append-only 均保留。source_revision_id 表示先前头，rollback_source_revision_id 表示内容来源，新版自己的 PublishedAsset 行明确关联新版；物理 CAS 字节可复用。详见 [T10_VERSION_AUDIT_ROLLBACK.md](T10_VERSION_AUDIT_ROLLBACK.md)。
