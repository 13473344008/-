from verify_history import *
h.admin=login(cred['admin_username'],cred['admin_password']);f=json.loads((rt/'test-artifacts/history-fixtures.json').read_text());b=f['browser']['batch_id']
with db() as c:c.execute("CREATE TRIGGER t10_fault_finalize BEFORE UPDATE OF published_at ON passport_revisions WHEN NEW.batch_id='"+b+"' AND NEW.published_at IS NOT NULL BEGIN SELECT RAISE(ABORT,'injected real finalize failure'); END")
try:r=roll(b,f['browser']['versions'][0]['revision']['id']);check('Actual DB finalization fault recovery required',r['data']['record']['publish_status']=='recovery_required');check('Actual file switched DB pending',ok('passport-batches/'+b+'/publication/health')['classification']=='file_switched_db_pending')
finally:
 with db() as c:c.execute('DROP TRIGGER t10_fault_finalize')
(rt/'test-artifacts/injected-pending.json').write_text(json.dumps(checks,indent=2))
