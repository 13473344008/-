from flow import *
auth();f=json.loads(statefile.read_text());out={'faults':{}}
try:
 for stage in ['build','write','copy1','copy2','validation','manifest','rename','finalize']:
  b=batch(f['product_id'],'PF-T12-TEST-FAULT-'+stage.upper());submit(b);check(stage+' real image candidate approved',decision(b)['code']==200)
  out['faults'][stage]={'batch_id':b,'request':pubreq(b)}
 (rt/'test-artifacts/faults.json').write_text(json.dumps(out,indent=2))
finally:(rt/'test-artifacts/fault-prepare.json').write_text(json.dumps(checks,indent=2))
