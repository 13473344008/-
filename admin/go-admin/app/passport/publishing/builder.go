package publishing

import (
	"fmt"
	"sort"
)

const BuilderVersion = "public-json-v1.0.0"

type BuildResult struct {
	Payload                  []byte
	PayloadHash, ContentHash string
	Assets                   []map[string]interface{}
}

// Build reads only the frozen review input. Every output field is named in this whitelist.
// It never receives an ORM, working batch, URL, or user-supplied public payload.
func Build(frozen []byte, version int64, issued string) (BuildResult, error) {
	result := BuildResult{}
	v, e := Decode(frozen)
	if e != nil {
		return result, e
	}
	c := obj(v)
	if c["schema"] != "review-v1" && c["schema"] != "review-v2" {
		return result, fmt.Errorf("unsupported frozen review schema")
	}
	batch, base := obj(c["batch"]), obj(c["base"])
	source := str(obj(base["content"])["source_language"])
	fields := map[string]interface{}{}
	for _, v := range arr(c["effective"]) {
		f := obj(v)
		fields[str(f["field_key"])] = f["value"]
	}
	p := core(fields)
	p["schema_version"] = FrozenSchemaVersion(frozen)
	p["record_type"] = batch["record_type"]
	p["notice"] = nil
	if batch["record_type"] == "test" {
		p["notice"] = "TEST RECORD — NOT FOR COMMERCIAL USE"
	}
	obj(p["product"])["code"] = c["product_code"]
	bc := obj(batch["content"])
	p["batch"] = map[string]interface{}{"code": batch["batch_code"], "production_date": bc["production_date"], "expiry_date": bc["expiry_date"], "quality_status": bc["quality_status"]}
	p["inspection"] = []interface{}{}
	p["certifications"] = []interface{}{}
	p["custom_sections"] = []interface{}{}
	p["assets"] = []interface{}{}
	byOwner := map[string][]interface{}{}
	assets := []map[string]interface{}{}
	for _, v := range arr(c["assets"]) {
		a := obj(v)
		if a["publish"] != true {
			continue
		}
		hash := str(a["normalized_sha256"])
		if len(hash) != 64 {
			return result, fmt.Errorf("invalid approved asset hash")
		}
		out := map[string]interface{}{"key": a["asset_key"], "role": a["asset_role"], "label": a["public_label"], "path": "assets/sha256/" + hash[:2] + "/" + hash + ".png", "mime_type": "image/png", "file_size": a["normalized_size"], "sha256": hash}
		if target := str(a["display_target"]); target != "" {
			out["display_target"] = target
		}
		assets = append(assets, out)
		owner := str(a["owner_id"])
		byOwner[owner] = append(byOwner[owner], a["asset_key"])
	}
	sort.Slice(assets, func(i, j int) bool { return str(assets[i]["key"]) < str(assets[j]["key"]) })
	for _, a := range assets {
		p["assets"] = append(arr(p["assets"]), a)
	}
	result.Assets = assets
	keys := func(id string) []interface{} {
		if a := byOwner[id]; a != nil {
			return a
		}
		return []interface{}{}
	}
	inspectionIDs := map[string]string{}
	inspections := append([]interface{}{}, arr(c["inspections"])...)
	sort.SliceStable(inspections, func(i, j int) bool {
		a, b := obj(inspections[i]), obj(inspections[j])
		if intValue(a["sort_order"]) == intValue(b["sort_order"]) {
			return str(a["item_code"]) < str(b["item_code"])
		}
		return intValue(a["sort_order"]) < intValue(b["sort_order"])
	})
	for _, v := range inspections {
		i := obj(v)
		if i["is_public"] != true {
			continue
		}
		out := map[string]interface{}{"code": i["item_code"], "asset_keys": keys(str(i["id"]))}
		for _, k := range []string{"name", "value_type", "numeric_value", "text_value", "unit", "standard_value", "min_limit", "max_limit", "min_inclusive", "max_inclusive", "specification", "test_method", "judgement", "tested_on"} {
			out[k] = i[k]
		}
		for _, k := range []string{"numeric_value", "standard_value", "min_limit", "max_limit"} {
			if out[k] != nil {
				out[k] = Decimal(str(out[k]))
			}
		}
		p["inspection"] = append(arr(p["inspection"]), out)
		inspectionIDs[str(i["id"])] = str(i["item_code"])
	}
	sectionIDs := map[string]string{}
	for _, v := range arr(c["effective_sections"]) {
		s := obj(v)
		if s["is_public"] != true {
			continue
		}
		out := map[string]interface{}{"key": s["section_key"], "type": s["section_type"], "title": s["title"], "content": sectionContent(str(s["section_type"]), obj(s["content"])), "asset_keys": keys(str(s["section_id"]))}
		p["custom_sections"] = append(arr(p["custom_sections"]), out)
		sectionIDs[str(s["section_id"])] = str(s["section_key"])
	}
	langs := map[string]bool{}
	for _, group := range []string{"override_translations", "inspection_translations"} {
		for _, v := range arr(c[group]) {
			t := obj(v)
			if t["translation_status"] == "approved" {
				langs[str(t["language_code"])] = true
			}
		}
	}
	for _, v := range arr(base["translations"]) {
		t := obj(v)
		if t["translation_status"] == "approved" {
			langs[str(t["language_code"])] = true
		}
	}
	sections := append(append([]interface{}{}, arr(c["base_sections"])...), arr(c["batch_sections"])...)
	for _, v := range sections {
		s := obj(v)
		if sectionIDs[str(s["id"])] == "" {
			continue
		}
		for _, v := range arr(s["translations"]) {
			t := obj(v)
			if t["translation_status"] == "approved" {
				langs[str(t["language_code"])] = true
			}
		}
	}
	delete(langs, source)
	ordered := []string{}
	for l := range langs {
		ordered = append(ordered, l)
	}
	sort.Strings(ordered)
	trs := []interface{}{}
	available := []interface{}{source}
	for _, lang := range ordered {
		f := map[string]interface{}{}
		for k, v := range fields {
			f[k] = v
		}
		for _, v := range arr(base["translations"]) {
			t := obj(v)
			if t["language_code"] != lang || t["translation_status"] != "approved" {
				continue
			}
			for _, k := range textFields {
				if t[k] != nil && t[k] != "" {
					f[k] = t[k]
				}
			}
			steps := []interface{}{}
			for _, v := range arr(fields["process"]) {
				s := obj(v)
				label := s["label"]
				if x := obj(t["process_labels"])[str(s["step_key"])]; x != nil {
					label = x
				}
				steps = append(steps, map[string]interface{}{"step_key": s["step_key"], "label": label})
			}
			f["process"] = steps
		}
		// Overrides win even when their translation is absent. A clear never falls back to the template.
		for _, v := range arr(c["overrides"]) {
			o := obj(v)
			k := str(o["field_key"])
			f[k] = fields[k]
			if o["operation"] == "clear" {
				continue
			}
			for _, v := range arr(c["override_translations"]) {
				t := obj(v)
				if t["batch_override_id"] != o["id"] || t["language_code"] != lang || t["translation_status"] != "approved" {
					continue
				}
				if t["translated_value"] != nil {
					f[k] = t["translated_value"]
				}
				if k == "process" && t["translated_process"] != nil {
					labels, e := Decode([]byte(str(t["translated_process"])))
					if e != nil {
						return result, e
					}
					steps := []interface{}{}
					for _, v := range arr(fields["process"]) {
						step := obj(v)
						label := step["label"]
						if x := obj(labels)[str(step["step_key"])]; x != nil {
							label = x
						}
						steps = append(steps, map[string]interface{}{"step_key": step["step_key"], "label": label})
					}
					f[k] = steps
				}
			}
		}
		tr := core(f)
		delete(obj(tr["product"]), "category_code")
		delete(obj(tr["product"]), "country_of_origin")
		for _, k := range []string{"quantity", "unit", "type_code"} {
			delete(obj(tr["packaging"]), k)
		}
		delete(obj(tr["storage"]), "shelf_life_days")
		tr["language_code"] = lang
		ti := []interface{}{}
		for _, v := range arr(c["inspection_translations"]) {
			t := obj(v)
			code := inspectionIDs[str(t["inspection_item_id"])]
			if code == "" || t["language_code"] != lang || t["translation_status"] != "approved" {
				continue
			}
			out := map[string]interface{}{"code": code, "name": t["display_name"]}
			for _, k := range []string{"specification", "test_method", "result_display_text"} {
				out[k] = t[k]
			}
			ti = append(ti, out)
		}
		sort.Slice(ti, func(i, j int) bool { return str(obj(ti[i])["code"]) < str(obj(ti[j])["code"]) })
		if len(ti) > 0 {
			tr["inspection"] = ti
		}
		ts := []interface{}{}
		for _, v := range sections {
			s := obj(v)
			key := sectionIDs[str(s["id"])]
			if key == "" {
				continue
			}
			for _, v := range arr(s["translations"]) {
				t := obj(v)
				if t["language_code"] == lang && t["translation_status"] == "approved" {
					ts = append(ts, map[string]interface{}{"key": key, "type": s["section_type"], "title": t["title"], "content": sectionContent(str(s["section_type"]), obj(t["content"]))})
				}
			}
		}
		sort.Slice(ts, func(i, j int) bool { return str(obj(ts[i])["key"]) < str(obj(ts[j])["key"]) })
		if len(ts) > 0 {
			tr["custom_sections"] = ts
		}
		trs = append(trs, tr)
		available = append(available, lang)
	}
	p["localization"] = map[string]interface{}{"source_language": source, "available_languages": available, "translations": trs}
	business, e := Canonical(p)
	if e != nil {
		return result, e
	}
	result.ContentHash = Hash(business)
	p["publication"] = map[string]interface{}{"version_number": version, "issued_at": issued, "kind": "publish", "source_version_number": nil}
	result.Payload, e = Canonical(p)
	if e != nil {
		return result, e
	}
	if e = ValidatePayload(result.Payload); e != nil {
		return result, e
	}
	result.PayloadHash = Hash(result.Payload)
	return result, nil
}

var textFields = []string{"product_name", "raw_material_name", "raw_material_type", "raw_material_origin", "raw_material_description", "package_description", "inner_material", "storage_conditions", "shelf_life_description", "manufacturer_name", "manufacturer_address"}

func core(f map[string]interface{}) map[string]interface{} {
	q := f["package_quantity"]
	if q != nil {
		q = Decimal(str(q))
	}
	process := f["process"]
	if process == nil {
		process = []interface{}{}
	}
	return map[string]interface{}{
		"product":      map[string]interface{}{"name": f["product_name"], "category_code": f["category_code"], "country_of_origin": f["origin_country_code"]},
		"raw_material": map[string]interface{}{"name": f["raw_material_name"], "type": f["raw_material_type"], "origin": f["raw_material_origin"], "description": f["raw_material_description"]}, "process": process,
		"packaging": map[string]interface{}{"quantity": q, "unit": f["package_unit"], "type_code": f["package_type_code"], "description": f["package_description"], "inner_material": f["inner_material"]},
		"storage":   map[string]interface{}{"conditions": f["storage_conditions"], "shelf_life_days": f["shelf_life_days"], "shelf_life_description": f["shelf_life_description"]}, "manufacturer": map[string]interface{}{"name": f["manufacturer_name"], "address": f["manufacturer_address"]}}
}
func intValue(v interface{}) int64 { r := ratString(fmt.Sprint(v)); return r }
func ratString(s string) int64     { var n int64; fmt.Sscan(s, &n); return n }

// Structured module content is reconstructed, never passed through from an ORM/JSON blob.
func sectionContent(kind string, c map[string]interface{}) map[string]interface{} {
	out := map[string]interface{}{}
	switch kind {
	case "text":
		out["text"] = c["text"]
	case "asset_gallery":
		out["caption"] = c["caption"]
	case "key_value":
		a := []interface{}{}
		for _, v := range arr(c["items"]) {
			i := obj(v)
			a = append(a, map[string]interface{}{"key": i["key"], "label": i["label"], "value": i["value"]})
		}
		out["items"] = a
	case "table":
		a := []interface{}{}
		for _, v := range arr(c["columns"]) {
			i := obj(v)
			a = append(a, map[string]interface{}{"key": i["key"], "label": i["label"]})
		}
		out["columns"] = a
		rows := []interface{}{}
		for _, v := range arr(c["rows"]) {
			rows = append(rows, map[string]interface{}{"cells": obj(v)["cells"]})
		}
		out["rows"] = rows
	}
	return out
}

// Old frozen inputs keep their original schema, payload and hash on retry.
func FrozenSchemaVersion(frozen []byte) string {
	v, e := Decode(frozen)
	if e != nil {
		return "1.0"
	}
	for _, a := range arr(obj(v)["assets"]) {
		if str(obj(a)["display_target"]) != "" && obj(a)["publish"] == true {
			return "1.1"
		}
	}
	return "1.0"
}
