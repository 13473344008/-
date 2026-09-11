// T6 read-only restart probe; only the explicitly named local T6 database is opened.
package main

import (
	"encoding/json"
	"fmt"
	"go-admin/app/passport/service"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"os"
	"path/filepath"
	"reflect"
	"time"
)

func main() {
	root := os.Args[1]
	dbpath := filepath.Join(root, "db/passport-admin-t6.db")
	raw, e := os.ReadFile(filepath.Join(root, "test-artifacts/browser-fixtures.json"))
	if e != nil {
		panic(e)
	}
	var fixture struct {
		C      string      `json:"c"`
		Detail interface{} `json:"detail"`
	}
	if e = json.Unmarshal(raw, &fixture); e != nil {
		panic(e)
	}
	db, e := gorm.Open(sqlite.Open("file:"+dbpath+"?mode=ro&_foreign_keys=on&_busy_timeout=5000"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if e != nil {
		panic(e)
	}
	pool, _ := db.DB()
	defer pool.Close()
	pool.SetMaxOpenConns(1)
	s := service.Batches{Products: service.Products{Actor: 1, Admin: true}}
	s.Orm = db
	v, e := s.GetBatch(fixture.C, "")
	if e != nil {
		panic(e)
	}
	raw, e = json.Marshal(v)
	if e != nil {
		panic(e)
	}
	var result interface{}
	if e = json.Unmarshal(raw, &result); e != nil {
		panic(e)
	}
	checks := []map[string]interface{}{}
	check := func(name string, ok bool) {
		status := "PASS"
		if !ok {
			status = "FAIL"
		}
		checks = append(checks, map[string]interface{}{"name": name, "status": status, "time": time.Now().UTC().Format(time.RFC3339Nano), "method": "read-only Go service after actual HTTP backend restart"})
	}
	check("Browser-created complete aggregate and resolver unchanged after backend restart", reflect.DeepEqual(result, fixture.Detail))
	for _, key := range []string{"t6_none", "t6_owner", "t6_view"} {
		var n int64
		if e = db.Table("sys_role").Where("role_key=? AND deleted_at=0", key).Count(&n).Error; e != nil {
			panic(e)
		}
		check("Test role persists "+key, n == 1)
	}
	var n int64
	if e = db.Table("casbin_rule").Where("v0=? AND v1 LIKE ?", "t6_owner", "/api/v1/passport-batches%").Count(&n).Error; e != nil {
		panic(e)
	}
	check("Owner batch Casbin grants persist", n == 5)
	if e = db.Table("casbin_rule").Where("v0=? AND v1 LIKE ?", "t6_none", "/api/v1/passport-batches%").Count(&n).Error; e != nil {
		panic(e)
	}
	check("Ungrant role has no batch policy after restart", n == 0)
	raw, _ = json.MarshalIndent(checks, "", "  ")
	fmt.Println(string(raw))
	for _, c := range checks {
		if c["status"] != "PASS" {
			os.Exit(1)
		}
	}
}
