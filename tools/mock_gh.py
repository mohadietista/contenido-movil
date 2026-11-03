import http.server, json, base64, hashlib, os, sys, urllib.parse, subprocess
VAULT='/Users/moha/Proyectos/PKM'; APP='/Users/moha/Proyectos/contenido-movil'
files=[p for p in subprocess.run(['git','-C',VAULT,'ls-files','-z'],capture_output=True).stdout.decode().split('\0') if p]
mem={}  # escrituras en memoria (no toca la bóveda)
def content(p):
    if p in mem: return mem[p]
    return open(os.path.join(VAULT,p),'rb').read()
def sha(b): return hashlib.sha1(b).hexdigest()
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(s,*a,**k): super().__init__(*a,directory=APP,**k)
    def cors(s):
        s.send_header('Access-Control-Allow-Origin','*'); s.send_header('Access-Control-Allow-Headers','*'); s.send_header('Access-Control-Allow-Methods','GET,PUT,POST,PATCH,OPTIONS')
    def js(s,o,code=200):
        b=json.dumps(o).encode(); s.send_response(code); s.cors(); s.send_header('Content-Type','application/json'); s.end_headers(); s.wfile.write(b)
    def do_OPTIONS(s): s.send_response(204); s.cors(); s.end_headers()
    def do_GET(s):
        u=urllib.parse.urlparse(s.path); p=urllib.parse.unquote(u.path)
        if not p.startswith('/repos/'): return super().do_GET()
        if '/git/trees/' in p:
            return s.js({'tree':[{'path':f,'type':'blob','sha':sha(content(f)),'mode':'100644'} for f in files]})
        if '/git/blobs/' in p:
            h=p.rsplit('/',1)[1]
            for f in files:
                c=content(f)
                if sha(c)==h: return s.js({'content':base64.b64encode(c).decode()})
            return s.js({'message':'nf'},404)
        if '/contents/' in p:
            f=p.split('/contents/',1)[1]; c=content(f); return s.js({'sha':sha(c),'content':base64.b64encode(c).decode()})
        s.js({'message':'?'},404)
    def do_PUT(s):
        p=urllib.parse.unquote(urllib.parse.urlparse(s.path).path); f=p.split('/contents/',1)[1]
        body=json.loads(s.rfile.read(int(s.headers['Content-Length']))); c=base64.b64decode(body['content']); mem[f]=c
        if f not in files: files.append(f)
        sys.stderr.write('PUT '+f+'\n'); s.js({'content':{'sha':sha(c)}})
    def log_message(s,*a): pass
http.server.ThreadingHTTPServer(('127.0.0.1',8787),H).serve_forever()
