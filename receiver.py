"""Local receiver for fetch_x.js: open http://127.0.0.1:8765/receive#<data> and the posts are saved to data/incoming.json.
Usage: python3 receiver.py [output path]"""
import http.server, json, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else 'data/incoming.json'  # same as serenity.config.INCOMING
PAGE = b"""<!doctype html><meta charset=utf-8><body><p id=s>sending...</p><script>
const raw=decodeURIComponent(location.hash.slice(1));
fetch('/data',{method:'POST',body:raw}).then(r=>r.ok?r.text():r.text().then(t=>{throw t})).then(t=>{document.getElementById('s').textContent='saved '+t+' chars'; history.replaceState(null,'',location.pathname);}).catch(e=>document.getElementById('s').textContent='error '+e);
</script>"""
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(PAGE)
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = self.rfile.read(n)
        try:
            data = json.loads(body)
            assert isinstance(data, list) and all(isinstance(x, dict) and x.get('id') for x in data)
        except Exception as e:
            print('rejected bad payload:', repr(e)[:200], file=sys.stderr, flush=True)
            self.send_response(400); self.end_headers(); self.wfile.write(b'bad payload'); return
        open(OUT, 'wb').write(body)
        print('saved', len(data), 'posts to', OUT, flush=True)
        self.send_response(200); self.end_headers(); self.wfile.write(str(len(body)).encode())
    def log_message(self, *a): pass
http.server.HTTPServer(('127.0.0.1', 8765), H).serve_forever()
