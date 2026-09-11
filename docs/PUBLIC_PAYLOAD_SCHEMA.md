# T3 Public Payload 白名单与 JSON Schema 1.0

状态：**等待人工验收**。本文件给出将来 T9 Builder/T11 静态端的独立契约，只有 docs 内设计示例，没有写入 site/、发布目录或数据库。旧 POC 的两个分离 Schema 原样保留；本契约与旧加载方式不同，不能把新 JSON 直接塞进旧 POC 就视为集成完成。

## 1. Public Payload Builder 边界

Builder 接收已固定且已审核的私有输入，逐字段构建新的公开 DTO。拒绝未知字段，禁止 ORM entity 自动序列化、递归透传、把 audit metadata 或任意 custom JSON 展开到根对象。Schema 每层 additionalProperties=false；这约束字段名，**不能自动判断允许的文字字段里是否有人粘贴客户秘密**，仍需要公开资格、审查及内容校验。

| 公开组 | 唯一内容来源 / 白名单 | 不输出 |
| --- | --- | --- |
| product | 固定产品码、模板译文名称、分类码、原产国 | product_id/revision_id、内部备注 |
| batch | 固定批次码、实际日期、质量状态 | workflow、用户、内部审核意见、数据库 ID |
| raw_material/process | 固定模板 + 明确覆盖后的允许文字/步骤 | 任意内部供应商结构 |
| inspection | is_public 且审核允许的项目、值/规格/方法/判定/资产键 | internal_note、操作者、私有报告路径 |
| certifications | 最终适用关系与固定认证版本的公开字段 | family UUID、内部备注、私有认证链接 |
| packaging/storage/manufacturer | 模板及允许覆盖后的明确列 | 成本、报价、客户、未允许的 Override |
| custom_sections | visible/public/ready 且审核允许的类型化文字 | 隐藏内容、私有模块、任意脚本、内部字段/路径 |
| assets | 审核冻结的键/角色/安全标签/相对路径/MIME/大小/Hash | source_media_asset_id、original_filename、storage_key |
| localization | 批准语言及明确可翻译字段 | 翻译人、审核状态、后台语言表 ID |
| publication | 公开内容版本、签发时间、发布/回滚类型及公开来源版本号 | 内部发布人/审核人、Record ID、错误、权限、DB 激活指针 |

资产的公开 key 由 Builder 生成语义键（如 product-image、cert-halal-1），不得复用内部 UUID/数据库 ID。所有 asset_keys 都只引用顶层 assets，资产文件路径从冻结存储生成；Public DTO 不接受用户直接输入文件 URL。

root schema_version 是字符串，不是浮点数。1.0 和未来 1.1/2.0 是独立注册契约；公开端根据精确支持版本选择静态兼容适配器，保留旧渲染能力。未知版本显示明确不兼容提示，不猜字段或回退后台 API。1.1 新契约可有新增字段，旧 1.0 Schema 仍严格不接受未知字段；需要先部署支持 1.1 的前端才发布它。2.0 允许破坏性变化但须保留 1.x 静态适配器，旧 Snapshot 不就地迁移。

## 2. 完整 JSON Schema（设计，不是 Migration）

所有 root 组必填；无资料使用 NULL/[]，不伪造日期、制造商、认证或 PASS。日期解析校验启用 format checker。小数使用字符串防精度丢失。默认单文件建议≤1MiB、单资产≤50MiB；数组容量为第一版安全上限，可在受控契约升级中调整，不代表“只能有这些检测项目”。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Product Digital Identity Public Payload 1.0",
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "schema_version": {
      "const": "1.0"
    },
    "record_type": {
      "enum": [
        "test",
        "commercial"
      ]
    },
    "notice": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 200
        },
        {
          "type": "null"
        }
      ]
    },
    "product": {
      "$ref": "#/$defs/product"
    },
    "batch": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "production_date": {
          "anyOf": [
            {
              "type": "string",
              "format": "date",
              "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "expiry_date": {
          "anyOf": [
            {
              "type": "string",
              "format": "date",
              "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "quality_status": {
          "enum": [
            "pending",
            "released",
            "hold",
            "rejected"
          ]
        }
      },
      "required": [
        "code",
        "production_date",
        "expiry_date",
        "quality_status"
      ]
    },
    "raw_material": {
      "$ref": "#/$defs/raw_material"
    },
    "process": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "step_key": {
            "type": "string",
            "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
            "maxLength": 64
          },
          "label": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200
          }
        },
        "required": [
          "step_key",
          "label"
        ]
      },
      "maxItems": 100
    },
    "inspection": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/inspection"
      },
      "maxItems": 500
    },
    "certifications": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/certification"
      },
      "maxItems": 100
    },
    "packaging": {
      "$ref": "#/$defs/packaging"
    },
    "storage": {
      "$ref": "#/$defs/storage"
    },
    "manufacturer": {
      "$ref": "#/$defs/manufacturer"
    },
    "custom_sections": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/section"
      },
      "maxItems": 100
    },
    "assets": {
      "type": "array",
      "items": {
        "$ref": "#/$defs/asset"
      },
      "maxItems": 200
    },
    "localization": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "source_language": {
          "enum": [
            "en",
            "zh-CN",
            "es",
            "ar",
            "fr",
            "de"
          ]
        },
        "available_languages": {
          "type": "array",
          "minItems": 1,
          "maxItems": 6,
          "uniqueItems": true,
          "items": {
            "enum": [
              "en",
              "zh-CN",
              "es",
              "ar",
              "fr",
              "de"
            ]
          }
        },
        "translations": {
          "type": "array",
          "items": {
            "$ref": "#/$defs/translation"
          },
          "maxItems": 5
        }
      },
      "required": [
        "source_language",
        "available_languages",
        "translations"
      ]
    },
    "publication": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "version_number": {
          "type": "integer",
          "minimum": 1,
          "maximum": 9007199254740991
        },
        "issued_at": {
          "type": "string",
          "format": "date-time",
          "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]{3}Z$"
        },
        "kind": {
          "enum": [
            "publish",
            "rollback"
          ]
        },
        "source_version_number": {
          "anyOf": [
            {
              "type": "integer",
              "minimum": 1,
              "maximum": 9007199254740991
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "version_number",
        "issued_at",
        "kind",
        "source_version_number"
      ]
    }
  },
  "required": [
    "schema_version",
    "record_type",
    "notice",
    "product",
    "batch",
    "raw_material",
    "process",
    "inspection",
    "certifications",
    "packaging",
    "storage",
    "manufacturer",
    "custom_sections",
    "assets",
    "localization",
    "publication"
  ],
  "allOf": [
    {
      "if": {
        "properties": {
          "record_type": {
            "const": "test"
          }
        }
      },
      "then": {
        "properties": {
          "notice": {
            "const": "TEST RECORD — NOT FOR COMMERCIAL USE"
          },
          "batch": {
            "properties": {
              "code": {
                "pattern": "(^|[-_])TEST([-_]|$)"
              }
            }
          }
        }
      }
    },
    {
      "if": {
        "properties": {
          "publication": {
            "properties": {
              "kind": {
                "const": "rollback"
              }
            }
          }
        }
      },
      "then": {
        "properties": {
          "publication": {
            "properties": {
              "source_version_number": {
                "type": "integer",
                "minimum": 1
              }
            }
          }
        }
      },
      "else": {
        "properties": {
          "publication": {
            "properties": {
              "source_version_number": {
                "type": "null"
              }
            }
          }
        }
      }
    }
  ],
  "$defs": {
    "product": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        },
        "category_code": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            {
              "type": "null"
            }
          ]
        },
        "country_of_origin": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^[A-Z]{2}$"
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "code",
        "name",
        "category_code",
        "country_of_origin"
      ]
    },
    "raw_material": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "name": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        },
        "type": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        },
        "origin": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        },
        "description": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "name",
        "type",
        "origin",
        "description"
      ]
    },
    "packaging": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "quantity": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
              "maxLength": 29
            },
            {
              "type": "null"
            }
          ]
        },
        "unit": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 32
            },
            {
              "type": "null"
            }
          ]
        },
        "type_code": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            {
              "type": "null"
            }
          ]
        },
        "description": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        },
        "inner_material": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "quantity",
        "unit",
        "type_code",
        "description",
        "inner_material"
      ]
    },
    "storage": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "conditions": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        },
        "shelf_life_days": {
          "anyOf": [
            {
              "type": "integer",
              "minimum": 0,
              "maximum": 36500
            },
            {
              "type": "null"
            }
          ]
        },
        "shelf_life_description": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "conditions",
        "shelf_life_days",
        "shelf_life_description"
      ]
    },
    "manufacturer": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "name": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 500
            },
            {
              "type": "null"
            }
          ]
        },
        "address": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 4000
            },
            {
              "type": "null"
            }
          ]
        }
      },
      "required": [
        "name",
        "address"
      ]
    },
    "inspection": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "code": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        },
        "value_type": {
          "enum": [
            "decimal",
            "integer",
            "text",
            "none"
          ]
        },
        "numeric_value": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
              "maxLength": 29
            },
            {
              "type": "null"
            }
          ]
        },
        "text_value": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 2000
            },
            {
              "type": "null"
            }
          ]
        },
        "unit": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 32
            },
            {
              "type": "null"
            }
          ]
        },
        "standard_value": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
              "maxLength": 29
            },
            {
              "type": "null"
            }
          ]
        },
        "min_limit": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
              "maxLength": 29
            },
            {
              "type": "null"
            }
          ]
        },
        "max_limit": {
          "anyOf": [
            {
              "type": "string",
              "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
              "maxLength": 29
            },
            {
              "type": "null"
            }
          ]
        },
        "min_inclusive": {
          "type": "boolean"
        },
        "max_inclusive": {
          "type": "boolean"
        },
        "specification": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 2000
            },
            {
              "type": "null"
            }
          ]
        },
        "test_method": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 500
            },
            {
              "type": "null"
            }
          ]
        },
        "judgement": {
          "enum": [
            "pass",
            "fail",
            "not_tested",
            "not_applicable",
            "pending",
            "informational"
          ]
        },
        "tested_on": {
          "anyOf": [
            {
              "type": "string",
              "format": "date",
              "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "asset_keys": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
            "maxLength": 64
          },
          "maxItems": 200,
          "uniqueItems": true
        }
      },
      "required": [
        "code",
        "name",
        "value_type",
        "numeric_value",
        "text_value",
        "unit",
        "standard_value",
        "min_limit",
        "max_limit",
        "min_inclusive",
        "max_inclusive",
        "specification",
        "test_method",
        "judgement",
        "tested_on",
        "asset_keys"
      ],
      "allOf": [
        {
          "if": {
            "properties": {
              "value_type": {
                "enum": [
                  "decimal",
                  "integer"
                ]
              }
            }
          },
          "then": {
            "properties": {
              "text_value": {
                "type": "null"
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "value_type": {
                "const": "integer"
              }
            }
          },
          "then": {
            "properties": {
              "numeric_value": {
                "anyOf": [
                  {
                    "type": "string",
                    "pattern": "^-?(0|[1-9][0-9]{0,17})$"
                  },
                  {
                    "type": "null"
                  }
                ]
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "value_type": {
                "const": "text"
              }
            }
          },
          "then": {
            "properties": {
              "numeric_value": {
                "type": "null"
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "value_type": {
                "const": "none"
              }
            }
          },
          "then": {
            "properties": {
              "numeric_value": {
                "type": "null"
              },
              "text_value": {
                "type": "null"
              },
              "judgement": {
                "enum": [
                  "not_tested",
                  "not_applicable",
                  "pending"
                ]
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "judgement": {
                "enum": [
                  "not_tested",
                  "not_applicable"
                ]
              }
            }
          },
          "then": {
            "properties": {
              "numeric_value": {
                "type": "null"
              },
              "text_value": {
                "type": "null"
              }
            }
          }
        },
        {
          "if": {
            "properties": {
              "judgement": {
                "enum": [
                  "pass",
                  "fail",
                  "informational"
                ]
              }
            }
          },
          "then": {
            "anyOf": [
              {
                "properties": {
                  "numeric_value": {
                    "type": "string",
                    "pattern": "^-?(0|[1-9][0-9]{0,17})(\\.[0-9]{1,9})?$",
                    "maxLength": 29
                  }
                }
              },
              {
                "properties": {
                  "text_value": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            ]
          }
        }
      ]
    },
    "certification": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "key": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "name": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        },
        "type": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "certificate_number": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 200
            },
            {
              "type": "null"
            }
          ]
        },
        "issuer": {
          "anyOf": [
            {
              "type": "string",
              "maxLength": 500
            },
            {
              "type": "null"
            }
          ]
        },
        "valid_from": {
          "anyOf": [
            {
              "type": "string",
              "format": "date",
              "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "valid_until": {
          "anyOf": [
            {
              "type": "string",
              "format": "date",
              "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
            },
            {
              "type": "null"
            }
          ]
        },
        "status": {
          "enum": [
            "unverified",
            "valid",
            "expired",
            "suspended",
            "revoked"
          ]
        },
        "asset_keys": {
          "type": "array",
          "items": {
            "type": "string",
            "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
            "maxLength": 64
          },
          "maxItems": 200,
          "uniqueItems": true
        }
      },
      "required": [
        "key",
        "name",
        "type",
        "certificate_number",
        "issuer",
        "valid_from",
        "valid_until",
        "status",
        "asset_keys"
      ]
    },
    "section": {
      "oneOf": [
        {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            "type": {
              "const": "text"
            },
            "title": {
              "type": "string",
              "minLength": 1,
              "maxLength": 200
            },
            "content": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "text": {
                  "type": "string",
                  "maxLength": 10000
                }
              },
              "required": [
                "text"
              ]
            },
            "asset_keys": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "maxItems": 200,
              "uniqueItems": true
            }
          },
          "required": [
            "key",
            "type",
            "title",
            "content",
            "asset_keys"
          ]
        },
        {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            "type": {
              "const": "key_value"
            },
            "title": {
              "type": "string",
              "minLength": 1,
              "maxLength": 200
            },
            "content": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "items": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "key": {
                        "type": "string",
                        "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                        "maxLength": 64
                      },
                      "label": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200
                      },
                      "value": {
                        "type": "string",
                        "maxLength": 2000
                      }
                    },
                    "required": [
                      "key",
                      "label",
                      "value"
                    ]
                  },
                  "maxItems": 100
                }
              },
              "required": [
                "items"
              ]
            },
            "asset_keys": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "maxItems": 200,
              "uniqueItems": true
            }
          },
          "required": [
            "key",
            "type",
            "title",
            "content",
            "asset_keys"
          ]
        },
        {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            "type": {
              "const": "table"
            },
            "title": {
              "type": "string",
              "minLength": 1,
              "maxLength": 200
            },
            "content": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "columns": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "key": {
                        "type": "string",
                        "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                        "maxLength": 64
                      },
                      "label": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 200
                      }
                    },
                    "required": [
                      "key",
                      "label"
                    ]
                  },
                  "maxItems": 20
                },
                "rows": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "cells": {
                        "type": "array",
                        "items": {
                          "type": "string",
                          "maxLength": 2000
                        },
                        "maxItems": 20
                      }
                    },
                    "required": [
                      "cells"
                    ]
                  },
                  "maxItems": 200
                }
              },
              "required": [
                "columns",
                "rows"
              ]
            },
            "asset_keys": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "maxItems": 200,
              "uniqueItems": true
            }
          },
          "required": [
            "key",
            "type",
            "title",
            "content",
            "asset_keys"
          ]
        },
        {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "key": {
              "type": "string",
              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
              "maxLength": 64
            },
            "type": {
              "const": "asset_gallery"
            },
            "title": {
              "type": "string",
              "minLength": 1,
              "maxLength": 200
            },
            "content": {
              "type": "object",
              "additionalProperties": false,
              "properties": {
                "caption": {
                  "type": "string",
                  "maxLength": 4000
                }
              },
              "required": [
                "caption"
              ]
            },
            "asset_keys": {
              "type": "array",
              "items": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "maxItems": 200,
              "uniqueItems": true
            }
          },
          "required": [
            "key",
            "type",
            "title",
            "content",
            "asset_keys"
          ]
        }
      ]
    },
    "asset": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "key": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
          "maxLength": 64
        },
        "role": {
          "enum": [
            "product_image",
            "certificate",
            "inspection_report",
            "section_image",
            "attachment"
          ]
        },
        "label": {
          "type": "string",
          "minLength": 1,
          "maxLength": 200
        },
        "path": {
          "type": "string",
          "pattern": "^assets/sha256/[0-9a-f]{2}/[0-9a-f]{64}\\.(jpg|png|webp|pdf)$"
        },
        "mime_type": {
          "enum": [
            "image/jpeg",
            "image/png",
            "image/webp",
            "application/pdf"
          ]
        },
        "file_size": {
          "type": "integer",
          "minimum": 1,
          "maximum": 52428800
        },
        "sha256": {
          "type": "string",
          "pattern": "^[0-9a-f]{64}$"
        }
      },
      "required": [
        "key",
        "role",
        "label",
        "path",
        "mime_type",
        "file_size",
        "sha256"
      ]
    },
    "translation": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "language_code": {
          "enum": [
            "en",
            "zh-CN",
            "es",
            "ar",
            "fr",
            "de"
          ]
        },
        "product": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "name": {
              "type": "string",
              "minLength": 1,
              "maxLength": 200
            }
          },
          "required": []
        },
        "raw_material": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "name": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            },
            "type": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            },
            "origin": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            },
            "description": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            }
          },
          "required": []
        },
        "process": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "step_key": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "label": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
              }
            },
            "required": [
              "step_key",
              "label"
            ]
          },
          "maxItems": 100
        },
        "packaging": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "description": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            },
            "inner_material": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            }
          },
          "required": []
        },
        "storage": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "conditions": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            },
            "shelf_life_description": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            }
          },
          "required": []
        },
        "manufacturer": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "name": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 500
                },
                {
                  "type": "null"
                }
              ]
            },
            "address": {
              "anyOf": [
                {
                  "type": "string",
                  "maxLength": 4000
                },
                {
                  "type": "null"
                }
              ]
            }
          },
          "required": []
        },
        "inspection": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "code": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
              },
              "specification": {
                "anyOf": [
                  {
                    "type": "string",
                    "maxLength": 2000
                  },
                  {
                    "type": "null"
                  }
                ]
              },
              "test_method": {
                "anyOf": [
                  {
                    "type": "string",
                    "maxLength": 500
                  },
                  {
                    "type": "null"
                  }
                ]
              },
              "result_display_text": {
                "anyOf": [
                  {
                    "type": "string",
                    "maxLength": 2000
                  },
                  {
                    "type": "null"
                  }
                ]
              }
            },
            "required": [
              "code"
            ]
          },
          "maxItems": 500
        },
        "certifications": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "key": {
                "type": "string",
                "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                "maxLength": 64
              },
              "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200
              },
              "issuer": {
                "anyOf": [
                  {
                    "type": "string",
                    "maxLength": 500
                  },
                  {
                    "type": "null"
                  }
                ]
              }
            },
            "required": [
              "key"
            ]
          },
          "maxItems": 100
        },
        "custom_sections": {
          "type": "array",
          "items": {
            "oneOf": [
              {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "key": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                    "maxLength": 64
                  },
                  "type": {
                    "const": "text"
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200
                  },
                  "content": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "text": {
                        "type": "string",
                        "maxLength": 10000
                      }
                    },
                    "required": [
                      "text"
                    ]
                  }
                },
                "required": [
                  "key",
                  "type",
                  "title",
                  "content"
                ]
              },
              {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "key": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                    "maxLength": 64
                  },
                  "type": {
                    "const": "key_value"
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200
                  },
                  "content": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "items": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "key": {
                              "type": "string",
                              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                              "maxLength": 64
                            },
                            "label": {
                              "type": "string",
                              "minLength": 1,
                              "maxLength": 200
                            },
                            "value": {
                              "type": "string",
                              "maxLength": 2000
                            }
                          },
                          "required": [
                            "key",
                            "label",
                            "value"
                          ]
                        },
                        "maxItems": 100
                      }
                    },
                    "required": [
                      "items"
                    ]
                  }
                },
                "required": [
                  "key",
                  "type",
                  "title",
                  "content"
                ]
              },
              {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "key": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                    "maxLength": 64
                  },
                  "type": {
                    "const": "table"
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200
                  },
                  "content": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "columns": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "key": {
                              "type": "string",
                              "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                              "maxLength": 64
                            },
                            "label": {
                              "type": "string",
                              "minLength": 1,
                              "maxLength": 200
                            }
                          },
                          "required": [
                            "key",
                            "label"
                          ]
                        },
                        "maxItems": 20
                      },
                      "rows": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "cells": {
                              "type": "array",
                              "items": {
                                "type": "string",
                                "maxLength": 2000
                              },
                              "maxItems": 20
                            }
                          },
                          "required": [
                            "cells"
                          ]
                        },
                        "maxItems": 200
                      }
                    },
                    "required": [
                      "columns",
                      "rows"
                    ]
                  }
                },
                "required": [
                  "key",
                  "type",
                  "title",
                  "content"
                ]
              },
              {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "key": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9_-]{1,64}(?![\\s\\S])",
                    "maxLength": 64
                  },
                  "type": {
                    "const": "asset_gallery"
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 200
                  },
                  "content": {
                    "type": "object",
                    "additionalProperties": false,
                    "properties": {
                      "caption": {
                        "type": "string",
                        "maxLength": 4000
                      }
                    },
                    "required": [
                      "caption"
                    ]
                  }
                },
                "required": [
                  "key",
                  "type",
                  "title",
                  "content"
                ]
              }
            ]
          },
          "maxItems": 100
        }
      },
      "required": [
        "language_code"
      ]
    }
  }
}
```

## 3. 完整测试示例

**TEST RECORD — NOT FOR COMMERCIAL USE**。以下只是 PF-TEST-001 的设计样例，publication 时间/版本是演示元数据，未发生实际发布；原料/工艺仅模板参考。生产/有效期、厂家、原产地、真实检测值及证书均未提供。认证名称只展示未核实模板条目，不代表持证。

没有真实图片/PDF，故 assets 与附件键为空，不编造文件、Hash 或下载地址。真实文件进入系统后必须由 Freeze Assets 生成有效 Hash、大小及路径，不能手填假资源通过验收。

```json
{
  "schema_version": "1.0",
  "record_type": "test",
  "notice": "TEST RECORD — NOT FOR COMMERCIAL USE",
  "product": {
    "code": "PF-STD",
    "name": "Potato Flakes",
    "category_code": null,
    "country_of_origin": null
  },
  "batch": {
    "code": "PF-TEST-001",
    "production_date": null,
    "expiry_date": null,
    "quality_status": "pending"
  },
  "raw_material": {
    "name": "Potato",
    "type": null,
    "origin": null,
    "description": "Template only; actual batch raw material information has not been supplied."
  },
  "process": [
    {
      "step_key": "receiving",
      "label": "Raw Potato Receiving"
    },
    {
      "step_key": "washing",
      "label": "Washing"
    },
    {
      "step_key": "peeling",
      "label": "Peeling"
    },
    {
      "step_key": "cooking",
      "label": "Cooking"
    },
    {
      "step_key": "mashing",
      "label": "Mashing"
    },
    {
      "step_key": "drum_drying",
      "label": "Drum Drying"
    },
    {
      "step_key": "flaking",
      "label": "Flaking"
    },
    {
      "step_key": "inspection",
      "label": "Inspection"
    },
    {
      "step_key": "packaging",
      "label": "Packaging"
    }
  ],
  "inspection": [
    {
      "code": "MOISTURE",
      "name": "Moisture",
      "value_type": "decimal",
      "numeric_value": null,
      "text_value": null,
      "unit": "%",
      "standard_value": null,
      "min_limit": null,
      "max_limit": null,
      "min_inclusive": true,
      "max_inclusive": true,
      "specification": null,
      "test_method": null,
      "judgement": "not_tested",
      "tested_on": null,
      "asset_keys": []
    }
  ],
  "certifications": [
    {
      "key": "halal",
      "name": "HALAL",
      "type": "HALAL",
      "certificate_number": null,
      "issuer": null,
      "valid_from": null,
      "valid_until": null,
      "status": "unverified",
      "asset_keys": []
    },
    {
      "key": "fssc_22000",
      "name": "FSSC 22000",
      "type": "FSSC_22000",
      "certificate_number": null,
      "issuer": null,
      "valid_from": null,
      "valid_until": null,
      "status": "unverified",
      "asset_keys": []
    }
  ],
  "packaging": {
    "quantity": null,
    "unit": null,
    "type_code": null,
    "description": null,
    "inner_material": null
  },
  "storage": {
    "conditions": null,
    "shelf_life_days": null,
    "shelf_life_description": null
  },
  "manufacturer": {
    "name": null,
    "address": null
  },
  "custom_sections": [
    {
      "key": "test_statement",
      "type": "text",
      "title": "Test record information",
      "content": {
        "text": "Reference template only. No commercial release, real COA, or certification claim is made."
      },
      "asset_keys": []
    }
  ],
  "assets": [],
  "localization": {
    "source_language": "en",
    "available_languages": [
      "en",
      "zh-CN"
    ],
    "translations": [
      {
        "language_code": "zh-CN",
        "product": {
          "name": "马铃薯雪花片"
        },
        "custom_sections": [
          {
            "key": "test_statement",
            "type": "text",
            "title": "测试记录说明",
            "content": {
              "text": "仅为参考模板；不代表真实商业发布、检测报告或认证声明。"
            }
          }
        ]
      }
    ]
  },
  "publication": {
    "version_number": 1,
    "issued_at": "2026-09-07T00:00:00.000Z",
    "kind": "publish",
    "source_version_number": null
  }
}
```

## 4. Schema 之外必须执行的语义检查

1. root product/batch code 与授权发布对象匹配，规范 ASCII 编码，拒绝尾换行及编码穿越；批次稳定码不可通过请求体替换。测试记录保持 TEST 段与强制测试提示；commercial 内容必须另经真实资料及商业规则验收。
2. production_date≤expiry_date、valid_from≤valid_until；检验真实日历。认证状态是发布时声明，静态端不得按后台最新认证动态改历史；当前日期提示如需要必须和历史声明分开显示。
3. numeric_value/min/max/standard 用精确十进制解析比较，min_limit≤max_limit；packaging.quantity 非空必须大于零；整数模式无小数，不使用 float 或词典序。小数规范去多余尾零/负零；pass/fail 有可核验结果和人工/规则判定依据，Schema 通过不代表合格。informational 必须有结果；pending 是待结果/待判定，不自动变 pass。
4. assets.key 唯一；路径目录前两位、文件名 Hash、sha256、MIME/扩展名、实际字节大小一致；冻结文件必须存在且 Hash 一致。所有 asset_keys 指向唯一资产，无重复键；无未引用资产（避免意外公开附件）。允许产品主图通过 assets.role=product_image 选择，最多一个；每个其他资产须由检测/认证/模块引用。
5. 数组 item_code/step_key/cert key/section key 唯一且顺序稳定；排序字段仅内部使用，公开数组已排好，不透传内部 sort/id。
6. section 的类型和 content 一致；key_value 的 key 唯一，table 列 key 唯一、每行 cells 数等于 columns 数。asset_gallery 的图片/附件来自 asset_keys；内容中不接受任意 path/html/script。自定义文字使用纯文本安全渲染，禁止 innerHTML。
7. localization.source_language 必须在 available_languages；translations 语言唯一、不重复源语言，语言集合必须与 available_languages 去掉源语言相等。译文不得增加源语言未公开的检测/认证/模块/步骤，或修改数字、单位、日期、Hash/路径/状态。按稳定 key 对齐；翻译表格/键值保持结构。缺译字段回退本 Snapshot 源语言，clear 字段不从模板恢复。
8. 顶层英语（或 source_language）数据加翻译覆盖只保存需翻译文字，不复制整套产品/批次业务数据。文字中没有假称认证或真实检测；示例的中文产品名并不意味着已经开发中文/六语言 UI。
9. publication.kind=rollback 时 source_version_number 为同批次已发布旧版本且小于新 version_number；业务 content_hash 与源一致。issued_at 是此次构建签发 UTC 时间，实际激活时间仅在私有 Publish Record 记录，不要求重写已冻结 JSON。
10. 数据库 payload_hash 不输出到自身 JSON；文件生成后计算并保存在私有版本记录/日志。Hash 不是签名，不能据此宣称数据真实或防止有权修改文件的人篡改。

## 5. 兼容与验证边界

T3 只对文档内 Schema/示例做离线结构校验和边界反例校验；不安装数据库、不执行迁移。Schema 不能代替文件实际存在性、权限、敏感内容审查、精确十进制逻辑或数据库不可变约束。旧 site 的 `record_updated`、产品/批次分离加载、固定英文标签和 TEST 质量状态不直接沿用到本契约；T11 显式做静态适配，并保留旧 POC。


## T9 本地实现说明（2026-09-10）

公开契约仍为 `schema_version = "1.0"`，上述 JSON Schema 未改。生产构建器内嵌相同 Schema，先严格解码（重复键、无效 UTF-8、深度/字节上限），再执行此固定契约全部已用关键字及语义校验；不是通用可加载外部 Schema 的解释器。另以现有 Ajv 6.15.0 对固定契约的共同关键字子集复验全部实际版本文件，只在校验副本中去掉其不识别的 2020-12 dialect 标记；不声称 Ajv 6 是通用 Draft 2020-12 验证器。

规范字节：键按 UTF-8/Unicode 码点顺序；数组保持经排序/校验的业务顺序；UTF-8、无 BOM、无尾换行、无多余空白；Go JSON 字符串转义固定（不转义 HTML 字符，U+2028/U+2029 保留 `\u2028`/`\u2029` 转义），业务纯文本另外拒绝 HTML 标记字符。精确小数保留字符串并规范前导/末尾零及负零；整数限制 JS 安全范围。不宣称 RFC 8785 全实现。

本轮发布子集比 Schema 更窄：只接收有界 PNG/JPEG 源图，输出去元数据 PNG；最多 16 个资产关联、单源/输出 2 MiB、宽高各 4096、像素不超过 1600 万；审核候选总计 4 MiB，公开 JSON 1 MiB。Schema 允许的 WebP/PDF 不等于本轮已有安全转换器。公共认证数组可为空；未开放认证关联不会悄悄省略后继续发布。
