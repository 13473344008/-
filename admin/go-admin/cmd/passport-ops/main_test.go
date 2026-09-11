package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestProductionConfigGuards(t *testing.T) {
	valid := `settings:
  application:
    mode: prod
    enabledp: true
  jwt:
    secret: 0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    timeout: 3600
  database:
    driver: sqlite3
    source: file:/data/db/passport.db?_foreign_keys=on&_journal_mode=WAL&_busy_timeout=5000&_synchronous=FULL
    maxOpenConns: 1
`
	tests := []struct {
		name, from, to string
		valid          bool
	}{{"valid", "", "", true}, {"dev", "mode: prod", "mode: dev", false}, {"disabled_scope", "enabledp: true", "enabledp: false", false}, {"weak_secret", "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", "go-admin", false}, {"excessive_expiry", "timeout: 3600", "timeout: 9999999", false}, {"foreign_keys_off", "_foreign_keys=on", "_foreign_keys=off", false}, {"multiple_connections", "maxOpenConns: 1", "maxOpenConns: 4", false}}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			text := valid
			if tc.from != "" {
				text = strings.Replace(text, tc.from, tc.to, 1)
			}
			p := filepath.Join(t.TempDir(), "settings.yml")
			if e := os.WriteFile(p, []byte(text), 0600); e != nil {
				t.Fatal(e)
			}
			if (checkConfig(p) == nil) != tc.valid {
				t.Fatal("guard mismatch")
			}
		})
	}
}
func TestCheckDoesNotCreateDatabase(t *testing.T) {
	p := filepath.Join(t.TempDir(), "absent.db")
	if execute([]string{"check", "--db", p}) == nil {
		t.Fatal("missing DB accepted")
	}
	if _, e := os.Stat(p); !os.IsNotExist(e) {
		t.Fatal("check created database")
	}
}
