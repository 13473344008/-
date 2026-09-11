// T4 technical probe only. Uses the same GORM SQLite driver as upstream runtime.
package main

import (
	"encoding/json"
	"fmt"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/driver/sqlite"
	"gorm.io/gorm"
	"os"
)

func main() {
	path := os.Args[1]
	db, e := gorm.Open(sqlite.Open("file:"+path+"?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL"), &gorm.Config{})
	if e != nil {
		panic(e)
	}
	sql, e := db.DB()
	if e != nil {
		panic(e)
	}
	sql.SetMaxOpenConns(1)
	defer sql.Close()
	if len(os.Args) > 2 {
		b, e := os.ReadFile(os.Args[2])
		if e != nil {
			panic(e)
		}
		var c map[string]string
		if e = json.Unmarshal(b, &c); e != nil {
			panic(e)
		}
		h, e := bcrypt.GenerateFromPassword([]byte(c["admin_password"]), bcrypt.DefaultCost)
		if e != nil {
			panic(e)
		}
		if e = db.Exec("UPDATE sys_user SET password=? WHERE user_id=1", string(h)).Error; e != nil {
			panic(e)
		}
	}
	out := map[string]interface{}{}
	for _, p := range []string{"foreign_keys", "journal_mode", "busy_timeout", "synchronous"} {
		var v string
		if e = db.Raw("PRAGMA " + p).Scan(&v).Error; e != nil {
			panic(e)
		}
		out[p] = v
	}
	var v string
	db.Raw("select sqlite_version()").Scan(&v)
	out["sqlite_version"] = v
	b, _ := json.Marshal(out)
	fmt.Println(string(b))
}
