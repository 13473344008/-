from fixture import *
import base64
auth();f=json.loads((rt/'test-artifacts/fixtures.json').read_text());b=f['preview']['id'];p='passport-batches/'+b+'/preview';before=snap()
try:
 for kind in ['working','review']:
  query='?kind='+kind+('&review_id='+f['review_id'] if kind=='review' else '')
  check('Anonymous '+kind+' denied',req(p+query,token=None)['code']==401)
  for role in ['editor','reviewer','viewer']:
   v=ok(p+query,token=role);check(role+' '+kind+' exact isolated weight',v['payload']['packaging']['quantity']==('20' if kind=='working' else '22'));check(role+' '+kind+' watermark kind',v['kind']==kind)
 check('Cross batch review denied',req('passport-batches/'+f['chain']['id']+'/preview?kind=review&review_id='+f['review_id'])['code']==404)
 check('Unknown preview kind rejected',req(p+'?kind=published')['code']==422)
 check('Review ID required',req(p+'?kind=review')['code']==422)
 check('Published batch no draft preview',req('passport-batches/'+f['chain']['id']+'/preview?kind=working')['code']==422)
 check('Public preview remains 25',json.loads((rt/'publish/published/PF-T11-TEST-PREVIEW.json').read_text())['packaging']['quantity']=='25')
 check('Preview is read only',snap()==before)
 check('Preview assets frozen PNG',all(base64.b64decode(v).startswith(b'\x89PNG') for v in ok(p+'?kind=review&review_id='+f['review_id'])['assets'].values()))
finally:(rt/'test-artifacts/preview-api.json').write_text(json.dumps(checks,indent=2))
