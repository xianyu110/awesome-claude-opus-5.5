import json,glob,os,sys,subprocess,threading,time,urllib.request
from concurrent.futures import ThreadPoolExecutor
HOST='https://upload.maynor1024.live'
STATE='mirror.json'; lock=threading.Lock()
S=json.load(open(STATE)) if os.path.exists(STATE) else {}
media={}
for f in glob.glob('raw/media/b*.json'):
    for m in json.load(open(f)).get('includes',{}).get('media',[]): media[m['media_key']]=m
byurl={}
for m in media.values():
    for v in m.get('variants',[]): byurl[v.get('url')]=m
C=json.load(open('cases.json'))
jobs=[]  # (key, src_url, kind)
def pick(m):
    v=sorted([x for x in m.get('variants',[]) if x.get('content_type')=='video/mp4'],key=lambda x:x.get('bit_rate',0))
    if not v: return None,[]
    mid=[x for x in v if 500000<=x.get('bit_rate',0)<=1100000]
    first=(mid or [x for x in v if x.get('bit_rate',0)<=1100000] or v[:1])[-1]
    return first['url'],[x['url'] for x in v]
for c in C:
    for it in c['media']:
        if it['type']=='photo': jobs.append((it['url'],it['url']+'?name=medium','img'))
        else:
            if it.get('poster'): jobs.append((it['poster'],it['poster']+'?name=medium','img'))
            m=byurl.get(it.get('url'))
            if m:
                u,allv=pick(m)
                if u: jobs.append((it['url'],u,'vid:'+'|'.join(allv)))
seen=set();J=[]
for j in jobs:
    if j[0] not in seen: seen.add(j[0]);J.append(j)
only=sys.argv[1] if len(sys.argv)>1 else 'all'
J=[j for j in J if only=='all' or j[2].startswith(only)]
todo=[j for j in J if j[0] not in S]
print('total',len(J),'todo',len(todo),flush=True)
def dl(u,path):
    r=subprocess.run(['curl','-sfL','-m','180','-o',path,u]); return r.returncode==0 and os.path.getsize(path)>0
def up(path,ctype):
    r=subprocess.run(['curl','-s','-m','600','-F',f'file=@{path};type={ctype}',HOST+'/upload'],capture_output=True,text=True)
    return HOST+json.loads(r.stdout)[0]['src']
def work(j):
    key,u,kind=j; tid=threading.get_ident(); path=f'/tmp/mir_{tid}'
    try:
        if kind=='img':
            path+='.jpg'
            if not dl(u,path) and not dl(key,path): raise Exception('dl')
            url=up(path,'image/jpeg')
        else:
            path+='.mp4'; allv=kind[4:].split('|')
            if not dl(u,path): raise Exception('dl')
            if os.path.getsize(path)>15e6 and allv[0]!=u:
                dl(allv[0],path)
            if os.path.getsize(path)>60e6: raise Exception('too big')
            url=up(path,'video/mp4')
        with lock:
            S[key]={'cdn':url,'bytes':os.path.getsize(path)}
            json.dump(S,open(STATE,'w'))
        return 1
    except Exception as e:
        print('FAIL',key,e,flush=True); return 0
    finally:
        try: os.remove(path)
        except: pass
n=0
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(work,todo):
        n+=1
        if n%50==0: print('done',n,len(S),time.strftime('%H:%M:%S'),flush=True)
print('finished',len(S),flush=True)
