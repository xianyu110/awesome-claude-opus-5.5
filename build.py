import json,glob,csv,re,datetime,collections
from urllib.parse import urlparse
posts=json.load(open('all_sorted.json'))
ents={}
for f in glob.glob('raw/*.json'):
    try: d=json.load(open(f))
    except Exception: continue
    for p in d.get('data',[]) if isinstance(d,dict) else d:
        u=[x.get('expanded_url','') for x in (p.get('entities') or {}).get('urls',[])]
        if u: ents[p['id']]=u
DROP={362,843,1270,1279,392,830,1049,1114,458,554,446,1044,791,1158,1321,1043,663,678,866,595,835,1567,1378,1478,1524,551,1025,1069,1299,1302,1314,1369,1326}
CAT={'G':'Game','3':'3D&WebGPU','W':'Web&UI','A':'App&Tool','F':'Agent&Workflow','C':'Coding','R':'Writing&Analysis','V':'Comparison','O':'Other'}
CATZH={'Game':'🎮 游戏 Game','3D&WebGPU':'🧊 3D & WebGPU','Web&UI':'🌐 网页与 UI Web&UI','App&Tool':'🛠️ 应用与工具 App&Tool','Agent&Workflow':'🤖 Agent 与工作流','Coding':'💻 编程 Coding','Writing&Analysis':'📝 写作与分析','Comparison':'⚔️ 模型对比 Comparison','Other':'🎬 其他（动效视频/动画/音乐）'}
BADDOM=('x.com','twitter.com','pic.x.com','t.co')
NONPLAY=('youtube.com','youtu.be','github.com','note.com','zenn.dev','qiita.com','medium.com','substack.com','bilibili.com','instagram.com','tiktok.com','linkedin.com','mp.weixin.qq.com')
PLAYKW=re.compile(r'play|demo|live|try it|遊べ|試せ|体验|试玩|在线|プレイ|デモ',re.I)
dec=[l.rstrip('\n').split('|') for f in sorted(glob.glob('dec*.txt')) for l in open(f) if l.strip()]
cases=[]
for idx,c,t,desc,pr in dec:
    i=int(idx)
    if i in DROP: continue
    p=posts[i]
    links=[u for u in ents.get(p['id'],[]) if u and urlparse(u).netloc.lower().removeprefix('www.') not in BADDOM]
    demo=links[0] if links else ''
    dom=urlparse(demo).netloc.lower().removeprefix('www.') if demo else ''
    playable=bool(demo) and not any(dom.endswith(n) for n in NONPLAY) and (c in 'G3WAV' or PLAYKW.search(p['text']) is not None)
    dt=datetime.datetime.strptime(p['date'][:19],'%Y-%m-%dT%H:%M:%S')+datetime.timedelta(hours=8)
    cases.append(dict(category=CAT[c],title_zh=t,desc_zh=desc,author='@'+p['user'],url=p['url'],
        date=dt.strftime('%Y-%m-%d %H:%M'),demo_url=demo,playable_demo='yes' if playable else 'no',
        prompt_included='yes' if pr=='1' else 'no',likes=p['likes'],impressions=p['imp'],_i=i))
import os
CR={v:k for k,v in CAT.items()}
MED=json.load(open('media.json')) if os.path.exists('media.json') else {}
MIR={k:v['cdn'] for k,v in json.load(open('mirror.json')).items()} if os.path.exists('mirror.json') else {}
for x in cases:
    m=MED.get(x['url'].rsplit('/',1)[1],{})
    x['thumb']=m.get('thumb','');x['media']=m.get('media',[]);x['full_text']=m.get('full_text','')
    for it in x['media']:
        if MIR.get(it.get('url')): it['cdn']=MIR[it['url']]
        if it.get('poster') and MIR.get(it['poster']): it['poster_cdn']=MIR[it['poster']]
    x['thumb_cdn']=MIR.get(x['thumb'],'')
    x['video_cdn']=next((it.get('cdn','') for it in x['media'] if it['type']!='photo' and it.get('cdn')),'')
    x['links']=m.get('links',[])
    if not x['demo_url'] and x['links']:
        x['demo_url']=x['links'][0]; dom=urlparse(x['demo_url']).netloc.lower().removeprefix('www.')
        x['playable_demo']='yes' if (not any(dom.endswith(n) for n in NONPLAY) and (CR[x['category']] in 'G3WAV' or PLAYKW.search(x['full_text']) is not None)) else 'no'
    x['likes']=max(x['likes'],m.get('likes',0));x['impressions']=max(x['impressions'],m.get('impressions',0))
order=list(CAT.values())
cases.sort(key=lambda x:(order.index(x['category']),-x['likes']))
for n,x in enumerate(cases,1): x['id']=n
fields=['id','category','title_zh','desc_zh','author','url','date','demo_url','playable_demo','prompt_included','likes','impressions']
json.dump([{k:x[k] for k in fields+['thumb','thumb_cdn','video_cdn','media','full_text','links']} for x in cases],open('cases.json','w'),ensure_ascii=False,indent=1)
with open('cases.csv','w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); w.writeheader(); w.writerows(cases)
cnt=collections.Counter(x['category'] for x in cases)
npl=sum(x['playable_demo']=='yes' for x in cases); npr=sum(x['prompt_included']=='yes' for x in cases); nd=sum(bool(x['demo_url']) for x in cases)
dates=sorted(x['date'] for x in cases)
top=sorted(cases,key=lambda x:-(x['likes']*(1.5 if x['playable_demo']=='yes' else 1)))[:20]
esc=lambda s:str(s).replace('|','\\|').replace('\n',' ')
def dl(x):
    if not x['demo_url']: return '—'
    return f"[{'▶️ 试玩' if x['playable_demo']=='yes' else '🔗 链接'}]({x['demo_url']})"
L=[]
L+=['# Awesome Claude Opus 5.5 案例合集','',
'> 收录 Anthropic **Claude Opus 5.5**（2026-09-22 正式发布，09-20 前后已有灰度/泄露测试）发布以来，全网（以 X/Twitter 为主）创作者**亲手用 Opus 5.5 做出来**的真实案例：游戏、3D/WebGPU 场景、网页、应用、Agent 工作流、代码重构、动效视频，以及附带实际产出的模型横评。',
'>','> 收录标准：必须有作者本人的实际产出（Demo/视频/截图/代码）；剔除纯吹捧、跑分价格表、中转/代理广告、新闻转述、纯提问与搬运；同一作者同一项目只保留互动最高的一条。',
'',f'更新时间：2026-09-28（北京时间） ｜ 数据区间：{dates[0][:10]} ~ {dates[-1][:10]}','',
'## 📊 统计','',f'- 案例总数：**{len(cases)}**',f'- 附带链接（Demo/源码/站点）：**{nd}**，其中可在线体验/试玩：**{npl}**',f'- 附提示词：**{npr}**','',
'| 分类 | 数量 |','|---|---|']
for k in order: L.append(f'| {CATZH[k]} | {cnt[k]} |')
L+=['','## 🏆 Top 20（高互动 / 可试玩优先）','','| # | 预览 | 案例 | 分类 | 说明 | 作者 | ❤️ | 链接 | Demo |','|---|---|---|---|---|---|---|---|---|']
for n,x in enumerate(top,1):
    th=f'<a href="https://xianyu110.github.io/awesome-claude-opus-5.5/#case-{x["id"]}"><img src="{x["thumb_cdn"] or x["thumb"]}" width="120" alt="{esc(x["title_zh"])}"></a>' if x['thumb'] else '—'
    L.append(f"| {n} | {th} | {esc(x['title_zh'])} | {x['category']} | {esc(x['desc_zh'])} | {x['author']} | {x['likes']:,} | [原帖]({x['url']}) | {dl(x)} |")
L+=['','## 📂 目录','']
for k in order: L.append(f"- [{CATZH[k]}（{cnt[k]}）](#{re.sub(r'[^0-9a-z一-龥_ -]','',CATZH[k].lower()).strip().replace(' ','-')})")
for k in order:
    L+=['',f'## {CATZH[k]}','','| 序号 | 案例 | 说明 | 作者 | 链接 | Demo |','|---|---|---|---|---|---|']
    for x in [c for c in cases if c['category']==k]:
        t=esc(x['title_zh'])+(' 📝' if x['prompt_included']=='yes' else '')
        L.append(f"| {x['id']} | {t} | {esc(x['desc_zh'])} | {x['author']} | [原帖]({x['url']}) | {dl(x)} |")
L+=['','## Claude 国内使用','','| 服务 | 说明 | 链接 |','|---|---|---|','| MomoAI 包月 | Claude 包月订阅 | https://momoai.asia/home |','| API 聚合 | Claude / GPT / Gemini 等模型 API 聚合 | https://tryallapi.com/ |','',
'友链：[Awesome GPT-6 Astra](https://github.com/xianyu110/awesome-gpt-6-astra) ｜ [Awesome GPT Image 2.5](https://github.com/xianyu110/awesome-gpt-image2.5)','',
'🌐 在线浏览（支持搜索/分类筛选）：https://xianyu110.github.io/awesome-claude-opus-5.5/']
L+=['','---','','图例：📝 = 原帖附提示词；▶️ 试玩 = 可在线体验；🔗 = 相关链接（源码/视频/文章）。互动数据截至 2026-09-28 抓取时。','','欢迎 PR 补充 🙌']
open('README.md','w').write('\n'.join(L)+'\n')
print(len(cases),dict(cnt),'demo',nd,'playable',npl,'prompt',npr)
for x in top[:20]: print(x['author'],x['likes'],x['title_zh'],x['url'],x['demo_url'])
