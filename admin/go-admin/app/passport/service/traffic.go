package service

import (
	"bufio"
	"go-admin/common/ipregion"
	"io"
	"net/url"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

type Traffic struct{ Products }
type TrafficQuery struct {
	BatchCode string `form:"batch_code"`
	Days      int    `form:"days"`
	PageIndex int    `form:"pageIndex"`
	PageSize  int    `form:"pageSize"`
}
type VisitRow struct {
	ID          string `json:"id"`
	BatchCode   string `json:"batch_code"`
	ProductCode string `json:"product_code"`
	VisitedAt   string `json:"visited_at"`
	Region      string `json:"region"`
	Version     string `json:"version"`
}
type TrafficBucket struct {
	Name  string `json:"name"`
	Count int    `json:"count"`
}
type TrafficResult struct {
	List        []VisitRow      `json:"list"`
	Count       int             `json:"count"`
	Regions     []TrafficBucket `json:"regions"`
	Batches     []TrafficBucket `json:"batches"`
	Available   bool            `json:"available"`
	Truncated   bool            `json:"truncated"`
	GeoReady    bool            `json:"geo_ready"`
	WindowStart string          `json:"window_start"`
	ReadAt      string          `json:"read_at"`
}

var accessLine = regexp.MustCompile(`^(\S+) \S+ \S+ \[([^\]]+)\] "GET ([^ ]+) HTTP/[^" ]+" (200|304) `)
var batchVisit = regexp.MustCompile(`^/b/([A-Za-z0-9_-]{1,64})(?:/v/([1-9][0-9]{0,15}))?$`)

const trafficBytes int64 = 16 * 1024 * 1024

func parseVisit(line string) (VisitRow, string, bool) {
	m := accessLine.FindStringSubmatch(line)
	if m == nil {
		return VisitRow{}, "", false
	}
	u, e := url.ParseRequestURI(m[3])
	if e != nil || u.RawPath != "" {
		return VisitRow{}, "", false
	}
	p := batchVisit.FindStringSubmatch(u.Path)
	if p == nil {
		return VisitRow{}, "", false
	}
	t, e := time.Parse("02/Jan/2006:15:04:05 -0700", m[2])
	if e != nil {
		return VisitRow{}, "", false
	}
	return VisitRow{BatchCode: p[1], Version: p[2], VisitedAt: t.UTC().Format(time.RFC3339)}, m[1], true
}
func buckets(m map[string]int) []TrafficBucket {
	v := []TrafficBucket{}
	for k, n := range m {
		v = append(v, TrafficBucket{k, n})
	}
	sort.Slice(v, func(i, j int) bool {
		if v[i].Count == v[j].Count {
			return v[i].Name < v[j].Name
		}
		return v[i].Count > v[j].Count
	})
	return v
}
func (s *Traffic) Read(q TrafficQuery) (TrafficResult, error) {
	now := time.Now().UTC()
	out := TrafficResult{List: []VisitRow{}, Regions: []TrafficBucket{}, Batches: []TrafficBucket{}, ReadAt: now.Format(time.RFC3339), GeoReady: ipregion.Ready()}
	if q.Days == 0 {
		q.Days = 7
	}
	if q.Days < 1 || q.Days > 90 || len(q.BatchCode) > 64 {
		return out, invalid("查询范围不正确")
	}
	if q.PageIndex < 1 {
		q.PageIndex = 1
	}
	if q.PageSize < 1 {
		q.PageSize = 20
	}
	if q.PageSize > 100 {
		q.PageSize = 100
	}
	if q.PageIndex > 100000 {
		return out, invalid("页码过大")
	}
	since := now.Add(-time.Duration(q.Days) * 24 * time.Hour)
	out.WindowStart = since.Format(time.RFC3339)
	// Reuse product data scope so traffic cannot disclose another owner's batch.
	var allowed []struct {
		BatchCode   string
		ProductCode string
	}
	sub := s.scope(s.Orm).Select("products.id")
	if e := s.Orm.Table("batches b").Joins("JOIN products p ON p.id=b.product_id").Where("b.product_id IN (?)", sub).Select("b.batch_code,p.product_code").Scan(&allowed).Error; e != nil {
		return out, e
	}
	codes := map[string]string{}
	for _, b := range allowed {
		codes[b.BatchCode] = b.ProductCode
	}
	path := os.Getenv("PASSPORT_ACCESS_LOG")
	if path == "" {
		return out, nil
	}
	st, e := os.Lstat(path)
	if e != nil || !st.Mode().IsRegular() {
		return out, nil
	}
	f, e := os.Open(path)
	if e != nil {
		return out, nil
	}
	defer f.Close()
	st, e = f.Stat()
	if e != nil {
		return out, e
	}
	offset := int64(0)
	if st.Size() > trafficBytes {
		offset = st.Size() - trafficBytes
		out.Truncated = true
	}
	r := bufio.NewReader(io.NewSectionReader(f, offset, st.Size()-offset))
	if offset > 0 {
		_, _ = r.ReadString('\n')
	}
	scanner := bufio.NewScanner(r)
	scanner.Buffer(make([]byte, 4096), 1024*1024)
	rows := []VisitRow{}
	regions := map[string]int{}
	batchCounts := map[string]int{}
	cache := map[string]string{}
	n := 0
	for scanner.Scan() {
		n++
		row, ip, ok := parseVisit(scanner.Text())
		if !ok {
			continue
		}
		product, ok := codes[row.BatchCode]
		if !ok || q.BatchCode != "" && !strings.Contains(row.BatchCode, q.BatchCode) {
			continue
		}
		t, _ := time.Parse(time.RFC3339, row.VisitedAt)
		if t.Before(since) || t.After(now) {
			continue
		}
		region, ok := cache[ip]
		if !ok {
			region = ipregion.Lookup(ip)
			cache[ip] = region
		}
		row.ID = strconv.Itoa(n)
		row.ProductCode = product
		row.Region = region
		rows = append(rows, row)
		regions[region]++
		batchCounts[row.BatchCode]++
	}
	if e = scanner.Err(); e != nil {
		return out, e
	}
	out.Available = true
	out.Count = len(rows)
	out.Regions = buckets(regions)
	out.Batches = buckets(batchCounts)
	sort.SliceStable(rows, func(i, j int) bool { return rows[i].VisitedAt > rows[j].VisitedAt })
	start := (q.PageIndex - 1) * q.PageSize
	if start < len(rows) {
		end := start + q.PageSize
		if end > len(rows) {
			end = len(rows)
		}
		out.List = rows[start:end]
	}
	return out, nil
}
