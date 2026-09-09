import http.server, json, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else 'data/incoming.json'
PAGE = b"""<!doctype html><meta charset=utf-8><body><p id=s>sending...</p><script>
const raw=decodeURIComponent(location.hash.slice(1));
fetch('/data',{method:'POST',body:raw}).then(r=>r.text()).then(t=>{document.getElementById('s').textContent='saved '+t+' chars'; history.replaceState(null,'',location.pathname);}).catch(e=>document.getElementById('s').textContent='error '+e);
</script>"""
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(PAGE)
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(n)
        json.loads(body); open(OUT, 'wb').write(body)
        self.send_response(200); self.end_headers(); self.wfile.write(str(len(body)).encode())
    def log_message(self, *a): pass
http.server.HTTPServer(('127.0.0.1', 8765), H).serve_forever()
