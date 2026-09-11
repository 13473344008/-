T10 complete locally, awaiting human acceptance. User human-accepted T0–T9; only T10 authorized.

Authoritative results: docs/T10_VERSION_AUDIT_ROLLBACK.md and docs/T10_TEST_RESULTS.json.
65/65 Gates PASS, 1297 named assertions/leaf tests PASS, 0 FAIL; includes 301 existing UI unit tests. Upstream generic check:api retains four existing T8 diagnostics, explicitly outside business Gate counts. 30 existing lint warnings, zero errors.

Added history/detail/integrity/compare/audit API and HistoryPanel; rollback shares T9 sealing, verify, atomic switch, finalize/fail pipeline. New version always, target historical review provenance retained, new actor/reason/audit. New migration 1789257600000_version_history (1 reason column, 4-column publication_health, 5 audit enums, partial normal-review success index, permission seed). Prior migrations unchanged.

Main 43 successful /48 attempts (5 failed), Fresh 13 successful /13 attempts. Total56 successful,57sealed JSON,73sealed asset relations. 522 full DB/file/baseline assertions PASS. 36748 historical files +53baseline+7site unchanged.

Main75 and fresh73 API assertions, actual browser21 + recovery6 + finalread UI4, real DBfailure2, migration10, persistence2, schema57, contracts8, static140, stopped4, extraAPI18, publishing42 leaf, fault6leaf, lock/live-service-role6leaf, UI301. All passing final artifact files.

Actual failure cases deliberately created only in runtime/t10. Corruption tests restored exact test bytes; original T4–T9 runtime/reports never edited. Process-restart test preserved pending rollback, browser finalized original operation asV5. No changes to public site/server/Caddy/Directus/Docker/DNS/HTTPS/QR. T11/T12 not started.

ALL T10 processes stopped. Ports18105,18106,19536,19538 returned ECONNREFUSED after stopping final static PID66241. No remaining work besides final user response; do not restart services or proceed T11.
