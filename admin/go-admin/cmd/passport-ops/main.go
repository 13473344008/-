// passport-ops is an offline utility: it has no HTTP listener and never prints secrets.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"go.yaml.in/yaml/v3"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

func execute(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("use bootstrap or check")
	}
	if args[0] == "probe" {
		client := http.Client{Timeout: 4 * time.Second}
		response, err := client.Get("http://127.0.0.1:8000/api/v1/app-config")
		if err != nil {
			return fmt.Errorf("API unavailable")
		}
		defer response.Body.Close()
		var body struct {
			Code int `json:"code"`
		}
		if response.StatusCode != 200 || json.NewDecoder(io.LimitReader(response.Body, 65536)).Decode(&body) != nil || body.Code != 200 {
			return fmt.Errorf("API/database not ready")
		}
		return nil
	}
	f := flag.NewFlagSet(args[0], flag.ContinueOnError)
	configPath := f.String("config", "", "production configuration")
	dbpath := f.String("db", "", "existing migrated SQLite database")
	passwordFile := f.String("password-file", "", "private initial password file; bootstrap only")
	if err := f.Parse(args[1:]); err != nil {
		return err
	}
	if args[0] == "check-config" {
		return checkConfig(*configPath)
	}
	if args[0] != "bootstrap" && args[0] != "check" {
		return fmt.Errorf("unknown command")
	}
	if st, err := os.Lstat(*dbpath); err != nil || !st.Mode().IsRegular() {
		return fmt.Errorf("database must be an existing regular file")
	}
	mode := "ro"
	if args[0] == "bootstrap" {
		mode = "rw"
	}
	db, err := gorm.Open(sqlite.Open("file:"+*dbpath+"?mode="+mode+"&_foreign_keys=on&_busy_timeout=5000"), &gorm.Config{Logger: logger.Default.LogMode(logger.Silent)})
	if err != nil {
		return fmt.Errorf("cannot open database")
	}
	pool, _ := db.DB()
	defer pool.Close()
	pool.SetMaxOpenConns(1)
	var integrity string
	if err = db.Raw("PRAGMA integrity_check").Scan(&integrity).Error; err != nil || integrity != "ok" {
		return fmt.Errorf("database integrity check failed")
	}
	var fk []map[string]interface{}
	if err = db.Raw("PRAGMA foreign_key_check").Scan(&fk).Error; err != nil || len(fk) != 0 {
		return fmt.Errorf("database foreign key check failed")
	}
	var migrations int64
	if err = db.Table("sys_migration").Count(&migrations).Error; err != nil || migrations < 18 {
		return fmt.Errorf("required database migrations missing")
	}
	if args[0] == "bootstrap" {
		st, err := os.Lstat(*passwordFile)
		if err != nil || !st.Mode().IsRegular() || st.Mode().Perm()&0077 != 0 {
			return fmt.Errorf("password file must be regular and accessible only by owner")
		}
		raw, err := os.ReadFile(*passwordFile)
		if err != nil {
			return fmt.Errorf("cannot read password file")
		}
		password := strings.TrimRight(string(raw), "\r\n")
		if len(password) < 16 || len(password) > 72 {
			return fmt.Errorf("initial password must be 16–72 bytes")
		}
		hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
		if err != nil {
			return err
		}
		err = db.Transaction(func(tx *gorm.DB) error {
			for _, table := range []string{"products", "batches", "passport_revisions"} {
				var n int64
				if e := tx.Table(table).Count(&n).Error; e != nil {
					return e
				}
				if n != 0 {
					return fmt.Errorf("bootstrap only accepts a fresh empty business database")
				}
			}
			var users int64
			if e := tx.Table("sys_user").Count(&users).Error; e != nil {
				return e
			}
			if users != 1 {
				return fmt.Errorf("bootstrap requires exactly the initial admin account")
			}
			var admin struct {
				UserID   int
				Password string
			}
			if e := tx.Table("sys_user").Where("username='admin' AND user_id=1").Take(&admin).Error; e != nil {
				return e
			}
			if bcrypt.CompareHashAndPassword([]byte(admin.Password), []byte("123456")) != nil {
				return fmt.Errorf("initial admin has already been configured; refusing password reset")
			}
			q := tx.Table("sys_user").Where("user_id=1 AND password=?", admin.Password).Update("password", string(hash))
			if q.Error != nil {
				return q.Error
			}
			if q.RowsAffected != 1 {
				return fmt.Errorf("bootstrap conflict")
			}
			return nil
		})
		if err != nil {
			return err
		}
	}
	var users []struct {
		Username string
		Password string
	}
	if err = db.Table("sys_user").Where("status='2' AND deleted_at=0").Select("username,password").Find(&users).Error; err != nil {
		return err
	}
	if len(users) == 0 {
		return fmt.Errorf("no enabled accounts")
	}
	for _, u := range users {
		if strings.HasPrefix(u.Username, "t12-") || bcrypt.CompareHashAndPassword([]byte(u.Password), []byte("123456")) == nil {
			return fmt.Errorf("enabled test account or default password detected")
		}
	}
	var admins int64
	if err = db.Table("sys_user u").Joins("JOIN sys_role r ON r.role_id=u.role_id").Where("u.status='2' AND u.deleted_at=0 AND r.role_key='admin' AND r.status='2' AND r.deleted_at=0").Count(&admins).Error; err != nil || admins == 0 {
		return fmt.Errorf("no enabled administrator")
	}
	fmt.Println("PASS: migrations, database integrity and initial account checks")
	return nil
}
func main() {
	if err := execute(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func checkConfig(path string) error {
	raw, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("cannot read production configuration")
	}
	var c struct {
		Settings struct {
			Application struct {
				Mode     string
				Enabledp bool
			}
			JWT struct {
				Secret  string
				Timeout int
			}
			Database struct {
				Driver       string
				Source       string
				MaxOpenConns int `yaml:"maxOpenConns"`
			}
		}
	}
	if yaml.Unmarshal(raw, &c) != nil {
		return fmt.Errorf("invalid configuration")
	}
	s := c.Settings
	if s.Application.Mode != "prod" || !s.Application.Enabledp || len(s.JWT.Secret) < 32 || strings.Contains(s.JWT.Secret, "REPLACE") || s.JWT.Timeout < 60 || s.JWT.Timeout > 86400 {
		return fmt.Errorf("production mode, data permissions and a unique strong JWT secret/expiry are required")
	}
	if s.Database.Driver != "sqlite3" || s.Database.MaxOpenConns != 1 {
		return fmt.Errorf("this deployment requires single-writer SQLite")
	}
	for _, part := range []string{"_foreign_keys=on", "_journal_mode=WAL", "_busy_timeout=5000", "_synchronous=FULL"} {
		if !strings.Contains(s.Database.Source, part) {
			return fmt.Errorf("SQLite safety options missing")
		}
	}
	return nil
}
