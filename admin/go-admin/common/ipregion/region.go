// Package ipregion resolves coarse locations locally; it never calls a remote API.
package ipregion

import (
	"go-admin/internal/ip2region/xdb"
	"net"
	"net/netip"
	"os"
	"strings"
	"sync"
)

var once sync.Once
var mu sync.Mutex
var readers = map[bool]*xdb.Searcher{}

func initReaders() {
	for _, v := range []struct {
		name    string
		version *xdb.Version
		ipv4    bool
	}{{"PASSPORT_GEOIP_V4", xdb.IPv4, true}, {"PASSPORT_GEOIP_V6", xdb.IPv6, false}} {
		p := os.Getenv(v.name)
		if p == "" {
			continue
		}
		if xdb.VerifyFromFile(p) != nil {
			continue
		}
		s, e := xdb.NewWithFileOnly(v.version, p)
		if e == nil {
			readers[v.ipv4] = s
		}
	}
}
func Ready() bool { once.Do(initReaders); return len(readers) > 0 }
func Lookup(ip string) string {
	a, e := netip.ParseAddr(ip)
	if e != nil {
		return "Unknown"
	}
	a = a.Unmap()
	if a.IsLoopback() || a.IsPrivate() || a.IsLinkLocalUnicast() {
		return "Local network"
	}
	if !a.IsGlobalUnicast() {
		return "Unknown"
	}
	once.Do(initReaders)
	s := readers[a.Is4()]
	if s == nil {
		return "Unknown"
	}
	mu.Lock()
	region, e := s.Search(a.String())
	mu.Unlock()
	if e != nil {
		return "Unknown"
	}
	fields := strings.Split(region, "|")
	out := []string{}
	seen := map[string]bool{}
	// Database format: country | province | city | ISP | country code.
	for i, v := range fields {
		if i >= 3 {
			break
		}
		v = strings.TrimSpace(v)
		if v != "" && v != "0" && !seen[v] {
			out = append(out, v)
			seen[v] = true
		}
	}
	if len(out) == 0 {
		return "Unknown"
	}
	return strings.Join(out, " / ")
}

// Proxy headers are ignored unless the immediate peer is explicitly trusted.
func ClientIP(remote, forwarded string) string {
	host, _, e := net.SplitHostPort(remote)
	if e != nil {
		host = remote
	}
	peer, e := netip.ParseAddr(host)
	if e != nil {
		return ""
	}
	peer = peer.Unmap()
	trusted := func(a netip.Addr) bool {
		for _, s := range strings.Split(os.Getenv("PASSPORT_TRUSTED_PROXIES"), ",") {
			p, e := netip.ParsePrefix(strings.TrimSpace(s))
			if e == nil && p.Contains(a) {
				return true
			}
		}
		return false
	}
	if !trusted(peer) || len(forwarded) > 2048 {
		return peer.String()
	}
	parts := strings.Split(forwarded, ",")
	for i := len(parts) - 1; i >= 0; i-- {
		a, e := netip.ParseAddr(strings.TrimSpace(parts[i]))
		if e != nil {
			return peer.String()
		}
		a = a.Unmap()
		if !trusted(a) {
			return a.String()
		}
	}
	return peer.String()
}
