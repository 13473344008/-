package service

import (
	"github.com/go-admin-team/go-admin-core/v2/sdk/config"
	"go-admin/common/actions"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestVisitFilter(t *testing.T) {
	tests := []struct {
		line string
		ok   bool
	}{
		{`127.0.0.1 - - [11/Sep/2026:13:00:00 +0800] "GET /b/TEST-001 HTTP/1.1" 200 1 "-" "browser"`, true},
		{`::1 - - [11/Sep/2026:13:00:00 +0800] "GET /b/TEST-001/v/2?lang=ar HTTP/1.1" 304 0 "-" "browser"`, true},
		{`127.0.0.1 - - [11/Sep/2026:13:00:00 +0800] "GET /assets/x.png HTTP/1.1" 200 1`, false},
		{`127.0.0.1 - - [11/Sep/2026:13:00:00 +0800] "GET /b/MISSING HTTP/1.1" 404 1`, false},
		{`127.0.0.1 - - [11/Sep/2026:13:00:00 +0800] "POST /b/TEST HTTP/1.1" 200 1`, false},
		{`127.0.0.1 - - [11/Sep/2026:13:00:00 +0800] "GET /b/%2e%2e HTTP/1.1" 200 1`, false},
		{`127.0.0.1 - - [bad] "GET /b/TEST HTTP/1.1" 200 1`, false}}
	for _, x := range tests {
		row, _, ok := parseVisit(x.line)
		if ok != x.ok {
			t.Fatal(x.line, ok)
		}
		if ok && row.VisitedAt != "2026-09-11T05:00:00Z" {
			t.Fatal(row)
		}
	}
}

func TestTrafficScopeAndAvailability(t *testing.T) {
	d, e := gorm.Open(sqlite.Open(":memory:"), &gorm.Config{})
	if e != nil {
		t.Fatal(e)
	}
	pool, _ := d.DB()
	pool.SetMaxOpenConns(1)
	defer pool.Close()
	for _, sql := range []string{"CREATE TABLE products(id TEXT,product_code TEXT,created_by INTEGER)", "CREATE TABLE batches(batch_code TEXT,product_id TEXT)", "INSERT INTO products VALUES('p1','ONE',1),('p2','TWO',2)", "INSERT INTO batches VALUES('B1','p1'),('B2','p2')"} {
		if e := d.Exec(sql).Error; e != nil {
			t.Fatal(e)
		}
	}
	before := config.ApplicationConfig.EnableDP
	config.ApplicationConfig.EnableDP = true
	defer func() { config.ApplicationConfig.EnableDP = before }()
	path := filepath.Join(t.TempDir(), "access.log")
	when := time.Now().Format("02/Jan/2006:15:04:05 -0700")
	raw := "127.0.0.1 - - [" + when + "] \"GET /b/B1 HTTP/1.1\" 200 1\n127.0.0.1 - - [" + when + "] \"GET /b/B2 HTTP/1.1\" 200 1\n"
	if e := os.WriteFile(path, []byte(raw), 0600); e != nil {
		t.Fatal(e)
	}
	t.Setenv("PASSPORT_ACCESS_LOG", path)
	s := Traffic{}
	s.Orm = d
	s.Actor = 1
	s.Permission = &actions.DataPermission{UserId: 1, DataScope: "5"}
	v, e := s.Read(TrafficQuery{})
	if e != nil || v.Count != 1 || v.List[0].BatchCode != "B1" {
		t.Fatal(v, e)
	}
	s.Permission = nil
	v, e = s.Read(TrafficQuery{})
	if e != nil || v.Count != 0 {
		t.Fatal("unscoped disclosure", v, e)
	}
	s.Admin = true
	v, e = s.Read(TrafficQuery{PageIndex: 2, PageSize: 1})
	if e != nil || v.Count != 2 || len(v.List) != 1 {
		t.Fatal("pagination", v, e)
	}
	t.Setenv("PASSPORT_ACCESS_LOG", path+"missing")
	v, e = s.Read(TrafficQuery{})
	if e != nil || v.Available {
		t.Fatal("missing log must not pretend zero", v, e)
	}
}
