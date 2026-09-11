package publishing

import (
	"strings"
	"testing"
)

func TestT11TestCodeMatchesPublishedSchema(t *testing.T) {
	for _, code := range []string{"PF-T11-TEST-001", "TEST-B", "PF_TEST_001"} {
		if _, e := Build([]byte(strings.Replace(string(candidate()), "TEST-B", code, 1)), 1, "2026-09-10T00:00:00.000Z"); e != nil {
			t.Fatalf("%s: %v", code, e)
		}
	}
	for _, code := range []string{"PF-TESTING-001", "NOTATEST", "PF-001"} {
		if _, e := Build([]byte(strings.Replace(string(candidate()), "TEST-B", code, 1)), 1, "2026-09-10T00:00:00.000Z"); e == nil {
			t.Fatalf("accepted %s", code)
		}
	}
}
