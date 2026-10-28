"""Local-only JSON REST API and static UI, using Python standard library."""
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from src.core import Store, Problem


def make_server(store, port=8000):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def respond(self,status,data):
            body=json.dumps(data,ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers(); self.wfile.write(body)
        def dispatch(self):
            path=urlsplit(self.path).path
            query=parse_qs(urlsplit(self.path).query)
            host=self.headers.get('Host','')
            allowed={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            if host not in allowed: raise Problem(403,'Localhost only')
            origin=self.headers.get('Origin')
            if origin and origin not in {f'http://{h}' for h in allowed}: raise Problem(403,'Origin not allowed')
            if self.command=='GET':
                if path=='/api/health': return self.respond(200,{'status':'ok','temporary_session':getattr(store,'session_only',False)})
                if path.startswith('/api/risks'):
                    if query.get('unavailable',['0'])[0]=='1': raise Problem(503,'จำลองบริการสต็อกไม่พร้อม กรุณาลองใหม่')
                    mode=query.get('mode',['demo'])[0]
                    if path=='/api/risks': return self.respond(200,store.risks(mode))
                    return self.respond(200,store.risk(path.rsplit('/',1)[1],query.get('location',['BKK-DC'])[0],mode))
                if path=='/api/project':
                    return self.respond(200,json.loads((store.root/'docs/source_comparison.json').read_text(encoding='utf-8')))
                if path.startswith('/api/policy-history/'):
                    return self.respond(200,store.policy_history(path.rsplit('/',1)[1],query.get('location',['BKK-DC'])[0],query.get('mode',['demo'])[0]))
                if path=='/api/quality': return self.respond(200,store.quality())
                if path=='/api/requests': return self.respond(200,store.all_requests())
                if path.startswith('/api/requests/'):
                    parts=path.strip('/').split('/')
                    if len(parts)==4 and parts[3]=='history': return self.respond(200,store.history(int(parts[2])))
                    if len(parts)==3: return self.respond(200,store.get_request(int(parts[2])))
                names={'/':'index.html','/style.css':'style.css','/app.js':'app.js','/features.js':'features.js'}
                if path in names:
                    f=store.root/'web'/names[path]; body=f.read_bytes()
                    self.send_response(200)
                    self.send_header('Content-Type',(mimetypes.guess_type(str(f))[0] or 'text/plain')+'; charset=utf-8')
                    self.send_header('Content-Length',str(len(body)))
                    self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
                    self.end_headers(); self.wfile.write(body); return
                raise Problem(404,'ไม่พบเส้นทาง')
            if self.command not in ('POST','PUT'): raise Problem(405,'Method not allowed')
            if self.headers.get_content_type()!='application/json': raise Problem(415,'ต้องใช้ application/json')
            size=int(self.headers.get('Content-Length','0'))
            if not 0<size<=16384: raise Problem(413,'Request size invalid')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict): raise Problem(422,'ต้องเป็น JSON object')
            if self.command=='POST' and path=='/api/policy-reviews': return self.respond(200,store.review_policy(data))
            if self.command=='POST' and path=='/api/what-if': return self.respond(200,store.what_if(data))
            if self.command=='POST' and path=='/api/requests': return self.respond(201,store.create(data))
            if self.command=='PUT' and path.startswith('/api/requests/'):
                return self.respond(200,store.update(int(path.rsplit('/',1)[1]),data))
            raise Problem(404,'ไม่พบเส้นทาง')
        def handle_request(self):
            try: self.dispatch()
            except Problem as e: self.respond(e.status,{'error':e.message})
            except (ValueError,TypeError): self.respond(400,{'error':'รูปแบบข้อมูลไม่ถูกต้อง'})
            except (OSError, __import__('sqlite3').Error): self.respond(503,{'error':'บริการข้อมูลไม่พร้อมใช้งาน กรุณาตรวจสอบไฟล์/ฐานข้อมูล'})
        do_GET=do_POST=do_PUT=do_DELETE=handle_request
    return ThreadingHTTPServer(('127.0.0.1',port),Handler)
