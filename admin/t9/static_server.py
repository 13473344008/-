from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import re,os
ROOT=Path(__file__).resolve().parents[2]/'runtime/t9/publish'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT),**kw)
 def do_GET(self):
  if not re.fullmatch(r'/(?:published/[A-Za-z0-9_-]{1,64}\.json|versions/[A-Za-z0-9_-]{1,64}/v[1-9][0-9]*\.json|assets/sha256/[0-9a-f]{2}/[0-9a-f]{64}\.png)',self.path):self.send_error(404);return
  p=ROOT/self.path.lstrip('/')
  if any(x.is_symlink() for x in [p,*p.parents]):self.send_error(404);return
  super().do_GET()
 def list_directory(self,path):self.send_error(404);return None
 def end_headers(self):self.send_header('X-Content-Type-Options','nosniff');super().end_headers()
print('T9 static files only, localhost:19536',flush=True)
ThreadingHTTPServer(('127.0.0.1',19536),Handler).serve_forever()
