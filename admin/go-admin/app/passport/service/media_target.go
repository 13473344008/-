package service

import (
	"encoding/json"
	"go-admin/app/passport/service/dto"
	"gorm.io/gorm"
	"strings"
)

func validateMediaTarget(tx *gorm.DB, rid, sid, target string) error {
	if target == "" {
		return nil
	}
	if sid != "" {
		return invalid("模块图片不能指定其他内容位置")
	}
	switch target {
	case "raw_material_origin", "raw_material_description", "package_description", "storage_conditions":
		return nil
	}
	if strings.HasPrefix(target, "process:") {
		key := strings.TrimPrefix(target, "process:")
		var raw string
		if e := tx.Table("product_revisions").Select("process_steps").Where("id=?", rid).Scan(&raw).Error; e != nil {
			return e
		}
		var steps []dto.Step
		if e := json.Unmarshal([]byte(raw), &steps); e != nil {
			return e
		}
		for _, step := range steps {
			if step.StepKey == key {
				return nil
			}
		}
	}
	return invalid("图片位置无效，请先保存对应工艺步骤")
}
