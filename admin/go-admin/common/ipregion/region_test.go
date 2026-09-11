package ipregion

import (
	"os"
	"strings"
	"testing"
)

func TestPrivateAndInvalid(t *testing.T) {
	for _, ip := range []string{"127.0.0.1", "::1", "10.0.0.1", "192.168.1.1"} {
		if Lookup(ip) != "Local network" {
			t.Fatal(ip)
		}
	}
	if Lookup("not an IP") != "Unknown" {
		t.Fatal("invalid IP")
	}
}
func TestProxyTrust(t *testing.T) {
	t.Setenv("PASSPORT_TRUSTED_PROXIES", "")
	if ClientIP("127.0.0.1:1234", "1.1.1.1") != "127.0.0.1" {
		t.Fatal("spoofed header trusted")
	}
	t.Setenv("PASSPORT_TRUSTED_PROXIES", "127.0.0.0/8,10.0.0.0/8")
	if ClientIP("127.0.0.1:1234", "8.8.8.8, 1.1.1.1, 10.0.0.1") != "1.1.1.1" {
		t.Fatal("untrusted chain")
	}
	if ClientIP("127.0.0.1:1234", "bad") != "127.0.0.1" {
		t.Fatal("invalid header")
	}
}
func TestOfflineDatabase(t *testing.T) {
	if os.Getenv("PASSPORT_GEOIP_V4") == "" {
		t.Skip("requires explicitly configured offline databases")
	}
	if !Ready() {
		t.Fatal("database unavailable")
	}
	for _, ip := range []string{"1.1.1.1", "8.8.8.8", "240e:3b7:3272:d8d0:db09:c067:8d59:539e"} {
		got := Lookup(ip)
		if got == "Unknown" || strings.Contains(got, "|") {
			t.Fatal(ip, got)
		}
		t.Log(ip, got)
	}
	s := readers[true]
	mu.Lock()
	raw, _ := s.Search("1.1.1.1")
	mu.Unlock()
	t.Log("xdb raw format", raw)
}
